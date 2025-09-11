from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import UserRegistrationSerializer, UserSerializer

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveAPIView):
    """
    View to retrieve the authenticated user's details.
    """
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class AuthExchangeView(APIView):
    """
    Placeholder view for exchanging a NextAuth JWT for an API JWT.
    """
    permission_classes = [permissions.AllowAny] # Or IsAuthenticated depending on the flow

    def post(self, request, *args, **kwargs):
        # TODO: Implement the logic to validate the NextAuth JWT.
        # This will likely involve:
        # 1. Getting the public key for the NextAuth provider (e.g., Google).
        # 2. Decoding and validating the token signature and claims.
        # 3. Finding or creating a local user matching the token's email.
        # 4. Generating a new SimpleJWT token pair for the local user.
        # 5. Returning the new token pair.
        return Response(
            {"detail": "Not Implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
