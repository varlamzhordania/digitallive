from django.urls import path
from .consumers import DisplayConsumer

app_name = "websocket"

urlpatterns = [
    path("ws/display/", DisplayConsumer.as_asgi(), name="display_socket"),
]
