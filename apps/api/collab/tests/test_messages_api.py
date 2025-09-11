import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from collab.models import Channel, ChannelMember, Thread, Message, ThreadMessage

User = get_user_model()

@pytest.fixture
def api_client_user_channel_thread():
    """
    Fixture to provide a client, user, channel, and a thread within the channel.
    """
    user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
    client = APIClient()
    client.force_authenticate(user=user)
    channel = Channel.objects.create(name="Test Channel", created_by=user)
    ChannelMember.objects.create(channel=channel, user=user, role='owner')
    thread = Thread.objects.create(channel=channel, topic="Test Thread", created_by=user)
    return client, user, channel, thread

@pytest.mark.django_db
def test_create_message_in_channel(api_client_user_channel_thread):
    """
    Test creating a simple message in a channel (not associated with a thread).
    """
    client, _, channel, _ = api_client_user_channel_thread
    url = f"/api/channels/{channel.pk}/messages/"
    data = {"content_md": "This is a general channel message."}
    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Message.objects.count() == 1
    message = Message.objects.first()
    assert message.content_md == "This is a general channel message."
    assert message.author_user.username == 'testuser'
    assert ThreadMessage.objects.count() == 0 # Not linked to a thread

@pytest.mark.django_db
def test_create_message_in_thread(api_client_user_channel_thread):
    """
    Test creating a message and associating it with a thread.
    """
    client, _, channel, thread = api_client_user_channel_thread
    url = f"/api/channels/{channel.pk}/messages/"
    data = {
        "content_md": "This message is for the test thread.",
        "thread_id": thread.pk
    }
    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert Message.objects.count() == 1
    assert ThreadMessage.objects.count() == 1
    assert ThreadMessage.objects.first().thread == thread
    assert ThreadMessage.objects.first().message.content_md == "This message is for the test thread."

@pytest.mark.django_db
def test_list_and_filter_messages(api_client_user_channel_thread):
    """
    Test listing all messages in a channel and filtering them by thread_id.
    """
    client, user, channel, thread = api_client_user_channel_thread

    # Create one message in the thread
    msg1 = Message.objects.create(channel=channel, author_user=user, author_type='user', content_md="Thread message")
    ThreadMessage.objects.create(thread=thread, message=msg1)

    # Create one message not in the thread
    Message.objects.create(channel=channel, author_user=user, author_type='user', content_md="General message")

    # 1. List all messages in the channel
    url = f"/api/channels/{channel.pk}/messages/"
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    # 2. Filter messages by thread_id
    url_filtered = f"/api/channels/{channel.pk}/messages/?thread_id={thread.pk}"
    response_filtered = client.get(url_filtered)
    assert response_filtered.status_code == status.HTTP_200_OK
    assert len(response_filtered.data) == 1
    assert response_filtered.data[0]['content_md'] == "Thread message"
