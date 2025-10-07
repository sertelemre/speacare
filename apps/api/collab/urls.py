from django.urls import path, include
from rest_framework_nested import routers
from .views import ChannelViewSet, ThreadViewSet, MessageViewSet, VoteViewSet, DocumentViewSet, ProjectViewSet, ProjectAssetViewSet
from .upload_views import presign_upload

# The main router for top-level resources
router = routers.SimpleRouter()
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'projects', ProjectViewSet, basename='project')
# A router for top-level messages might also be useful, but for now we nest it.
# router.register(r'messages', MessageViewSet, basename='message')

# Nested router for threads and messages within a channel
channels_router = routers.NestedSimpleRouter(router, r'channels', lookup='channel')
channels_router.register(r'threads', ThreadViewSet, basename='channel-threads')
channels_router.register(r'documents', DocumentViewSet, basename='channel-documents')
channels_router.register(r'messages', MessageViewSet, basename='channel-messages')

# Nested router for thread actions
threads_router = routers.NestedSimpleRouter(channels_router, r'threads', lookup='thread')

# Nested router for votes within a message
votes_router = routers.NestedSimpleRouter(channels_router, r'messages', lookup='message')
votes_router.register(r'votes', VoteViewSet, basename='message-votes')

# Nested router for project assets
projects_router = routers.NestedSimpleRouter(router, r'projects', lookup='project')
projects_router.register(r'assets', ProjectAssetViewSet, basename='project-assets')


urlpatterns = [
    path('', include(router.urls)),
    path('', include(channels_router.urls)),
    path('', include(threads_router.urls)),
    path('', include(votes_router.urls)),
    path('', include(projects_router.urls)),
    path('uploads/presign/', presign_upload, name='presign-upload'),
]
