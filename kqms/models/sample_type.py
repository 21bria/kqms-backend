from django.db import models
class SampleType(models.Model):
    type_sample    = models.CharField(max_length=25, unique=True)
    keterangan     = models.CharField(max_length=250, default=None, null=True, blank=True)
    status         = models.IntegerField(default=None, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.type_sample

    class Meta:
        db_table = 'sample_types'
        app_label = 'kqms'
    
    indexes = [
        models.Index(fields=['type_sample'])
    ]
