import time
import subprocess

from celery import shared_task
from moviepy import VideoFileClip


@shared_task
def update_video_duration(display_id):
    try:
        from .models import Display
        display = Display.objects.get(id=display_id)

        if display.current_video:
            video_path = display.current_video.path

            video = VideoFileClip(video_path)
            duration = video.duration

            display.video_duration = duration
            display.save(update_fields=['video_duration'])

            return f"Video duration updated to {duration} seconds."
        else:
            return "No video file assigned to the display."
    except Display.DoesNotExist:
        return f"Display with ID {display_id} does not exist."
    except Exception as e:
        return f"An error occurred: {str(e)}"


@shared_task
def start_streaming(video_path, stream_key, loop_flag=None, inactivity_timeout=300):
    from main.models import Display
    loop_flag = ["-stream_loop", "-1"] if loop_flag else []

    # Flags for threading and preset
    threads_flag = ["-threads", "2"]
    preset_flag = ["-preset", "veryfast"]

    # Optional CRF value and buffer size for optimization
    crf_flag = ["-crf", "23"]
    buffer_flag = ["-bufsize", "2000k"]

    ffmpeg_command = [
        'ffmpeg', *loop_flag, '-re',
        '-i', video_path,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        *threads_flag, *preset_flag, *crf_flag, *buffer_flag,
        '-f', 'flv',
        f'rtmp://nginx_rtmp:1935/stream/{stream_key}'
    ]

    try:
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        display = Display.objects.get(stream_key=stream_key)
        display.task_id = start_streaming.request.id
        display.save(update_fields=['task_id'])

        while True:
            display = Display.objects.get(stream_key=stream_key)

            if display.paused:
                process.terminate()
                display.task_id = ""
                display.paused = False
                display.save(update_fields=['paused', 'task_id'])
                print(f"Stream {stream_key} paused and stopped.")
                break
            time.sleep(3)
        process.wait()
    except subprocess.CalledProcessError as e:
        print(f"FFmpeg Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
