from django.db import models
from .materials import Material  # Impor model Material

class OreClass(models.Model):
    ore_class   = models.CharField(max_length=20, unique=True)
    min_grade   = models.CharField(max_length=15, default=None, null=True, blank=True)
    max_grade   = models.CharField(max_length=15, default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    material    = models.ForeignKey(Material, on_delete=models.CASCADE, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.ore_class  

    class Meta:
        db_table  = 'ore_classes'
        app_label = 'kqms'