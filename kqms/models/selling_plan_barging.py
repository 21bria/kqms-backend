from django.db import models
import uuid

class SellingPlanBarging(models.Model):
    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_date        = models.DateField(default=None, null=True, blank=True)
    type_ore         = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_selling     = models.CharField(max_length=10, default=None, null=True, blank=True)
    tonnage_plan     = models.FloatField(default=None, null=True, blank=True)
    ni_plan          = models.FloatField(default=None, null=True, blank=True)
    co_plan          = models.FloatField(default=None, null=True, blank=True)
    fe_plan	         = models.FloatField(default=None, null=True, blank=True)
    sio2_plan	     = models.FloatField(default=None, null=True, blank=True)
    al2o3_plan	     = models.FloatField(default=None, null=True, blank=True)
    mgo_plan	     = models.FloatField(default=None, null=True, blank=True)
    sm_plan	         = models.FloatField(default=None, null=True, blank=True)
    check_duplicated = models.CharField(max_length=150, default=None, null=True, blank=True)
    description      = models.CharField(max_length=250, default=None, null=True, blank=True)
    id_user          = models.IntegerField(default=None, null=True, blank=True)
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'ore_sellings_plan_barging'
        app_label  = 'kqms'
    
    indexes = [
        models.Index(fields=['plan_date']),
        models.Index(fields=['type_ore']),
        models.Index(fields=['type_selling'])
    ]

class BargingPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    plan_date = models.DateField(default=None, null=True, blank=True)
    tugboat_name = models.CharField(max_length=150, null=True, blank=True)
    barge_name   = models.CharField(max_length=150, null=True, blank=True)

    # nilai tonase per hari (isi cell Excel)
    tonnage_plan = models.FloatField(null=True, blank=True)

    # nomor plan (misal urutan plan atau referensi sheet)
    no_plan = models.IntegerField(null=True, blank=True)

    # gabungan unik (buat mencegah duplikat saat import)
    check_duplicated = models.CharField(max_length=200, null=True, blank=True)

    # tambahan keterangan di file, misal “Emerald 36 - BG. Finacia 57”
    description = models.CharField(max_length=250, null=True, blank=True)

    # user input
    id_user = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table  = 'ore_barging_plan'
        app_label = 'kqms'
        indexes = [
            models.Index(fields=['plan_date']),
            models.Index(fields=['barge_name']),
        ]

    def __str__(self):
        return f"{self.plan_date} - {self.barge_name or 'No Barge'}"