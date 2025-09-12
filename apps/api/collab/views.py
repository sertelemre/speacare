from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Channel, ChannelBot, Thread, Message, ThreadMessage
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .permissions import IsChannelMember
from .serializers import (
    ChannelSerializer, ChannelBotSerializer, BotInviteSerializer,
    ThreadSerializer, MessageSerializer, VoteSerializer, DocumentSerializer
)
from .tasks import debate_round

class ChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows channels to be viewed, created, and managed.
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Users should only see channels they are a member of.
        """
        if self.request.user.is_authenticated:
            return Channel.objects.filter(members__user=self.request.user).distinct().order_by('-created_at')
        return Channel.objects.none()

    def perform_create(self, serializer):
        """
        The serializer already handles creating the user as a member,
        so we just pass the context.
        """
        serializer.save()

    @action(detail=True, methods=['post'], url_path='invite-bot', serializer_class=BotInviteSerializer)
    def invite_bot(self, request, pk=None):
        """
        Invite a bot to the channel.
        """
        channel = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bot_id = serializer.validated_data['bot_id']

        # Check if bot is already in the channel
        if ChannelBot.objects.filter(channel=channel, bot_id=bot_id).exists():
            return Response({'detail': 'Bot is already in this channel.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the ChannelBot membership
        channel_bot = ChannelBot.objects.create(channel=channel, bot_id=bot_id)
        response_serializer = ChannelBotSerializer(channel_bot)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='bots')
    def bots(self, request, pk=None):
        """
        List all bots in the channel.
        """
        channel = self.get_object()
        channel_bots = ChannelBot.objects.filter(channel=channel).select_related('bot')
        serializer = ChannelBotSerializer(channel_bots, many=True)
        return Response(serializer.data)


class ThreadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Threads, nested under a Channel.
    """
    serializer_class = ThreadSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]

    def get_queryset(self):
        """
        Filter threads by the channel specified in the URL.
        """
        return Thread.objects.filter(channel_id=self.kwargs['channel_pk']).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create a new thread associated with the channel from the URL and the current user.
        """
        channel = Channel.objects.get(pk=self.kwargs['channel_pk'])
        serializer.save(created_by=self.request.user, channel=channel)


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Messages, nested under a Channel.
    Supports filtering by thread_id.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]

    def get_queryset(self):
        """
        Filter messages by the channel from the URL.
        Optionally, further filter by thread_id from query params.
        """
        queryset = Message.objects.filter(channel_id=self.kwargs['channel_pk'])

        thread_id = self.request.query_params.get('thread_id')
        if thread_id:
            # If a thread_id is provided, we need to get messages linked to that thread.
            # This requires a join through the ThreadMessage table.
            thread_message_ids = ThreadMessage.objects.filter(thread_id=thread_id).values_list('message_id', flat=True)
            queryset = queryset.filter(id__in=thread_message_ids)

        return queryset.order_by('created_at')

    def perform_create(self, serializer):
        """
        Create a new message, broadcast it via Channels, and trigger a debate round.
        """
        channel = Channel.objects.get(pk=self.kwargs['channel_pk'])
        message = serializer.save(
            author_user=self.request.user,
            author_type='user',
            channel=channel
        )

        # Broadcast the new message to the channel group
        channel_layer = get_channel_layer()
        message_data = MessageSerializer(message).data
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'message.new',
                'message': message_data
            }
        )

        # If a thread_id is provided, associate the message and trigger debate
        thread_id = self.request.data.get('thread_id')
        if thread_id:
            try:
                thread = Thread.objects.get(id=thread_id, channel=channel)
                ThreadMessage.objects.create(thread=thread, message=message)
                # Trigger the debate round task
                debate_round.delay(thread.id)
            except Thread.DoesNotExist:
                # Optionally handle this error, e.g., by raising a validation error
                pass


class VoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing Votes on a Message.
    """
    serializer_class = VoteSerializer
    permission_classes = [permissions.IsAuthenticated] # Or a custom permission

    def get_queryset(self):
        """
        Filter votes by the message specified in the URL.
        """
        return Vote.objects.filter(message_id=self.kwargs['message_pk']).order_by('-created_at')


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing Documents within a Channel.
    """
    serializer_class = DocumentSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]

    def get_queryset(self):
        """
        Filter documents by the channel specified in the URL.
        """
        return Document.objects.filter(channel_id=self.kwargs['channel_pk']).order_by('-created_at')
