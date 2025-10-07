from django.contrib import admin
from .models import (
    Channel, ChannelMember, ChannelBot, Thread, Message, ThreadMessage, 
    Vote, Document, Task, Attachment, Project, ProjectAsset
)

# ==============================================================================
# Project Admin
# ==============================================================================

class ProjectAssetInline(admin.TabularInline):
    model = ProjectAsset
    extra = 0
    readonly_fields = ['created_at', 'mime_type', 'file_size']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_active', 'created_at', 'asset_count']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectAssetInline]
    
    def asset_count(self, obj):
        return obj.assets.count()
    asset_count.short_description = 'Asset Sayısı'

@admin.register(ProjectAsset)
class ProjectAssetAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'asset_type', 'created_by', 'created_at', 'has_file', 'has_url']
    list_filter = ['asset_type', 'created_at', 'project']
    search_fields = ['name', 'description', 'summary']
    readonly_fields = ['created_at', 'mime_type', 'file_size']
    
    def has_file(self, obj):
        return bool(obj.file)
    has_file.boolean = True
    has_file.short_description = 'Dosya Var'
    
    def has_url(self, obj):
        return bool(obj.url)
    has_url.boolean = True
    has_url.short_description = 'URL Var'

# ==============================================================================
# Channel Admin
# ==============================================================================

class ChannelMemberInline(admin.TabularInline):
    model = ChannelMember
    extra = 0

class ChannelBotInline(admin.TabularInline):
    model = ChannelBot
    extra = 0

@admin.register(Channel)
class ChannelAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'is_active', 'is_private', 'created_at']
    list_filter = ['is_active', 'is_private', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at']
    inlines = [ChannelMemberInline, ChannelBotInline]
    filter_horizontal = ['projects']

# ==============================================================================
# Other Models
# ==============================================================================

@admin.register(Thread)
class ThreadAdmin(admin.ModelAdmin):
    list_display = ['topic', 'channel', 'created_by', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'channel']
    search_fields = ['topic']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'channel', 'author_display_name', 'author_type', 'created_at']
    list_filter = ['author_type', 'created_at', 'channel']
    search_fields = ['content_md']
    readonly_fields = ['created_at']

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'doc_type', 'created_by', 'created_at']
    list_filter = ['doc_type', 'created_at', 'channel']
    search_fields = ['title', 'content_md']

@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['message', 'voter_bot', 'value', 'created_at']
    list_filter = ['value', 'created_at']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'channel', 'status', 'assignee_bot', 'due_at', 'created_at']
    list_filter = ['status', 'created_at', 'channel']
    search_fields = ['title']

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['message', 'filename', 'mime', 'size', 'created_at']
    list_filter = ['mime', 'created_at']
    search_fields = ['filename']
