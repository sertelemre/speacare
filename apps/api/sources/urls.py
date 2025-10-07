from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SourceViewSet

# Simple router for sources
router = DefaultRouter()
router.register(r'sources', SourceViewSet, basename='sources')

urlpatterns = [
    path('', include(router.urls)),
]
