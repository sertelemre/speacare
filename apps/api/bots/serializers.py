from rest_framework import serializers
from .models import Bot

class BotSerializer(serializers.ModelSerializer):
    """
    Serializer for the Bot model.
    """
    created_by = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Bot
        fields = [
            'id',
            'name',
            'title',
            'character',
            'job_description',
            'persona_json',
            'llm_provider',
            'llm_model',
            'temperature',
            'system_prompt',
            'background',
            'expertise_tags',
            'stance_profile',
            'color',
            'created_by',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        # Set the created_by field to the current user during creation
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
