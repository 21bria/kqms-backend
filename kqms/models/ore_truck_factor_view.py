from django.db import models

class OreTruckFactorView(models.Model):
   
    type_tf      = models.CharField(max_length=150,default=None,null=True,blank=True)
    nama_material = models.CharField(max_length=50,unique=True)
    density      = models.FloatField(default=None,null=True,blank=True)
    bcm          = models.FloatField(default=None,null=True,blank=True)
    ton          = models.FloatField(default=None,null=True,blank=True)
    status       = models.IntegerField(default=None,null=True,blank=True)

    class Meta:
        managed   = False
        db_table  ='list_truck_factors'
        app_label = 'kqms'


