import uuid
import subprocess

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from autoslug.fields import AutoSlugField

from core.models import BaseModel, UploadPath
from main.tasks import start_streaming


class Place(BaseModel):
    owner = models.ForeignKey(
        get_user_model(),
        verbose_name='Owner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_places',
    )
    name = models.CharField(
        verbose_name=_('Name'),
        max_length=255,
        blank=False,
        null=False,
    )
    slug = AutoSlugField(
        verbose_name=_('Slug'),
        populate_from='name',
        unique=True,
    )
    address = models.TextField(
        verbose_name=_('Address'),
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = _('Place')
        verbose_name_plural = _('Places')
        ordering = ('name',)

    def __str__(self):
        return self.name


class Display(BaseModel):
    place = models.ForeignKey(
        Place,
        verbose_name='Place',
        on_delete=models.CASCADE,
        related_name='displays',
    )
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        blank=False,
        null=False,
        help_text=_('The name of the display.'),
    )
    slug = AutoSlugField(
        verbose_name=_('Slug'),
        populate_from='name',
        unique=True
    )
    stream_key = models.UUIDField(
        verbose_name=_('Stream Key'),
        default=uuid.uuid4,
        editable=False,
        unique=True
    )
    current_video = models.FileField(
        verbose_name=_("Video"),
        upload_to=UploadPath(
            folder="streams",
            sub_path="videos"
        ),
        validators=[
            FileExtensionValidator(
                allowed_extensions=['mp4', ]
            )
            # add more
        ],
        blank=True,
        null=True,
        help_text=_('The current video played.'),
    )
    video_duration = models.FloatField(
        verbose_name=_('Video Duration (seconds)'),
        blank=True,
        null=True,
        help_text=_(
            'Duration of the video in seconds (for easier tracking).'
        )
    )
    loop = models.BooleanField(
        verbose_name=_('Loop'),
        default=True,
        help_text=_('If true, loop the current video.'),
    )
    paused = models.BooleanField(
        verbose_name=_('Paused'),
        default=False,
        help_text=_('If true, pause the current video.'),
    )
    task_id = models.CharField(verbose_name=_("Task ID"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _('Display')
        verbose_name_plural = _('Displays')
        ordering = ('name',)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def set_video_duration(self, save=False):
        if self.current_video and not self.video_duration:
            try:
                video_path = self.current_video.path
                ffmpeg_command = [
                    'ffmpeg', '-i', video_path, '-f',
                    'ffmetadata', '-'
                ]
                result = subprocess.run(
                    ffmpeg_command,
                    capture_output=True,
                    text=True,
                    check=True
                )

                for line in result.stderr.splitlines():
                    if "Duration" in line:
                        # Example output: Duration: 00:01:23.45, start: 0.000000, bitrate: 315 kb/s
                        duration_str = \
                            line.split(',')[0].split(':')[
                                1].strip()
                        minutes, seconds = duration_str.split(
                            ':'
                        )
                        total_seconds = int(
                            minutes
                        ) * 60 + float(seconds)
                        self.video_duration = total_seconds
                        if save:
                            self.save(
                                update_fields=[
                                    'video_duration']
                            )
                        break
            except subprocess.CalledProcessError as e:
                raise ValidationError(
                    f"Error extracting video duration: {e}"
                )

    def start_streaming(self):
        """
        Starts streaming the current video to the corresponding stream key.
        This function can use FFmpeg and handle the `paused` and `loop` settings.
        """
        if self.paused:
            self.paused = False
            self.save(update_fields=['paused'])

        if self.current_video:
            video_path = self.current_video.path
            start_streaming.apply_async(args=[video_path, self.stream_key, self.loop])
        else:
            raise ValueError("No video file assigned to the display.")

    def pause_streaming(self):
        self.paused = True
        self.save(update_fields=['paused'])
        return True
