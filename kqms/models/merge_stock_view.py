from django.db import models

class domeMergeView(models.Model):
    dome_primary     = models.CharField(max_length=50, default=None, null=True, blank=True)
    original_dome    = models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_primary  = models.FloatField( default=None, null=True, blank=True)
    dome_new         = models.CharField(max_length=50, default=None, null=True, blank=True)
    dome_second      = models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_second   = models.FloatField(default=None, null=True, blank=True)
    sum_tonnage      = models.FloatField( default=None, null=True, blank=True)
    status           = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_id           = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks          = models.TextField(default=None, null=True, blank=True)

    class Meta:
        managed     = False
        db_table    = 'compositing_domes_v'
        app_label   = 'kqms'

class stockpileMergeView(models.Model):
    stockpile_ori   = models.BigIntegerField(default=None, null=True, blank=True)
    stockpile       = models.CharField(max_length=50, default=None, null=True, blank=True)
    tonnage_primary = models.FloatField( default=None, null=True, blank=True)
    stockpile_new   = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile_second= models.BigIntegerField(default=None, null=True, blank=True)
    tonnage_second  = models.FloatField(default=None, null=True, blank=True)
    sum_tonnage     = models.FloatField( default=None, null=True, blank=True)
    ref_id          = models.CharField(max_length=15, default=None, null=True, blank=True)
    status          = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)

    class Meta:
        managed     = False
        db_table    = 'compositing_stock_v'
        app_label   = 'kqms'