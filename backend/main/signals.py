from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Display
from websocket.serializers import DisplaySerializer

@receiver(post_save, sender=Display)
def display_updated(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    serializer = DisplaySerializer(instance)
    async_to_sync(channel_layer.group_send)(
        f"display_{instance.stream_key}",
        {
            "type": "display.update",
            "data": serializer.data,
        }
    )
