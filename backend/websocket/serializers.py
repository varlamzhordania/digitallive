from django.conf import settings
from rest_framework import serializers

from main.models import Display

class DisplaySerializer(serializers.ModelSerializer):
    current_video = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Display
        fields = [
            "is_active", "updated_at", "name", "slug", "current_video", "video_duration",
            "loop", "paused"]


    def get_current_video(self, obj):
        return f"{settings.SERVER_DOMAIN}{obj.current_video.url}"
