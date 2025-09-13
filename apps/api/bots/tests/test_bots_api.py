import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from bots.models import Bot

User = get_user_model()

@pytest.fixture
def api_client():
    """
    Fixture to provide an authenticated API client.
    """
    user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_create_bot(api_client):
    """
    Test creating a bot for an authenticated user.
    """
    url = "/api/bots/"
    data = {
        "name": "Test Bot",
        "title": "A bot for testing",
        "llm_provider": "openai",
            "llm_model": "gpt-4o",
    }
    response = api_client.post(url, data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
    assert Bot.objects.count() == 1
    assert Bot.objects.get().name == "Test Bot"
    assert Bot.objects.get().created_by.username == 'testuser'

@pytest.mark.django_db
def test_list_bots_for_user(api_client):
    """
    Test that a user can only list their own bots.
    """
    # Create a bot for the authenticated user
    user = User.objects.get(username='testuser')
    Bot.objects.create(name="My Bot", created_by=user, llm_provider="test", llm_model="test")

    # Create another user and their bot
    other_user = User.objects.create_user(username='otheruser', password='password123', email='other@example.com')
    Bot.objects.create(name="Other User's Bot", created_by=other_user, llm_provider="test", llm_model="test")

    # List bots
    url = "/api/bots/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['name'] == "My Bot"
