from django.db import models
from django.contrib.auth import get_user_model
from .folder import Folder
from .file import File

User = get_user_model()

class FilePermission(models.Model):
    PERMISSION_CHOICES = (
        ('view', 'View'),
        ('upload', 'Upload'),
        ('edit', 'Edit'),
        ('delete', 'Delete'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(
        Folder, null=True, blank=True, on_delete=models.CASCADE
    )
    file = models.ForeignKey(
        File, null=True, blank=True, on_delete=models.CASCADE
    )
    permission = models.CharField(max_length=10, choices=PERMISSION_CHOICES)

    class Meta:
        unique_together = ('user', 'folder', 'file', 'permission')

