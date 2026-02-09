from django.db import models

class BargeUnits(models.Model):
    barge_code  = models.CharField(max_length=25, unique=True)
    barge_name  = models.CharField(max_length=50, default=None, null=True, blank=True)
    capacity    = models.FloatField(default=None, null=True, blank=True)
    description = models.CharField(max_length=255, default=None, null=True, blank=True)
    active      = models.IntegerField(default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.barge_code

    class Meta:
        app_label = 'kqms'
        db_table  = 'master_barge'
        indexes   = [
            models.Index(fields=['barge_code']),
            models.Index(fields=['barge_name'])
        ]
        

class BargePort(models.Model):
    port_name   = models.CharField(max_length=150, default=None, null=True, blank=True)
    port_type   = models.CharField(max_length=50, default=None, null=True, blank=True)
    description = models.CharField(max_length=255, default=None, null=True, blank=True)
    active      = models.IntegerField(default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.port_name

    class Meta:
        app_label = 'kqms'
        db_table  = 'master_barge_port'
        indexes   = [
            models.Index(fields=['port_name']),
        ]
       