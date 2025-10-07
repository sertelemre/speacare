from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Channel, ChannelBot, Thread, Message, ThreadMessage, Project, ProjectAsset
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .permissions import IsChannelMember
from .serializers import (
    ChannelSerializer, ChannelBotSerializer, BotInviteSerializer,
    ThreadSerializer, MessageSerializer, VoteSerializer, DocumentSerializer,
    ProjectSerializer, ProjectDetailSerializer, ProjectListSerializer, ProjectAssetSerializer
)
from .tasks import debate_round, create_consensus_document

class ChannelViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows channels to be viewed, created, and managed.
    """
    queryset = Channel.objects.all()
    serializer_class = ChannelSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily disabled for testing

    def get_queryset(self):
        """
        Users should only see channels they are a member of.
        """
        # For testing without authentication, show all channels
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            return Channel.objects.filter(members__user=self.request.user).distinct().order_by('-created_at')
        else:
            # Show all channels for testing
            return Channel.objects.all().order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create channel and make the creator an owner.
        """
        # For testing without authentication, use a default user
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            user = self.request.user
        else:
            # Use the admin user for testing
            from accounts.models import User
            user = User.objects.get(username='admin')
        
        channel = serializer.save(created_by=user)
        
        # Create channel member as owner
        from collab.models import ChannelMember
        ChannelMember.objects.create(channel=channel, user=user, role='owner')

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

    @action(detail=True, methods=['post'], url_path='stop-bots')
    def stop_bots(self, request, pk=None):
        """
        Stop bot conversations in the channel.
        """
        channel = self.get_object()
        # Set channel as inactive for bot conversations
        channel.is_active = False
        channel.save()
        
        # Broadcast to channel that bot conversations are stopped
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bots.stopped',
                'message': 'Bot conversations have been stopped'
            }
        )
        
        return Response({'status': 'Bot conversations stopped'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='start-bots')
    def start_bots(self, request, pk=None):
        """
        Start bot conversations in the channel.
        """
        channel = self.get_object()
        # Set channel as active for bot conversations
        channel.is_active = True
        channel.save()
        
        # Broadcast to channel that bot conversations are started
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'bots.started',
                'message': 'Bot conversations have been started'
            }
        )
        
        return Response({'status': 'Bot conversations started'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='clear-messages')
    def clear_messages(self, request, pk=None):
        """
        Clear all messages in the channel.
        """
        channel = self.get_object()
        
        # Delete all messages in the channel
        deleted_count = Message.objects.filter(channel=channel).delete()[0]
        
        # Broadcast to channel that messages were cleared
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'channel_{channel.id}',
            {
                'type': 'messages.cleared',
                'message': f'Chat history cleared. {deleted_count} messages deleted.'
            }
        )
        
        return Response({
            'status': 'Messages cleared successfully',
            'deleted_count': deleted_count
        }, status=status.HTTP_200_OK)


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

    @action(detail=True, methods=['post'])
    def close(self, request, pk=None, channel_pk=None):
        """
        Close a thread.
        """
        thread = self.get_object()
        thread.status = 'done'
        thread.save()
        return Response({'status': 'Thread closed successfully'})

    @action(detail=True, methods=['post'])
    def debate_round(self, request, pk=None, channel_pk=None):
        """
        Start a debate round for this thread.
        """
        thread = self.get_object()
        debate_round.delay(thread.id)
        return Response({'status': 'Debate round started'})

    @action(detail=True, methods=['post'])
    def consensus(self, request, pk=None, channel_pk=None):
        """
        Generate a consensus document for this thread.
        """
        thread = self.get_object()
        create_consensus_document.delay(thread.id)
        return Response({'status': 'Consensus document generation started'})


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Messages, nested under a Channel.
    Supports filtering by thread_id.
    """
    serializer_class = MessageSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily for testing

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
        Create a new message, broadcast it via Channels, and trigger bot responses.
        """
        channel = Channel.objects.get(pk=self.kwargs['channel_pk'])
        
        # For testing without authentication, use a default user
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            user = self.request.user
        else:
            # Use the admin user for testing
            from accounts.models import User
            user, _ = User.objects.get_or_create(username='admin', defaults={'email': 'admin@example.com'})
        
        message = serializer.save(
            author_user=user,
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

        # If channel was waiting for this user, clear the waiting state
        if channel.waiting_for_user == self.request.user:
            channel.waiting_for_user = None
            channel.save()

        # If channel was stopped (is_active=False), reactivate it when user sends a message
        if not channel.is_active:
            channel.is_active = True
            channel.save()
            # Broadcast that channel is reactivated
            async_to_sync(channel_layer.group_send)(
                f'channel_{channel.id}',
                {
                    'type': 'channel.reactivated',
                    'message': f'Channel reactivated by {self.request.user.username}',
                    'reactivated_by': self.request.user.username
                }
            )

        # Trigger bot responses for all bots in the channel (only if channel is active and not waiting for another user)
        if channel.is_active and not channel.waiting_for_user:
            channel_bots = ChannelBot.objects.filter(channel=channel, is_active=True).select_related('bot')
            # Trigger bots sequentially with short delays to ensure they see each other's messages
            for i, channel_bot in enumerate(channel_bots):
                # Trigger bot response task with short delays (2, 4, 6 seconds)
                from .tasks import bot_response
                bot_response.apply_async(args=[channel_bot.bot.id, message.id], countdown=i*2)  # 0, 2, 4 seconds delay

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


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Projects.
    """
    permission_classes = [permissions.AllowAny]  # Temporarily disabled for testing

    def get_queryset(self):
        """
        Users should only see projects they created.
        """
        # For testing without authentication, show all projects
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            return Project.objects.filter(created_by=self.request.user).order_by('-created_at')
        else:
            # Show all projects for testing
            return Project.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        """
        Use different serializers for list and detail views.
        """
        if self.action == 'list':
            return ProjectListSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return ProjectDetailSerializer
        return ProjectSerializer

    def perform_create(self, serializer):
        """
        Create a new project with the current user as creator.
        """
        # For testing without authentication, use a default user
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            user = self.request.user
        else:
            # Use the test user we created earlier
            from accounts.models import User
            user, _ = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        serializer.save(created_by=user)

    @action(detail=True, methods=['get'], url_path='assets')
    def assets(self, request, pk=None):
        """
        List all assets for a specific project.
        """
        project = self.get_object()
        assets = ProjectAsset.objects.filter(project=project).order_by('-created_at')
        serializer = ProjectAssetSerializer(assets, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='add-asset')
    def add_asset(self, request, pk=None):
        """
        Add a new asset to the project.
        """
        project = self.get_object()
        serializer = ProjectAssetSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save(project=project, created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProjectAssetViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing ProjectAssets.
    """
    serializer_class = ProjectAssetSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily disabled for testing

    def get_queryset(self):
        """
        Filter assets by project and user permissions.
        """
        project_id = self.kwargs.get('project_pk')
        if project_id:
            # For testing without authentication, show all assets for the project
            if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
                project = Project.objects.filter(id=project_id, created_by=self.request.user).first()
            else:
                project = Project.objects.filter(id=project_id).first()
            
            if project:
                return ProjectAsset.objects.filter(project=project).order_by('-created_at')
        return ProjectAsset.objects.none()

    def perform_create(self, serializer):
        """
        Create a new asset with the current user as creator.
        """
        project_id = self.kwargs.get('project_pk')
        
        # For testing without authentication, use a default user
        if hasattr(self.request, 'user') and self.request.user and self.request.user.is_authenticated:
            user = self.request.user
        else:
            from accounts.models import User
            user, _ = User.objects.get_or_create(username='testuser', defaults={'email': 'test@example.com'})
        
        project = Project.objects.get(id=project_id, created_by=user)
        serializer.save(project=project, created_by=user)

    @action(detail=True, methods=['post'], url_path='generate-summary')
    def generate_summary(self, request, pk=None, project_pk=None):
        """
        Generate AI summary for the asset (placeholder for future AI integration).
        """
        asset = self.get_object()
        
        # TODO: Implement AI summary generation
        # For now, return a placeholder response
        return Response({
            'message': 'AI summary generation will be implemented in the future',
            'asset_id': asset.id
        }, status=status.HTTP_200_OK)
