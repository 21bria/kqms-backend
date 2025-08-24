from django.db import models

class bargingAdjust(models.Model):
    date_arrival    = models.DateField(default=None,null=True,blank=True)
    date_departure  = models.DateField(default=None,null=True,blank=True)
    jetty_departure = models.CharField(max_length=25,default=None,null=True,blank=True)
    code_lot        = models.CharField(max_length=25,default=None,null=True,blank=True)
    ritase_ori      = models.IntegerField(default=None,null=True,blank=True)
    tonnage_ori     = models.FloatField(default=None,null=True,blank=True)
    tonnage_adjust  = models.FloatField(default=None,null=True,blank=True)
    status          = models.CharField(max_length=15,default=None,null=True,blank=True)
    remarks         = models.TextField(default=None,null=True,blank=True)
    id_user         = models.IntegerField(default=None,null=True,blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='ore_sellings_barging_adjust'
        app_label = 'kqms'

