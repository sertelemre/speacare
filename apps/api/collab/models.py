from django.conf import settings
from django.db import models

# ==============================================================================
# Channel Models
# ==============================================================================

class Channel(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_channels')
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ChannelMember(models.Model):
    ROLE_CHOICES = [('owner', 'Owner'), ('member', 'Member')]
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='channel_memberships')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('channel', 'user')

class ChannelBot(models.Model):
    POLICY_CHOICES = [('always', 'Always On'), ('on_mention', 'On Mention'), ('topic_based', 'Topic Based')]
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='bots')
    bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='channel_assignments')
    is_active = models.BooleanField(default=True)
    join_policy = models.CharField(max_length=20, choices=POLICY_CHOICES, default='always')

    class Meta:
        unique_together = ('channel', 'bot')
        indexes = [models.Index(fields=['channel'])]

# ==============================================================================
# Thread and Message Models
# ==============================================================================

class Thread(models.Model):
    STATUS_CHOICES = [('open', 'Open'), ('frozen', 'Frozen'), ('done', 'Done')]
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='threads')
    topic = models.CharField(max_length=255)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.topic

class Message(models.Model):
    AUTHOR_TYPE_CHOICES = [('user', 'User'), ('bot', 'Bot'), ('system', 'System')]
    STANCE_CHOICES = [('pro', 'Pro'), ('con', 'Con'), ('neutral', 'Neutral')]

    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='messages')
    author_type = models.CharField(max_length=10, choices=AUTHOR_TYPE_CHOICES)
    author_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    author_bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, null=True, blank=True)
    content_md = models.TextField()
    stance = models.CharField(max_length=10, choices=STANCE_CHOICES, null=True, blank=True)
    reply_to = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)
    meta_json = models.JSONField(default=dict, blank=True)

    class Meta:
        indexes = [models.Index(fields=['channel', 'created_at'])]

    @property
    def author_display_name(self):
        if self.author_type == 'user' and self.author_user:
            return self.author_user.username
        if self.author_type == 'bot' and self.author_bot:
            return self.author_bot.name
        return "System"

class ThreadMessage(models.Model):
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, related_name='thread_messages')
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='thread_associations')

    class Meta:
        unique_together = ('thread', 'message')
        indexes = [models.Index(fields=['thread'])]

class Attachment(models.Model):
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='attachments')
    url = models.URLField()
    filename = models.CharField(max_length=255)
    mime = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

# ==============================================================================
# Document, Vote, and Task Models
# ==============================================================================

class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ('consensus', 'Consensus'),
        ('brief', 'Brief'),
        ('summary', 'Summary'),
        ('risk_log', 'Risk Log')
    ]
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='documents')
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, null=True, blank=True, related_name='documents')
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    content_md = models.TextField()
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Vote(models.Model):
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='votes')
    voter_bot = models.ForeignKey('bots.Bot', on_delete=models.CASCADE, related_name='votes')
    value = models.IntegerField(choices=[(-1, 'Downvote'), (0, 'Neutral'), (1, 'Upvote')])
    rationale_md = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Task(models.Model):
    STATUS_CHOICES = [('todo', 'To Do'), ('doing', 'In Progress'), ('done', 'Done')]
    channel = models.ForeignKey('Channel', on_delete=models.CASCADE, related_name='tasks')
    thread = models.ForeignKey('Thread', on_delete=models.CASCADE, null=True, blank=True, related_name='tasks')
    title = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='todo')
    assignee_bot = models.ForeignKey('bots.Bot', on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    due_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
