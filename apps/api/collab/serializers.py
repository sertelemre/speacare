from rest_framework import serializers
from .models import Channel, ChannelMember, ChannelBot, Thread, Message, Vote, Document, Project, ProjectAsset
from bots.models import Bot
from bots.serializers import BotSerializer # Reuse BotSerializer for nested representation

class ChannelSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and listing Channels.
    """
    # Using StringRelatedField for read-only representation of the creator's username.
    created_by = serializers.StringRelatedField(read_only=True)
    # Projects field'ını nested serializer ile düzelt
    projects = serializers.SerializerMethodField()

    class Meta:
        model = Channel
        fields = ['id', 'name', 'description', 'created_by', 'projects', 'is_private', 'is_active', 'waiting_for_user', 'created_at']
        read_only_fields = ['id', 'created_at', 'created_by', 'waiting_for_user']

    def get_projects(self, obj):
        """
        Projects field'ını nested olarak döndür
        """
        return [{'id': project.id, 'name': project.name} for project in obj.projects.all()]

    # create metodu kaldırıldı - perform_create kullanılıyor


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
    author_bot = serializers.SerializerMethodField()
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

    def get_author_bot(self, obj):
        """
        Bot bilgisini isim ve renk ile birlikte döndür
        """
        if obj.author_bot:
            return {
                'name': obj.author_bot.name,
                'color': obj.author_bot.color
            }
        return None

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


class ProjectAssetSerializer(serializers.ModelSerializer):
    """
    Serializer for ProjectAsset model.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    file_url = serializers.SerializerMethodField()

    class Meta:
        model = ProjectAsset
        fields = [
            'id', 'project', 'name', 'asset_type', 'description', 'summary',
            'file', 'file_url', 'url', 'mime_type', 'file_size', 
            'created_by', 'created_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'mime_type', 'file_size']

    def get_file_url(self, obj):
        """
        Dosya URL'sini döndür
        """
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None

    def validate(self, data):
        """
        En az bir dosya veya URL olmalı
        """
        if not data.get('file') and not data.get('url'):
            raise serializers.ValidationError("En az bir dosya veya URL girmelisiniz.")
        return data


class ProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Project model.
    """
    created_by = serializers.StringRelatedField(read_only=True)
    assets = ProjectAssetSerializer(many=True, read_only=True)
    asset_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'details', 'created_by', 
            'is_active', 'created_at', 'updated_at', 'assets', 'asset_count'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']

    def get_asset_count(self, obj):
        """
        Projeye ait asset sayısını döndür
        """
        return obj.assets.count()

    # create metodu kaldırıldı - perform_create kullanılıyor


class ProjectDetailSerializer(ProjectSerializer):
    """
    Detaylı proje serializer'ı - tüm asset'leri içerir
    """
    pass


class ProjectListSerializer(serializers.ModelSerializer):
    """
    Liste görünümü için basit proje serializer'ı
    """
    created_by = serializers.StringRelatedField(read_only=True)
    asset_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'created_by', 
            'is_active', 'created_at', 'asset_count'
        ]

    def get_asset_count(self, obj):
        return obj.assets.count()
