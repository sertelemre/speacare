from django.conf import settings
from django.db import models

class Bot(models.Model):
    STANCE_CHOICES = [
        ('support', 'Support'),
        ('neutral', 'Neutral'),
        ('critical', 'Critical'),
        ('devils_advocate', "Devil's Advocate"),
    ]

    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    character = models.TextField(blank=True, help_text="Bot's personality, background, and communication style")
    job_description = models.TextField(blank=True, help_text="Bot's professional role, expertise, and responsibilities")
    persona_json = models.JSONField(default=dict)
    llm_provider = models.CharField(max_length=100)
    llm_model = models.CharField(max_length=100)
    temperature = models.FloatField(default=0.7)
    system_prompt = models.TextField(blank=True)
    background = models.TextField(blank=True)
    expertise_tags = models.JSONField(default=list)
    stance_profile = models.CharField(max_length=20, choices=STANCE_CHOICES, default='neutral')
    color = models.CharField(max_length=7, default='#3B82F6', help_text="Hex color code for bot avatar")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bots')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class BotSource(models.Model):
    """
    Through model to link Bots to their knowledge Sources.
    """
    bot = models.ForeignKey('Bot', on_delete=models.CASCADE)
    source = models.ForeignKey('sources.Source', on_delete=models.CASCADE)
    # You could add extra fields here about the relationship, e.g., how the bot uses this source.

    class Meta:
        unique_together = ('bot', 'source')

    def __str__(self):
        return f"{self.bot.name} - {self.source.title}"
