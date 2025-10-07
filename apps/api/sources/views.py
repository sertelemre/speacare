from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Source
from .serializers import SourceSerializer
from collab.permissions import IsChannelMember

class SourceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sources within a channel.
    """
    serializer_class = SourceSerializer
    permission_classes = [permissions.IsAuthenticated, IsChannelMember]

    def get_queryset(self):
        """
        Filter sources by the channel specified in the URL.
        """
        return Source.objects.filter(channel_id=self.kwargs['channel_pk']).order_by('-created_at')

    def perform_create(self, serializer):
        """
        Create a new source associated with the channel from the URL and the current user.
        """
        from collab.models import Channel
        channel = Channel.objects.get(pk=self.kwargs['channel_pk'])
        serializer.save(added_by=self.request.user, channel=channel)