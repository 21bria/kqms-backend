from django.db import models
from .sample_type import SampleType 

class SampleTypeDetails(models.Model):

    id_type     = models.ForeignKey(SampleType, related_name='details_type_sample', on_delete=models.CASCADE)
    id_method   = models.IntegerField(default=None, null=True, blank=True)
    remakrs     = models.CharField(max_length=250, default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sample_type_details'
        app_label = 'kqms'
