from django.urls import path, include
from rest_framework_nested import routers
from .views import ChannelViewSet, ThreadViewSet, MessageViewSet, VoteViewSet, DocumentViewSet

# The main router for top-level resources
router = routers.SimpleRouter()
router.register(r'channels', ChannelViewSet, basename='channel')
# A router for top-level messages might also be useful, but for now we nest it.
# router.register(r'messages', MessageViewSet, basename='message')

# Nested router for threads and messages within a channel
channels_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
channels_router.register(r'threads', ThreadViewSet, basename='channel-threads')
channels_router.register(r'documents', DocumentViewSet, basename='channel-documents')
channels_router.register(r'messages', MessageViewSet, basename='channel-messages')

# Nested router for votes within a message
votes_router = routers.NestedSimpleRouter(channels_router, r'messages', lookup='message')
votes_router.register(r'votes', VoteViewSet, basename='message-votes')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(channels_router.urls)),
    path('', include(votes_router.urls)),
]
