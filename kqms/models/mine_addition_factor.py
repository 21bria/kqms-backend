from django.db import models
from .source_model import SourceMines,SourceMinesLoading

class mineAdditionFactor(models.Model):
    type_truck  = models.CharField(max_length=100,default=None,null=True,blank=True)
    material    = models.CharField(max_length=25,default=None, null=True, blank=True)
    tf_bcm      = models.FloatField(default=None, null=True, blank=True)
    tf_ton      = models.FloatField(default=None, null=True, blank=True)
    validation  = models.CharField(max_length=100, default=None, null=True, blank=True)
    remarks     = models.CharField(max_length=255, default=None, null=True, blank=True)
    # created_at  = models.DateTimeField(auto_now_add=True)
    # updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
       return f"{self.type_truck}{self.material}"

    class Meta:
        db_table  = 'mine_addition_factor'
        app_label = 'kqms'


class volumeTruckFactorAdjustment(models.Model):
    date_start    = models.DateField(default=None,null=True,blank=True)
    date_end      = models.DateField(default=None,null=True,blank=True)
    category      = models.CharField(max_length=25,default=None,null=True,blank=True)
    vendors       = models.CharField(max_length=50,default=None,null=True,blank=True)
    sources       = models.BigIntegerField(default=None,null=True,blank=True)
    loading_point = models.BigIntegerField(default=None,null=True,blank=True)
    # sources       = models.ForeignKey(SourceMines, on_delete=models.CASCADE, db_column='sources', null=True, blank=True)
    # loading_point = models.ForeignKey(SourceMinesLoading, on_delete=models.CASCADE, db_column='loading_point', null=True, blank=True)
    type_truck    = models.CharField(max_length=50,default=None,null=True,blank=True)
    material      = models.CharField(max_length=25,default=None,null=True,blank=True)
    bcm_original  = models.FloatField(default=None,null=True,blank=True)
    ton_original  = models.FloatField(default=None,null=True,blank=True)
    bcm_updated   = models.FloatField(default=None,null=True,blank=True)
    ton_updated   = models.FloatField(default=None,null=True,blank=True)
    status        = models.CharField(max_length=50,blank=True,default=None,null=True)
    remarks       = models.CharField(max_length=255,blank=True,default=None,null=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table  ='mine_volume_factors_adjustment'
        app_label = 'kqms'


class mineVolumeAdjustment(models.Model):
    date_start    = models.DateField(default=None,null=True,blank=True)
    date_end      = models.DateField(default=None,null=True,blank=True)
    category      = models.CharField(max_length=25,default=None,null=True,blank=True)
    vendors       = models.CharField(max_length=50,default=None,null=True,blank=True)
    sources_area  = models.CharField(max_length=250,default=None,null=True,blank=True)
    loading_point = models.CharField(max_length=250,default=None,null=True,blank=True)
    type_truck    = models.CharField(max_length=50,default=None,null=True,blank=True)
    material      = models.CharField(max_length=25,default=None,null=True,blank=True)
    bcm_original  = models.FloatField(default=None,null=True,blank=True)
    ton_original  = models.FloatField(default=None,null=True,blank=True)
    bcm_updated   = models.FloatField(default=None,null=True,blank=True)
    ton_updated   = models.FloatField(default=None,null=True,blank=True)
    status        = models.CharField(max_length=50,blank=True,default=None,null=True)
    remarks       = models.CharField(max_length=255,blank=True,default=None,null=True)

    class Meta:
        managed   = False
        db_table  = 'mine_volume_adjustment'
        app_label = 'kqms'

