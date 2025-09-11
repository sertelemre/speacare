from rest_framework import permissions
from .models import ChannelMember

class IsChannelMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a channel to view it.
    Assumes the view has a 'channel_pk' URL keyword argument.
    """

    def has_permission(self, request, view):
        # Allow read-only methods for anyone if you want public channels to be visible
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Check if the user is a member of the channel
        channel_pk = view.kwargs.get('channel_pk')
        if not request.user.is_authenticated or not channel_pk:
            return False

        return ChannelMember.objects.filter(
            channel_id=channel_pk,
            user=request.user
        ).exists()
