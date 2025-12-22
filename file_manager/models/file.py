import uuid
from django.db import models
from django.contrib.auth import get_user_model
from .folder import Folder

User = get_user_model()

class File(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    original_name = models.CharField(max_length=255)

    uploaded_by = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.original_name
    
