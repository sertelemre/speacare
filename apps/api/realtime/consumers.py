import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from collab.models import ChannelMember

class ChannelConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.channel_id = self.scope['url_route']['kwargs']['channel_id']
        self.channel_group_name = f'channel_{self.channel_id}'
        self.user = self.scope['user']

        # Geçici olarak authentication kontrolünü devre dışı bırak
        # if self.user.is_anonymous:
        #     await self.close()
        #     return

        # is_member = await self.is_channel_member(self.user, self.channel_id)
        # if not is_member:
        #     await self.close()
        #     return

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
        print(f"WebSocket consumer: Sending message to client: {event['message']}")
        try:
            await self.send_json(content={
                'type': 'message.new',
                'message': event['message']
            })
            print(f"WebSocket consumer: Message sent successfully")
        except Exception as e:
            print(f"WebSocket consumer: Error sending message: {e}")

    async def doc_new(self, event):
        await self.send_json(content=event['document'])

    async def bots_stopped(self, event):
        # Send bot stopped notification to WebSocket
        await self.send_json(content={
            'type': 'bots_stopped',
            'message': event['message']
        })

    async def bots_started(self, event):
        # Send bot started notification to WebSocket
        await self.send_json(content={
            'type': 'bots_started',
            'message': event['message']
        })

    async def messages_cleared(self, event):
        # Send messages cleared notification to WebSocket
        await self.send_json(content={
            'type': 'messages_cleared',
            'message': event['message']
        })

    async def bot_thinking(self, event):
        # Send bot thinking notification to WebSocket
        await self.send_json(content={
            'type': 'bot_thinking',
            'bot_name': event['bot_name'],
            'bot_id': event['bot_id']
        })

    async def bot_finished_thinking(self, event):
        # Send bot finished thinking notification to WebSocket
        await self.send_json(content={
            'type': 'bot_finished_thinking',
            'bot_name': event['bot_name'],
            'bot_id': event['bot_id']
        })

    @database_sync_to_async
    def is_channel_member(self, user, channel_id):
        """
        Checks if a user is a member of the channel.
        """
        return ChannelMember.objects.filter(user=user, channel_id=channel_id).exists()
