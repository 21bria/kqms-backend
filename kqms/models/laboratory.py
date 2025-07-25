from django.db import models
import uuid
class LaboratorySamples(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_received   = models.DateField(default=None, null=True, blank=True)
    time_received   = models.TimeField(default=None, null=True, blank=True)
    shift           = models.CharField(max_length=25, default=None, null=True, blank=True)
    waybill_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    qty_sample      = models.IntegerField(default=None, null=True, blank=True)
    sample_id       = models.CharField(max_length=25, default=None, null=True, blank=True)
    mral_order      = models.CharField(max_length=5, default=None, null=True, blank=True)
    roa_order       = models.CharField(max_length=5, default=None, null=True, blank=True)
    job_number      = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_wet      = models.IntegerField(default=0, null=True, blank=True)
    sample_final    = models.IntegerField(default=0, null=True, blank=True)
    sample_press    = models.IntegerField(default=0, null=True, blank=True)
    sample_analysis = models.IntegerField(default=0, null=True, blank=True)
    status          = models.CharField(max_length=50, default=None, null=True, blank=True)
    remarks         = models.CharField(max_length=255, default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'laboratory_samples'
        app_label = 'kqms'