from django.conf import settings
from django.db import models

class Source(models.Model):
    KIND_CHOICES = [
        ('url', 'URL'),
        ('file', 'File'),
        ('kb', 'Knowledge Base'),
    ]

    channel = models.ForeignKey('collab.Channel', on_delete=models.CASCADE, related_name='sources')
    kind = models.CharField(max_length=10, choices=KIND_CHOICES)
    pointer = models.TextField(help_text="URL, file path, or KB identifier")
    title = models.CharField(max_length=255)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='added_sources')
    created_at = models.DateTimeField(auto_now_add=True)

    # Bots can be linked to a source via the BotSource model in the 'bots' app.
    # We can define a ManyToManyField here using the 'through' model for convenience.
    bots = models.ManyToManyField('bots.Bot', through='bots.BotSource', related_name='sources')

    def __str__(self):
        return self.title
