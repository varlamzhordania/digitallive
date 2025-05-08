import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django_ckeditor_5.fields import CKEditor5Field
from rest_framework.authtoken.models import Token
from autoslug.fields import AutoSlugField

from core.models import BaseModel, UploadPath
from main.tasks import start_streaming, update_video_duration


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
        ],
        blank=True,
        null=True,
        help_text=_('The current video played.'),
    )
    video_duration = models.FloatField(
        verbose_name=_('Video Duration (seconds)'),
        default=0,
        blank=True,
        null=True,
        help_text=_(
            'Duration of the video in seconds (for easier tracking).'
        )
    )
    loop = models.IntegerField(
        verbose_name=_('Number of times to play'),
        default=0,
        help_text=_('-1 means unlimited and 0 mean only the first time'),
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
        is_video_uploaded = self.pk is None and self.current_video
        is_video_changed = self.pk and self.current_video != Display.objects.get(
            pk=self.pk
        ).current_video  # Video update

        super().save(*args, **kwargs)

        if is_video_uploaded or is_video_changed:
            self.set_video_duration()

    def set_video_duration(self, video_duration=None):
        if video_duration is None:
            update_video_duration.apply_async(args=[self.id])
        else:
            self.video_duration = video_duration
            self.save(update_fields=['video_duration'])

    def start_streaming(self):
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


class DisplayLog(BaseModel):
    class TypeChoices(models.TextChoices):
        ERROR = 'ERROR', _('Error')
        WARNING = 'WARNING', _('Warning')
        INFO = 'INFO', _('Info')
        DEBUG = 'DEBUG', _('Debug')
        UNKNOWN = 'UNKNOWN', _('Unknown')

    display = models.ForeignKey(
        Display,
        verbose_name=_('Display'),
        on_delete=models.CASCADE,
        related_name='logs',
        blank=True,
        null=True,
    )
    type = models.CharField(
        verbose_name=_('Log Type'),
        max_length=10,
        choices=TypeChoices.choices,
        default=TypeChoices.UNKNOWN,
        help_text=_('Type of the log')
    )
    message = models.TextField(
        verbose_name=_('Message'),
        help_text=_('The log message')
    )
    is_active = None

    class Meta:
        verbose_name = _('Display Log')
        verbose_name_plural = _('Display Logs')
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.display.name} - {self.type} - {self.created_at}'


class DisplayToken(Token):
    display = models.ForeignKey(Display, on_delete=models.CASCADE, related_name='tokens')
    user = None

    class Meta:
        verbose_name = _('Display Token')
        verbose_name_plural = _('Display Tokens')
        ordering = ['-created']

    def __str__(self):
        return f"Token for {self.display.name}"



class Ticker(BaseModel):
    display = models.ForeignKey(
        Display,
        on_delete=models.CASCADE,
        related_name='tickers',
        verbose_name=_('Display'),
    )
    start_time = models.DateTimeField(
        verbose_name=_('Start Time'),
        null=True,
        blank=True,
        help_text=_('When to start showing this ticker (optional).')
    )
    end_time = models.DateTimeField(
        verbose_name=_('End Time'),
        null=True,
        blank=True,
        help_text=_('When to stop showing this ticker (optional).')
    )

    class Meta:
        verbose_name = _('Ticker')
        verbose_name_plural = _('Tickers')
        ordering = ('-created_at',)

    def __str__(self):
        return f"Ticker ID: {self.id}"


class TickerItem(BaseModel):
    ticker = models.ForeignKey(
        Ticker,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name=_('Ticker')
    )
    content = CKEditor5Field(
        verbose_name=_('Content'),
        help_text=_('Individual text message for the ticker.'),
        config_name="comment",
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order'),
        help_text=_('Order in which this text will appear in the ticker feed.')
    )

    class Meta:
        verbose_name = _('Ticker Item')
        verbose_name_plural = _('Ticker Items')
        ordering = ('order',)

    def __str__(self):
        return self.content
