from django.db import models

class OreTruckFactor(models.Model):
   
    type_tf      = models.CharField(max_length=150,default=None,null=True,blank=True)
    reference_tf = models.CharField(max_length=150,unique=True)
    material     = models.IntegerField(default=None,null=True,blank=True)
    density      = models.FloatField(default=None,null=True,blank=True)
    bcm          = models.FloatField(default=None,null=True,blank=True)
    ton          = models.FloatField(default=None,null=True,blank=True)
    status       = models.IntegerField(default=None,null=True,blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now_add=True)

    
    class Meta:
        db_table  ='ore_truck_factors'
        app_label = 'kqms'

class OreTruckFactorAdjust(models.Model):
    unit_truck   = models.CharField(max_length=25,default=None,null=True,blank=True)
    sources      = models.IntegerField(default=None,null=True,blank=True)
    material     = models.IntegerField(default=None,null=True,blank=True)
    date_start   = models.DateField(default=None,null=True,blank=True)
    date_end     = models.DateField(default=None,null=True,blank=True)
    ton          = models.FloatField(default=None,null=True,blank=True)
    reference_tf = models.CharField(max_length=150)
    status       = models.CharField(max_length=50)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now_add=True)


    class Meta:
        db_table  ='ore_truck_factors_adjust'
        app_label = 'kqms'
