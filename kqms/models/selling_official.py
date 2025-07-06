from django.db import models

class SellingOfficial(models.Model):
    id_surveyor      = models.IntegerField(default=None, null=True, blank=True)
    type_selling     = models.CharField(max_length=50, default=None, null=True, blank=True)
    tonnage          = models.FloatField(default=None, null=True, blank=True)
    id_factory       = models.IntegerField(default=None, null=True, blank=True)
    so_number        = models.CharField(max_length=150,default=None, null=True, blank=True)
    product_code     = models.CharField(max_length=150,default=None, null=True, blank=True)
    ni               = models.FloatField(default=None, null=True, blank=True)
    co	             = models.FloatField(default=None, null=True, blank=True)
    al2o3	         = models.FloatField(default=None, null=True, blank=True)
    cao	             = models.FloatField(default=None, null=True, blank=True)
    cr2o3	         = models.FloatField(default=None, null=True, blank=True)
    fe	             = models.FloatField(default=None, null=True, blank=True)
    mgo	             = models.FloatField(default=None, null=True, blank=True)
    sio2	         = models.FloatField(default=None, null=True, blank=True)
    mno	             = models.FloatField(default=None, null=True, blank=True)
    mc	             = models.FloatField(default=None, null=True, blank=True)
    start_date       = models.DateField(default=None, null=True, blank=True)
    end_date         = models.DateField(default=None, null=True, blank=True)
    check_duplicated = models.CharField(max_length=150, default=None, null=True, blank=True)
    description      = models.CharField(max_length=250, default=None, null=True, blank=True)
    id_user          = models.IntegerField(default=None, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'ore_sellings_official'
        app_label  = 'kqms'

    indexes = [
        models.Index(fields=['type_selling']),
        models.Index(fields=['product_code'])
    ]

class SellingSurveyor(models.Model):
    code_surveyor = models.CharField(max_length=50, default=None, null=True, blank=True)
    name_surveyor = models.CharField(max_length=150, default=None, null=True, blank=True)
    description   = models.CharField(max_length=150, default=None, null=True, blank=True)
    start_date    = models.DateField(default=None, null=True, blank=True)
    end_date      = models.DateField(default=None, null=True, blank=True)
    
    class Meta:
        db_table   = 'ore_sellings_surveyor'
        app_label  = 'kqms'
