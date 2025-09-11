import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from collab.models import Channel, ChannelMember

User = get_user_model()

@pytest.fixture
def api_client_user_channel():
    """
    Fixture to provide an authenticated client and a channel owned by that user.
    """
    user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
    client = APIClient()
    client.force_authenticate(user=user)
    channel = Channel.objects.create(name="Test Channel", created_by=user)
    ChannelMember.objects.create(channel=channel, user=user, role='owner')
    return client, user, channel

@pytest.mark.django_db
def test_create_thread_in_channel(api_client_user_channel):
    """
    Test creating a thread in a channel the user is a member of.
    """
    client, user, channel = api_client_user_channel
    url = f"/api/channels/{channel.pk}/threads/"
    data = {"topic": "New Discussion Topic"}
    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert channel.threads.count() == 1
    assert channel.threads.first().topic == "New Discussion Topic"
    assert channel.threads.first().created_by == user

@pytest.mark.django_db
def test_list_threads_in_channel(api_client_user_channel):
    """
    Test listing threads from a specific channel.
    """
    client, user, channel = api_client_user_channel
    channel.threads.create(topic="Topic 1", created_by=user)
    channel.threads.create(topic="Topic 2", created_by=user)

    url = f"/api/channels/{channel.pk}/threads/"
    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

@pytest.mark.django_db
def test_cannot_access_threads_in_unauthorized_channel():
    """
    Test that a user cannot create or list threads in a channel they are not a member of.
    """
    # User 1 and their channel
    user1 = User.objects.create_user(username='user1', password='p', email='user1@e.com')
    channel1 = Channel.objects.create(name="User1's Channel", created_by=user1)
    ChannelMember.objects.create(channel=channel1, user=user1, role='owner')

    # User 2 (the one making the request)
    user2 = User.objects.create_user(username='user2', password='p', email='user2@e.com')
    client = APIClient()
    client.force_authenticate(user=user2)

    # Try to list threads from User1's channel
    list_url = f"/api/channels/{channel1.pk}/threads/"
    response = client.get(list_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN

    # Try to create a thread in User1's channel
    create_url = f"/api/channels/{channel1.pk}/threads/"
    data = {"topic": "Hijacking Topic"}
    response = client.post(create_url, data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
