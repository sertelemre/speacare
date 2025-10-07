from rest_framework import viewsets, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from .models import Bot
from .serializers import BotSerializer

# This could also be sourced from a config file or database
LLM_PROVIDERS = {
    "openai": {
        "label": "OpenAI",
        "models": ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]
    },
    "deepseek": {
        "label": "DeepSeek (OpenAI API)",
        "models": ["deepseek-chat", "deepseek-coder"]
    },
    "gemini": {
        "label": "Google Gemini",
        "models": ["gemini-1.5-pro-latest", "gemini-pro"]
    },
    "groq": {
        "label": "Groq",
        "models": ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
    }
}

class LLMProviderListView(APIView):
    """
    View to list available LLM providers and their models.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, format=None):
        """
        Return a list of all available LLM providers.
        """
        return Response(LLM_PROVIDERS)


class BotViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows bots to be viewed or edited.
    """
    queryset = Bot.objects.all()
    serializer_class = BotSerializer
    permission_classes = [permissions.AllowAny]  # Temporarily allow all for testing

    def get_queryset(self):
        """
        This view should return a list of all the bots.
        For now, show all bots for testing purposes.
        """
        # Always show all bots for now (testing purposes)
        # TODO: In production, filter by user or make it configurable
        return self.queryset.all()

    def perform_create(self, serializer):
        """
        Associate the bot with the currently authenticated user and validate the model.
        """
        provider = serializer.validated_data.get('llm_provider')
        model = serializer.validated_data.get('llm_model')

        if provider not in LLM_PROVIDERS:
            raise ValidationError(f"Invalid provider: {provider}")

        if model not in LLM_PROVIDERS[provider]['models']:
            raise ValidationError(f"Invalid model '{model}' for provider '{provider}'.")

        serializer.save(created_by=self.request.user)
