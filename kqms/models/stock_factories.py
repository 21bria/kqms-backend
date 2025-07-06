from django.db import models
class StockFactories(models.Model):
    factory_stock  = models.CharField(max_length=150, unique=True)
    capasity       = models.FloatField(null=True,blank=True)
    description    = models.CharField(max_length=255, default=None, null=True, blank=True)
    status         = models.IntegerField(default=None, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.factory_stock 

    class Meta:
        db_table  = 'stock_factories'
        app_label = 'kqms'
