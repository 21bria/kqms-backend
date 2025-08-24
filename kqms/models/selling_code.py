from django.db import models

class SellingCode(models.Model):
    product_code = models.CharField(max_length=50, unique=True)
    description   = models.CharField(max_length=250, default=None, null=True, blank=True)
    type          = models.CharField(max_length=10, default=None, null=True, blank=True)
    active        = models.IntegerField(default=None, null=True, blank=True)
    truck_factors = models.FloatField(default=None, null=True, blank=True)
    sublot_close  = models.CharField(max_length=10, default=None, null=True, blank=True)
    group_close   = models.IntegerField(default=None, null=True, blank=True)
    ritase_max    = models.IntegerField(default=None, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True) 
    updated_at    = models.DateTimeField(auto_now_add=True) 

    def __str__(self):
        return self.product_code

    class Meta:
        db_table  = 'ore_selling_code_product'
        app_label = 'kqms'
    
    indexes = [
            models.Index(fields=['product_code']),
            models.Index(fields=['type'])
    ]




