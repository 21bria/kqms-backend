from channels.generic.websocket import AsyncJsonWebsocketConsumer

class UploadMineConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        await self.channel_layer.group_add("upload_notifications", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("upload_notifications", self.channel_name)

    async def upload_done(self, event):
        await self.send_json({
            "message"       : event["message"],
            "total_ritase"  : event["total_ritase"],
            "total_tonase"  : event["total_tonase"],
        })
