from django.db import models
import uuid
from kqms.models import MineUnits

class HmUnit(models.Model):
    SHIFT_CHOICES = [
        ('Day', 'Day'),
        ('Night', 'Night'),
    ]
    id  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(
        MineUnits,
        on_delete=models.PROTECT,
        related_name='hm_units'
    )
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    hm_start = models.DecimalField(max_digits=15, decimal_places=2)
    hm_end   = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(
        max_length=20,
        default='DRAFT',
        choices=[
            ('DRAFT', 'Draft'),
            ('SUBMITTED', 'Submitted'),
            ('APPROVED', 'Approved'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mine_hm_unit'
        unique_together = ('unit', 'date', 'shift')

    def __str__(self):
        return f'{self.unit.unit_code} | {self.date} | {self.shift}'
    
class UnitStatus(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=50)
    category = models.CharField(
        max_length=20,
        choices=[
            ('OPERATING', 'Operating'),
            ('STANDBY', 'Standby'),
            ('BREAKDOWN', 'Breakdown'),
            ('MAINTENANCE', 'Maintenance'),
            ('SUPPORT', 'Support'),
            ('OFF', 'Off / Non Shift'),
        ]
    )

    class Meta:
        db_table = 'mine_units_categories_status'
        app_label = 'kqms'

class UnitActivity(models.Model):
    status = models.ForeignKey(
        UnitStatus,
        on_delete=models.PROTECT,
        related_name='activities'
    )
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        db_table  = 'mine_unit_activity'
        app_label = 'kqms'

class UnitLocation(models.Model):
    code = models.CharField(max_length=50, unique=True)  # PIT, WS
    name = models.CharField(max_length=150)   

    class Meta:
        db_table  = 'mine_unit_location'
        app_label = 'kqms'

class HmUnitDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    hm_unit = models.ForeignKey(
        HmUnit,
        on_delete=models.CASCADE,
        related_name='details'
    )
    start_time = models.TimeField()
    end_time   = models.TimeField()
    duration_min = models.PositiveIntegerField()
    status   = models.ForeignKey('UnitStatus', on_delete=models.PROTECT)
    activity = models.ForeignKey('UnitActivity', on_delete=models.PROTECT)
    location = models.ForeignKey('UnitLocation', on_delete=models.PROTECT)
    category = models.CharField(
        max_length=20,
        blank=True, 
        null=True,
        choices=[
            ('Mining', 'Mining'),
            ('Project', 'Project')
        ]
    )
    remark = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'mine_hm_unit_detail'
        app_label = 'kqms'
        indexes = [
        models.Index(fields=['hm_unit']),
        models.Index(fields=['start_time', 'end_time']),
        models.Index(fields=['category'])
        ]

    