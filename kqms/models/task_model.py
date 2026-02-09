from django.db import models
import uuid
from django.contrib.auth.models import Group
from django.utils.text import slugify

class taskImports(models.Model):
    task_id            = models.CharField(max_length=255, null=True,default=None)
    successful_imports = models.IntegerField(blank=True,default=0)
    failed_imports     = models.IntegerField(blank=True,default=0)
    duplicate_imports  = models.IntegerField(blank=True,default=0)
    errors             = models.TextField(default=None, null=True, blank=True)
    duplicates         = models.TextField(default=None, null=True, blank=True)
    file_name          = models.CharField(max_length=255,default=None, null=True, blank=True)
    destination        = models.CharField(max_length=255,default=None, null=True, blank=True)
    duplicate_file_path = models.CharField(max_length=255, default=None, null=True, blank=True)
    created_at         = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.task_id 

    class Meta:
        db_table  = 'task_imports'
        app_label = 'kqms'
    
class TaskList(models.Model):
    type_table     = models.CharField(max_length=150, unique=True)  # dijadikan unique kalau jadi kode unik
    task_path      = models.CharField(max_length=255, null=True, blank=True)  # path ke task Celery
    status         = models.IntegerField(default=1, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    # Relasi ke Group
    # allowed_groups = models.ManyToManyField(Group, related_name="allowed_tasks", blank=True)
    allowed_group_names = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.type_table

    class Meta:
        db_table  = 'task_table_list'
        app_label = 'kqms'
        ordering  = ['type_table']


class importTask(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task_id    = models.CharField(max_length=100, blank=True, null=True)
    file_name  = models.CharField(max_length=255)
    task_type  = models.CharField(max_length=150, default='Import Task')
    total_rows = models.PositiveIntegerField(default=0)
    inserted   = models.PositiveIntegerField(default=0)
    skipped    = models.PositiveIntegerField(default=0)
    errors     = models.JSONField(blank=True, null=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    # date_import = models.DateField( blank=True, null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        app_label = 'kqms'
        db_table = 'mine_import_task'
