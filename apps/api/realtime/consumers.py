import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from collab.models import ChannelMember

class ChannelConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel_group_name = f'channel_{self.channel_id}'
        self.user = self.scope['user']

        if self.user.is_anonymous:
            await self.close()
            return

        is_member = await self.is_channel_member(self.user, self.channel_id)
        if not is_member:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.channel_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.channel_group_name,
            self.channel_name
        )

    # Receive message from WebSocket (not used for user messages, but useful for other events)
    async def receive_json(self, content):
        # For now, we don't expect clients to send messages directly over the socket.
        # They will use the HTTP API. This is here for potential future use.
        pass

    # Receive message from room group
    async def message_new(self, event):
        # Send message to WebSocket
        await self.send_json(content=event['message'])

    async def doc_new(self, event):
        await self.send_json(content=event['document'])

    @database_sync_to_async
    def is_channel_member(self, user, channel_id):
        """
        Checks if a user is a member of the channel.
        """
        return ChannelMember.objects.filter(user=user, channel_id=channel_id).exists()
