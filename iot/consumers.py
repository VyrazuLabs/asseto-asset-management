import json

from channels.generic.websocket import AsyncWebsocketConsumer


class SensorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "sensor_data"
        await self.channel_layer.group_add(self.group_name, self.channel_name)

        await self.accept()

        print("[ws] Client connected")

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print("Websocket disconnet")

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)

        print("Recieved", data)

    async def sensor_message(self, event):
        await self.send(
            text_data=json.dumps({"type": "sensor_message", "data": event["data"]})
        )
