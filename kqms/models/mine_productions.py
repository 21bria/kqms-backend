from django.db import models
import uuid

class mineProductions(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_production = models.DateField(default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources_area    = models.BigIntegerField(default=None, null=True, blank=True)
    loading_point   = models.BigIntegerField(default=None, null=True, blank=True)
    dumping_point   = models.BigIntegerField(default=None, null=True, blank=True)
    dome_id         = models.BigIntegerField(default=None, null=True, blank=True)
    distance        = models.CharField(max_length=250, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    time_dumping    = models.CharField(max_length=25,default=None, null=True, blank=True)
    time_loading    = models.TimeField(default=None, null=True, blank=True)
    left_loading    = models.CharField(max_length=2,default=None, null=True, blank=True)
    block_id        = models.CharField(max_length=250,default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_material     = models.IntegerField(default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_materials   = models.CharField(max_length=150, default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'productions_mines'
        app_label  = 'kqms'
        indexes = [
        models.Index(
            fields=[
                'date_production', 'hauler', 'time_loading',
                'id_material', 'dome_id', 'sources_area',
                'loading_point', 'dumping_point'
            ],
            name='idx_mineprod_dedupe'
        )
    ]


# Mine Productions Quick
class mineQuickProductions(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_production = models.DateField(default=None, null=True, blank=True)
    vendors         = models.CharField(max_length=25, default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    loader          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler          = models.CharField(max_length=25, default=None, null=True, blank=True)
    hauler_class    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sources         = models.IntegerField(default=None, null=True, blank=True)
    loading_point   = models.IntegerField(default=None, null=True, blank=True)
    dumping_point   = models.IntegerField(default=None, null=True, blank=True)
    dome_id         = models.IntegerField(default=None, null=True, blank=True)
    distance        = models.CharField(max_length=250, default=None, null=True, blank=True)
    category_mine   = models.CharField(max_length=25, default=None, null=True, blank=True)
    block_id        = models.BigIntegerField(default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15, default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15, default=None, null=True, blank=True)
    id_material     = models.IntegerField(default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    bcm             = models.FloatField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    time_loading    = models.CharField(max_length=2,default=None, null=True, blank=True)
    remarks         = models.TextField(default=None, null=True, blank=True)
    hauler_type     = models.CharField(max_length=15, default=None, null=True, blank=True)
    ref_materials   = models.CharField(max_length=150, default=None, null=True, blank=True)
    ref_plan_truck  = models.CharField(max_length=150, default=None, null=True, blank=True)
    task_id         = models.CharField(max_length=255, default=None, null=True, blank=True)
    no_production   = models.CharField(max_length=25, default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'productions_quick_mines'
        app_label  = 'kqms'
