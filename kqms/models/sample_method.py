from django.db import models

class SampleMethod(models.Model):
    sample_method  = models.CharField(max_length=25, unique=True)
    keterangan     = models.CharField(max_length=250, default=None, null=True, blank=True)
    status         = models.IntegerField(default=None, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.sample_method

    class Meta:
        db_table = 'sample_methods'
        app_label = 'kqms'
    
    indexes = [
        models.Index(fields=['sample_method'])
    ]
