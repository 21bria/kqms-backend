from django.db import models
import uuid

class FuelStockDaily(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date       = models.DateField()
    incoming   = models.FloatField(default=0)
    remark     = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'kqms'
        db_table  = 'mine_stock_fuel'
        indexes   = [
            models.Index(fields=['date']),
        ]
        