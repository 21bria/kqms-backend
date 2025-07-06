from django.db import models
import uuid

class SellingPlan(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_date        = models.DateField(default=None, null=True, blank=True)
    type_ore         = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_selling     = models.CharField(max_length=10, default=None, null=True, blank=True)
    tonnage_plan     = models.FloatField(default=None, null=True, blank=True)
    ni_plan          = models.FloatField(default=None, null=True, blank=True)
    ni_buyer         = models.FloatField(default=None, null=True, blank=True)
    ni_surveyor	     = models.FloatField(default=None, null=True, blank=True)
    check_duplicated = models.CharField(max_length=150, default=None, null=True, blank=True)
    description      = models.CharField(max_length=250, default=None, null=True, blank=True)
    left_date        = models.IntegerField(default=None, null=True, blank=True)
    id_user          = models.IntegerField(default=None, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'ore_sellings_plan'
        app_label  = 'kqms'
    
    indexes = [
        models.Index(fields=['plan_date']),
        models.Index(fields=['type_selling'])
    ]
