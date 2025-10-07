from rest_framework import serializers
from .models import Source

class SourceSerializer(serializers.ModelSerializer):
    """
    Serializer for the Source model.
    """
    added_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Source
        fields = ['id', 'channel', 'kind', 'pointer', 'title', 'added_by', 'created_at']
        read_only_fields = ['id', 'channel', 'added_by', 'created_at']
