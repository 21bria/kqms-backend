from django.db import models
import uuid

class planProductions(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_plan  = models.DateField(default=None, null=True, blank=True)
    category   = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources    = models.CharField(max_length=50, default=None, null=True, blank=True)
    vendors    = models.CharField(max_length=15, default=None, null=True, blank=True)
    topsoil    = models.FloatField(default=None, null=True, blank=True)
    ob         = models.FloatField(default=None, null=True, blank=True)
    lglo       = models.FloatField(default=None, null=True, blank=True)
    mglo       = models.FloatField(default=None, null=True, blank=True)
    hglo       = models.FloatField(default=None, null=True, blank=True)
    waste      = models.FloatField(default=None, null=True, blank=True)
    mws        = models.FloatField(default=None, null=True, blank=True)
    lgso       = models.FloatField(default=None, null=True, blank=True)
    uglo       = models.FloatField(default=None, null=True, blank=True)
    mgso       = models.FloatField(default=None, null=True, blank=True)
    hgso       = models.FloatField(default=None, null=True, blank=True)
    quarry     = models.FloatField(default=None, null=True, blank=True)
    ballast    = models.FloatField(default=None, null=True, blank=True)
    biomass    = models.FloatField(default=None, null=True, blank=True)
    ref_plan   = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id    = models.CharField(max_length=255, default=None, null=True, blank=True)
    id_user    = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  = 'plan_productions'
        app_label = 'kqms'

