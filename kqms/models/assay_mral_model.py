from django.db import models
import uuid

class AssayMral(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    release_date = models.DateField(default=None, null=True, blank=True)
    release_time = models.TimeField(default=None, null=True, blank=True)
    release_mral = models.DateTimeField(default=None, null=True, blank=True)
    job_number   = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_id    = models.CharField(max_length=15, default=None, null=True, blank=True)
    ni           = models.FloatField(default=None, null=True, blank=True)
    co           = models.FloatField(default=None, null=True, blank=True)
    fe2o3        = models.FloatField(default=None, null=True, blank=True)
    fe           = models.FloatField(default=None, null=True, blank=True)
    mgo          = models.FloatField(default=None, null=True, blank=True)
    sio2         = models.FloatField(default=None, null=True, blank=True)
    no_input     = models.BigIntegerField(default=None, null=True, blank=True)
    user_id      = models.IntegerField(default=None, null=True, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'assay_mrals'
        app_label = 'kqms'




   
