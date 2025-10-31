from django.db import models

class SellingDetailsBargingView(models.Model):
    date_barge_in       = models.DateField(default=None, null=True, blank=True)
    date_barge_out      = models.DateField(default=None, null=True, blank=True)
    barge_code          = models.CharField(max_length=50, default=None, null=True, blank=True)
    shift               = models.CharField(max_length=10, default=None, null=True, blank=True)
    dome                = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile           = models.CharField(max_length=50, default=None, null=True, blank=True)
    material            = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_code           = models.CharField(max_length=15, default=None, null=True, blank=True)
    ritase              = models.IntegerField(default=None, null=True, blank=True)
    tonnage             = models.FloatField(default=None, null=True, blank=True)
    ton_barge_load      = models.FloatField(default=None, null=True, blank=True)
    ton_barge_unload    = models.FloatField(default=None, null=True, blank=True)
    ton_barge_unload    = models.FloatField(default=None, null=True, blank=True)
    fill_adjust         = models.FloatField(default=None, null=True, blank=True)
    batch               = models.CharField(max_length=25, default=None, null=True, blank=True)
    code_inc            = models.CharField(max_length=25, default=None, null=True, blank=True)
    code_sub            = models.CharField(max_length=150, default=None, null=True, blank=True)
    code_batch_in       = models.CharField(max_length=100, default=None, null=True, blank=True)
    code_batch_ex       = models.CharField(max_length=100, default=None, null=True, blank=True)
    code_batch_pulp     = models.CharField(max_length=100, default=None, null=True, blank=True)
    surv_order          = models.CharField(max_length=100, default=None, null=True, blank=True)
    code_fix_batch      = models.CharField(max_length=100, default=None, null=True, blank=True)
    code_lot            = models.CharField(max_length=100, default=None, null=True, blank=True)
    factory_stock       = models.CharField(max_length=100, default=None, null=True, blank=True)
    type_selling        = models.CharField(max_length=100, default=None, null=True, blank=True)
    date_hauling        = models.DateField(default=None, null=True, blank=True)
    time_hauling        = models.TimeField(default=None, null=True, blank=True)
    no_input            = models.CharField(max_length=50, default=None, null=True, blank=True)
    sale_adjust         = models.CharField(max_length=25, default=None, null=True, blank=True)
    sale_dome           = models.CharField(max_length=25, default=None, null=True, blank=True)
    status_barging      = models.CharField(max_length=50, default=None, null=True, blank=True)
    direct              = models.CharField(max_length=25, default=None, null=True, blank=True)
    remarks             = models.CharField(max_length=255, default=None, null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed   = False
        db_table  = 'details_selling_barging'
        app_label = 'kqms'


class SellingDetailsBargingTempView(models.Model):
    date_hauling   = models.DateField(default=None, null=True, blank=True)
    time_hauling   = models.TimeField(default=None, null=True, blank=True)
    barge_code     = models.CharField(max_length=50, default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    dome           = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile      = models.CharField(max_length=50, default=None, null=True, blank=True)
    material       = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_code      = models.CharField(max_length=15, default=None, null=True, blank=True)
    tonnage        = models.FloatField(default=None, null=True, blank=True)
    code_lot       = models.CharField(max_length=100, default=None, null=True, blank=True)
    code_inc       = models.CharField(max_length=25, default=None, null=True, blank=True)
    code_sub       = models.CharField(max_length=25, default=None, null=True, blank=True)
    type_selling   = models.CharField(max_length=100, default=None, null=True, blank=True)
    sale_adjust    = models.CharField(max_length=255, default=None, null=True, blank=True)
    no_urut        = models.IntegerField(default=0, null=True, blank=True)
    remarks        = models.CharField(max_length=255, default=None, null=True, blank=True)
    status         = models.IntegerField(default=None, null=True, blank=True)
    
    class Meta:
        managed   = False
        db_table  = 'details_selling_barging_temp'
        app_label = 'kqms'