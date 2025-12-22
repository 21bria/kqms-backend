import uuid
from django.db import models
from django.contrib.auth import get_user_model
from .file import File

User = get_user_model()

class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('upload', 'Upload'),
        ('replace', 'Replace'),
        ('delete', 'Delete'),
        ('restore', 'Restore'),
        ('lock', 'Lock'),
        ('unlock', 'Unlock'),
        ('open', 'Open'),
        ('sync', 'Sync from Google'),
        ('version', 'Create Version'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    file = models.ForeignKey(
        File, related_name='audit_logs',
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User, null=True, on_delete=models.SET_NULL
    )

    action = models.CharField(max_length=20, choices=ACTION_CHOICES)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    extra = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} {self.action} {self.file}"
