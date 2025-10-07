from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import UserRegistrationView, MeView, AuthExchangeView, UserView

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('me/', MeView.as_view(), name='user-me'),
    path('user/', UserView.as_view(), name='user-detail'),
    path('exchange/', AuthExchangeView.as_view(), name='auth-exchange'),
    # JWT endpoints
    path('jwt/obtain/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('jwt/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
