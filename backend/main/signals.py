from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Display, Ticker, TickerItem
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


@receiver(post_save, sender=Ticker)
def ticker_updated(sender, instance, **kwargs):
    display = instance.display
    display_serializer = DisplaySerializer(display)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"display_{display.stream_key}",
        {
            "type": "display.update",
            "data": display_serializer.data
        }
    )


@receiver(post_save, sender=TickerItem)
def ticker_item_updated(sender, instance, **kwargs):
    display = instance.ticker.display

    display_serializer = DisplaySerializer(display)

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"display_{display.stream_key}",
        {
            "type": "display.update",
            "data": display_serializer.data
        }
    )
