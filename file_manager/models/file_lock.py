import uuid
from django.db import models
from django.contrib.auth import get_user_model
from .file import File

User = get_user_model()

class FileLock(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    file = models.OneToOneField(
        File,
        related_name='lock',
        on_delete=models.CASCADE
    )

    locked_by = models.ForeignKey(
        User, on_delete=models.CASCADE
    )

    locked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.file.original_name} locked by {self.locked_by}"
    
    class Meta:
        ordering = ['-locked_at']