from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

class Menu(models.Model):
    title = models.CharField(max_length=100)
    icon = models.CharField(max_length=100, null=True, blank=True)
    url = models.CharField(max_length=255, null=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    allowed_group_names = models.JSONField(default=list, blank=True)

    # Tambahan untuk kategori (seperti <li class="slide__category">)
    is_category = models.BooleanField(default=False)
    category_title = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering  = ['order']
        app_label = 'kqms'

    def __str__(self):
        return self.title
