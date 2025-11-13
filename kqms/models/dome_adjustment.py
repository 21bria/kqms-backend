from django.db import models

class domeAdjustment(models.Model):
    id_dome        = models.BigIntegerField(default=None,null=True,blank=True)
    current_total  = models.FloatField(default=0,null=True,blank=True)
    target_total   = models.FloatField(default=0,null=True,blank=True)
    scale_factor   = models.FloatField(default=0,null=True,blank=True)
    description    = models.TextField(default=None,null=True,blank=True)
    cek_duplicated = models.CharField(max_length=255,default=None,null=True,blank=True)
    id_user        = models.IntegerField(default=None,null=True,blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='ore_adjustment_dome'
        app_label = 'kqms'

