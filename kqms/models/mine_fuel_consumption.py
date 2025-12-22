from django.db import models
import uuid

class FuelConsumption(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date            = models.DateField()
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    unit            = models.CharField(max_length=25, default=None, null=True, blank=True)
    hours_metre     = models.CharField(max_length=25, default=None, null=True, blank=True)
    drivers         = models.CharField(max_length=50, default=None, null=True, blank=True)
    charging_time   = models.TimeField()
    volume          = models.FloatField(default=None, null=True, blank=True)
    category        = models.CharField(max_length=50, default=None, null=True, blank=True)
    storage         = models.CharField(max_length=150, default=None, null=True, blank=True)
    operator        = models.CharField(max_length=150, default=None, null=True, blank=True)
    remark          = models.TextField(blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'mine_units_fuel_consumption'
        app_label = 'kqms'
