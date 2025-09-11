from rest_framework import viewsets, permissions
from .models import Bot
from .serializers import BotSerializer

class BotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bots to be viewed or edited.
    """
    queryset = Bot.objects.all()
    serializer_class = BotSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This view should return a list of all the bots
        for the currently authenticated user.
        """
        return self.queryset.filter(created_by=self.request.user)

    def perform_create(self, serializer):
        """
        Associate the bot with the currently authenticated user.
        """
        serializer.save(created_by=self.request.user)
