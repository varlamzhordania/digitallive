import json

from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async

from main.models import Display

from .serializers import DisplaySerializer


class DisplayConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.key = self.scope['query_string'].decode('utf-8').split('=')[1]

        try:
            self.display = await self.get_display(self.key)
        except Display.DoesNotExist:
            await self.close(code=400)
            return

        await self.channel_layer.group_add(f"display_{self.display.stream_key}", self.channel_name)
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        if action == "get_display_data":
            await self.send_display_data()
        else:
            await self.send(text_data=json.dumps({"error": "Unknown action"}))

    async def disconnect(self):
        await self.channel_layer.group_discard(f"display_{self.display.code}", self.channel_name)
        await self.close()

    async def send_display_data(self):
        self.display = await self.get_display(self.key)

        serializer_data = await sync_to_async(self.get_display_serializer_data)(self.display)

        data = {
            "action": "get_display_data",
            "message": serializer_data
        }

        await self.send(text_data=json.dumps(data))

    def get_display_serializer_data(self, display):
        from .serializers import DisplaySerializer
        serializer = DisplaySerializer(display)
        return serializer.data

    async def display_update(self, event):
        data = event["data"]

        prep_data = {
            "action": "display_update",
            "message": data
        }

        await self.send(text_data=json.dumps(prep_data))

    @sync_to_async
    def get_display(self, key):
        queryset = Display.objects.get(stream_key=key)
        return queryset
