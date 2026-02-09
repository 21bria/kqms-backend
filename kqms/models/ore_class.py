from django.db import models
from .materials import Material  # Impor model Material

class OreClass(models.Model):
    ore_class = models.CharField(max_length=20, unique=True)

    ni_min = models.FloatField(null=True, blank=True)
    ni_max = models.FloatField(null=True, blank=True)

    mgo_min = models.FloatField(null=True, blank=True)
    mgo_max = models.FloatField(null=True, blank=True)

    fe_min  = models.FloatField(null=True, blank=True)
    fe_max  = models.FloatField(null=True, blank=True)

    status   = models.BooleanField(default=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'kqms'
        db_table = 'ore_classes'
        indexes = [
            models.Index(fields=['ore_class']),
            models.Index(fields=['material']),
        ]
