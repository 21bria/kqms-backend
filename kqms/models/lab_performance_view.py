from django.db import models

class laboratoryPerformanceView(models.Model):
    tgl_deliver     = models.DateField(default=None, null=True, blank=True)
    sample_id       = models.CharField(max_length=25, default=None, null=True, blank=True)
    delivery_time   = models.CharField(max_length=25, default=None, null=True, blank=True)
    waybill_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    numb_sample     = models.IntegerField(default=None, null=True, blank=True)
    mral_order      = models.CharField(max_length=5, default=None, null=True, blank=True)
    roa_order       = models.CharField(max_length=5, default=None, null=True, blank=True)
    job_number_mral = models.CharField(max_length=25, default=None, null=True, blank=True)
    release_mral    = models.DateTimeField(default=None, null=True, blank=True)
    day_mral        = models.CharField(max_length=6, default=None, null=True, blank=True)
    time_mral       = models.CharField(max_length=9, default=None, null=True, blank=True)
    job_number_roa  = models.CharField(max_length=25, default=None, null=True, blank=True)
    release_roa     = models.DateTimeField(default=None, null=True, blank=True)
    day_roa         = models.CharField(max_length=6, default=None, null=True, blank=True)
    time_roa        = models.CharField(max_length=9, default=None, null=True, blank=True)

    class Meta:
        managed    = False
        db_table   = 'laboratory_performance'
        app_label  = 'kqms'