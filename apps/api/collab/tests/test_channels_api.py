import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from collab.models import Channel, ChannelMember
from bots.models import Bot

User = get_user_model()

@pytest.fixture
def api_client():
    user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
    client = APIClient()
    client.force_authenticate(user=user)
    return client

@pytest.mark.django_db
def test_create_channel(api_client):
    """
    Test creating a channel, which should also make the creator an owner.
    """
    url = "/api/channels/"
    data = {"name": "Test Channel", "description": "A channel for testing."}
    response = api_client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Channel.objects.count() == 1

    channel = Channel.objects.get()
    assert channel.name == "Test Channel"

    # Verify the creator is an owner
    assert ChannelMember.objects.filter(channel=channel, user__username='testuser', role='owner').exists()

@pytest.mark.django_db
def test_list_channels(api_client):
    """
    Test that a user can only list channels they are a member of.
    """
    user = User.objects.get(username='testuser')

    # Create a channel the user is a member of
    ch1 = Channel.objects.create(name="My Channel", created_by=user)
    ChannelMember.objects.create(channel=ch1, user=user, role='owner')

    # Create another channel the user is not a member of
    other_user = User.objects.create_user(username='otheruser', password='password123', email='other@example.com')
    Channel.objects.create(name="Other Channel", created_by=other_user)

    url = "/api/channels/"
    response = api_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['name'] == "My Channel"

@pytest.mark.django_db
def test_invite_and_list_bots_in_channel(api_client):
    """
    Test inviting a bot to a channel and listing the bots in that channel.
    """
    user = User.objects.get(username='testuser')
    channel = Channel.objects.create(name="Bot Test Channel", created_by=user)
    ChannelMember.objects.create(channel=channel, user=user, role='owner')
    bot = Bot.objects.create(name="Invited Bot", created_by=user, llm_provider="test", llm_model="test")

    # Invite the bot
    invite_url = f"/api/channels/{channel.pk}/invite-bot/"
    invite_data = {"bot_id": bot.pk}
    response = api_client.post(invite_url, invite_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

    # List the bots in the channel
    list_bots_url = f"/api/channels/{channel.pk}/bots/"
    response = api_client.get(list_bots_url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1
    assert response.data[0]['bot']['name'] == "Invited Bot"
