from django.urls import path

from .consumers import SensorConsumer

websocket_urlpatterns=[
    path("ws/iot/device/random-data", SensorConsumer.as_asgi())
]