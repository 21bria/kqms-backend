from channels.generic.websocket import AsyncWebsocketConsumer
import json

class DuplicateNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("duplicates", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("duplicates", self.channel_name)

    async def send_duplicate(self, event):
        await self.send(text_data=json.dumps({
            "message"   : event.get("message"),
            "count"     : event.get("count"),
            "duplicates": event.get("duplicates"),
            "type"      : "double_batch"
        }))
