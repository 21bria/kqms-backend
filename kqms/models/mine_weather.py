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