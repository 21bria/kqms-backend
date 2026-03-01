from django.db import models
import uuid

class Weather(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField()
    shift       = models.CharField(max_length=10)
    category    = models.CharField(max_length=20)
    start_time  = models.TimeField(default=None, null=True, blank=True)
    end_time    = models.TimeField(default=None, null=True, blank=True)
    duration    = models.DecimalField(max_digits=5, decimal_places=2)
    remark      = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'mine_weather'
        app_label = 'kqms'
        indexes = [
            models.Index(
                fields=['date', 'shift', 'category', 'start_time', 'end_time'],
                name='idx_weather_duplicate_check'
            )
        ]


class RainfallPoint(models.Model):
    name  = models.CharField(max_length=50)
    description = models.CharField(max_length=255,blank=True,null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'kqms'
        db_table  = 'mine_rainfall_point'
        indexes = [
            models.Index(
                fields=['name'],
                name='idx_rainfall_type'
            )
        ]

class Rainfall(models.Model):
    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date        = models.DateField()
    point       = models.ForeignKey(RainfallPoint, related_name="point_rainfall",on_delete=models.SET_NULL, null=True,blank=True,)
    milimeter   = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(blank=True,null=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'kqms'
        db_table  = 'mine_rainfall'
        indexes = [
            models.Index(
                fields=['date'],
                name='idx_rainfall'
            )
        ]