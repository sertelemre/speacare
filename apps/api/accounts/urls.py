from django.urls import path
from .views import UserRegistrationView, MeView, AuthExchangeView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', MeView.as_view(), name='user-me'),
    path('exchange/', AuthExchangeView.as_view(), name='auth-exchange'),
]
