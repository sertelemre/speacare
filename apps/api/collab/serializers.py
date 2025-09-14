from rest_framework import serializers
from .models import Channel, ChannelMember, ChannelBot, Thread, Message, Vote, Document
from bots.models import Bot
from bots.serializers import BotSerializer # Reuse BotSerializer for nested representation

class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and listing Channels.
    """
    # Using StringRelatedField for read-only representation of the creator's username.
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_by', 'is_private', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by']

    def create(self, validated_data):
        """
        Custom create method to also make the channel creator an 'owner'.
        """
        user = self.context['request'].user
        channel = Channel.objects.create(created_by=user, **validated_data)
        ChannelMember.objects.create(channel=channel, user=user, role='owner')
        return channel


class ChannelDetailSerializer(ChannelSerializer):
    """
    More detailed serializer for a single channel view, could include members, bots, etc.
    For now, it's the same as the base serializer.
    """
    pass


class ChannelBotSerializer(serializers.ModelSerializer):
    """
    Serializer for listing bots that are members of a channel.
    Uses a nested BotSerializer to show bot details.
    """
    bot = BotSerializer(read_only=True)

    class Meta:
        model = ChannelBot
        fields = ['id', 'bot', 'is_active', 'join_policy']


class BotInviteSerializer(serializers.Serializer):
    """
    A simple serializer to validate the bot_id for an invitation.
    """
    bot_id = serializers.IntegerField(required=True)

    def validate_bot_id(self, value):
        """
        Check if the bot exists.
        In a real application, we might also check if the user has permission
        to add this bot (e.g., it's public or created by them).
        """
        if not Bot.objects.filter(id=value).exists():
            raise serializers.ValidationError("A bot with this ID does not exist.")
        return value


class ThreadSerializer(serializers.ModelSerializer):
    """
    Serializer for Threads within a channel.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    channel = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Thread
        fields = ['id', 'channel', 'topic', 'created_by', 'status', 'created_at']
        read_only_fields = ['id', 'channel', 'created_by', 'created_at']


class MessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Messages within a channel.
    """
    author_user = serializers.StringRelatedField(read_only=True)
    author_bot = serializers.StringRelatedField(read_only=True)
    thread_id = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = [
            'id', 'channel', 'author_type', 'author_user', 'author_bot',
            'content_md', 'stance', 'reply_to', 'created_at', 'meta_json',
            'thread_id'
        ]
        read_only_fields = [
            'id', 'channel', 'author_type', 'author_user', 'author_bot', 'created_at', 'thread_id'
        ]

    def get_thread_id(self, obj):
        """
        Get the thread ID if the message is associated with a thread.
        """
        association = obj.thread_associations.first()
        if association:
            return association.thread.id
        return None


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for the Vote model.
    """
    voter_bot = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Vote
        fields = ['id', 'message', 'voter_bot', 'value', 'rationale_md', 'created_at']
        read_only_fields = fields


class DocumentSerializer(serializers.ModelSerializer):
    """
    Serializer for the Document model.
    """
    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Document
        fields = ['id', 'channel', 'thread', 'title', 'doc_type', 'content_md', 'created_by', 'created_at']
        read_only_fields = ['id', 'channel', 'thread', 'created_by', 'created_at']
