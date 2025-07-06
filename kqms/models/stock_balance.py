from django.db import models
from decimal import Decimal
from .source_model import SourceMinesDome, SourceMinesDumping
from .materials import Material
import uuid

class DomeBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dome = models.ForeignKey(SourceMinesDome, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    date = models.DateField()

    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    total_in = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    total_out = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    closing_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )

    class Meta:
        unique_together = ('dome', 'material', 'date')
        db_table  = 'balance_dome'
        app_label = 'kqms'

class StockpileBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stockpile = models.ForeignKey(SourceMinesDumping, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    date = models.DateField()

    opening_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    total_in = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    total_out = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )
    closing_balance = models.DecimalField(
        max_digits=12, decimal_places=2, default=Decimal('0')
    )

    class Meta:
        unique_together = ('stockpile', 'material', 'date')
        db_table  = 'balance_stockpile'
        app_label = 'kqms'
