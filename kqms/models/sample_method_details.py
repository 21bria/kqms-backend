from django.db import models
class SampleMethodDetail(models.Model):
    sample_method  = models.CharField(max_length=25, unique=True)
    type_id        = models.BigIntegerField(default=None, null=True, blank=True)
    type_sample    = models.CharField(max_length=25, unique=True)

    class Meta:
        managed   = False
        db_table  = 'method_details'
        app_label = 'kqms'
