from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BotViewSet, LLMProviderListView

router = DefaultRouter()
router.register(r'', BotViewSet, basename='bot')

urlpatterns = [
    path('llm-providers/', LLMProviderListView.as_view(), name='llm-provider-list'),
    path('', include(router.urls)),
]
