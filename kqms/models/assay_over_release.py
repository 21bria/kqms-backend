from django.db import models

class listOverMral(models.Model):

    tgl_sample      = models.DateField(default=None, null=True, blank=True)
    sample_id       = models.CharField(max_length=25, default=None, null=True, blank=True)
    type_sample     = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method   = models.CharField(max_length=25, default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=50, default=None, null=True, blank=True)
    delivery        = models.DateTimeField(default=None, null=True, blank=True)
    waybill_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    numb_sample     = models.IntegerField(default=None, null=True, blank=True)
    mral_order      = models.CharField(max_length=5,default=None, null=True, blank=True)
    release_mral    = models.DateTimeField(default=None, null=True, blank=True)
    day_over        = models.CharField(max_length=11,default=None, null=True, blank=True)
    time_over       = models.CharField(max_length=28,default=None, null=True, blank=True)

    class Meta:
        managed   = False
        db_table  = 'release_not_ontime_mral'
        app_label = 'kqms'

   
class listOverRoa(models.Model):

    tgl_sample      = models.DateField(default=None, null=True, blank=True)
    sample_id       = models.CharField(max_length=25, default=None, null=True, blank=True)
    type_sample     = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method   = models.CharField(max_length=25, default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=50, default=None, null=True, blank=True)
    delivery        = models.DateTimeField(default=None, null=True, blank=True)
    waybill_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    numb_sample     = models.IntegerField(default=None, null=True, blank=True)
    roa_order       = models.CharField(max_length=5,default=None, null=True, blank=True)
    release_roa     = models.DateTimeField(default=None, null=True, blank=True)
    day_over        = models.CharField(max_length=11,default=None, null=True, blank=True)
    time_over       = models.CharField(max_length=28,default=None, null=True, blank=True)

    class Meta:
        managed   = False
        db_table  = 'release_not_ontime_roa'
        app_label = 'kqms'

   

