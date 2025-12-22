import uuid
from django.db import models
from django.contrib.auth import get_user_model
from file_manager.models.file import File

User = get_user_model()

def version_upload_to(instance, filename):
    return f"uploads/versions/{instance.file.id}/{instance.version}/{filename}"

class FileVersion(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    file = models.ForeignKey(
        File,
        related_name='versions',
        on_delete=models.CASCADE
    )
    file_blob = models.FileField(upload_to=version_upload_to)
    version = models.PositiveIntegerField()
    size = models.BigIntegerField()
    mime_type = models.CharField(max_length=100)
    uploaded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('file', 'version')
        ordering = ['-version']
        
