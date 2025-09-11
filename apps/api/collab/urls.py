from django.urls import path, include
from rest_framework_nested import routers
from .views import ChannelViewSet, ThreadViewSet, MessageViewSet

# The main router for top-level resources
router = routers.SimpleRouter()
router.register(r'channels', ChannelViewSet, basename='channel')

# Nested router for threads within a channel
channels_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
channels_router.register(r'threads', ThreadViewSet, basename='channel-threads')

# Nested router for messages within a channel
# We are not nesting under threads for now, as per the spec: GET /channels/{id}/messages?thread_id=...
channels_router.register(r'messages', MessageViewSet, basename='channel-messages')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(channels_router.urls)),
]
