from django.db import models

class sellingPlanView(models.Model):
    plan_date        = models.DateField(default=None, null=True, blank=True)
    type_ore         = models.CharField(max_length=10, default=None, null=True, blank=True)
    tonnage_plan     = models.FloatField(default=None, null=True, blank=True)
    ni_plan          = models.FloatField(default=None, null=True, blank=True)
    total            = models.FloatField(default=None, null=True, blank=True)
    achiev	         = models.FloatField(default=None, null=True, blank=True)
    total_wmt	     = models.FloatField(default=None, null=True, blank=True)

    class Meta:
        managed    = False
        db_table   = 'selling_plan_view'
        app_label  = 'kqms'
