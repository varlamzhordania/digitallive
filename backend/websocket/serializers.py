from django.conf import settings
from rest_framework import serializers

from main.models import Display, Ticker, TickerItem


class TickerItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = TickerItem
        fields = '__all__'


class TickerSerializer(serializers.ModelSerializer):
    items = TickerItemSerializer(many=True, read_only=True)

    class Meta:
        model = Ticker
        fields = ['id', 'interval', 'start_time', 'end_time', 'items']


class DisplaySerializer(serializers.ModelSerializer):
    current_video = serializers.SerializerMethodField(read_only=True)
    tickers = TickerSerializer(many=True, read_only=True)

    class Meta:
        model = Display
        fields = [
            "is_active", "updated_at", "name", "slug", "current_video", "video_duration",
            "loop", "paused", "tickers"]

    def get_current_video(self, obj):
        return f"{settings.SERVER_DOMAIN}{obj.current_video.url}"
