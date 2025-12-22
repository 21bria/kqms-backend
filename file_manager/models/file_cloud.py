from django.db import models
from .file import File

class FileCloudLink(models.Model):
    PROVIDERS = (
        ('google', 'Google Drive'),
    )

    file = models.OneToOneField(
        File,
        related_name='cloud',
        on_delete=models.CASCADE
    )

    provider = models.CharField(max_length=20, choices=PROVIDERS)
    cloud_id = models.CharField(max_length=255)
    cloud_url = models.URLField()

    synced_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.file.original_name} ({self.provider})"
