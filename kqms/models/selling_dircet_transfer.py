from django.db import models

class SellingDirectTransferView(models.Model):
    date_hauling    = models.DateField(default=None, null=True, blank=True)
    dome            = models.CharField(max_length=50, default=None, null=True, blank=True)
    stockpile       = models.CharField(max_length=50, default=None, null=True, blank=True)
    barge_code      = models.CharField(max_length=25, default=None, null=True, blank=True)
    material        = models.CharField(max_length=50, default=None, null=True, blank=True)
    direct          = models.CharField(max_length=50, default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    status_transfer = models.CharField(max_length=255, default=None, null=True, blank=True)
    
    class Meta:
        managed   = False
        db_table  = 'selling_direct_transfer'
        app_label = 'kqms'