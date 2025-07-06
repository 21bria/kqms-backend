from django.db import models

class MineUnits(models.Model):
    unit_code   = models.CharField(max_length=25, unique=True)
    unit_model  = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_type   = models.CharField(max_length=50, default=None, null=True, blank=True)
    id_category = models.IntegerField(default=None, null=True, blank=True)
    id_vendor   = models.IntegerField(default=None, null=True, blank=True)
    supports    = models.CharField(max_length=50, default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    description = models.CharField(max_length=255, default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.unit_code

    class Meta:
        db_table  = 'mine_units'
        app_label = 'kqms'

class mineUnitsView(models.Model):
    unit_code   = models.CharField(max_length=25, default=None, null=True, blank=True)
    unit_model  = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_type   = models.CharField(max_length=50, default=None, null=True, blank=True)
    supports    = models.CharField(max_length=25, default=None, null=True, blank=True)
    category    = models.CharField(max_length=50, default=None, null=True, blank=True)
    vendor_name = models.CharField(max_length=25, default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    
    class Meta:
        managed     = False
        db_table    = 'list_mine_units'
        app_label   = 'kqms'

class unitsCategories(models.Model):
    category  = models.CharField(max_length=50, default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'units_categories'
        app_label = 'kqms'

