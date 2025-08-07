from django.db import models
import uuid

class BlendingResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blend_code = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    target_tonase = models.FloatField()
    target_ni = models.FloatField()
    final_ni = models.FloatField()
    final_fe = models.FloatField(null=True, blank=True)
    final_co = models.FloatField(null=True, blank=True)
    final_mgo = models.FloatField(null=True, blank=True)
    final_al2o3 = models.FloatField(null=True, blank=True)
    final_sio2 = models.FloatField(null=True, blank=True)
    final_sm = models.FloatField(null=True, blank=True)
    total_used = models.FloatField()
    id_user = models.IntegerField(default=None, null=True, blank=True)
    
    class Meta:
        db_table   = 'ore_sellings_blending'
        app_label  = 'kqms'


class BlendingDetail(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    blending = models.ForeignKey(BlendingResult, on_delete=models.CASCADE, related_name="details")
    pile_id = models.CharField(max_length=50)
    used_tonase = models.FloatField()
    ni = models.FloatField()
    fe = models.FloatField()
    co = models.FloatField(null=True, blank=True)
    mgo = models.FloatField(null=True, blank=True)
    al2o3 = models.FloatField(null=True, blank=True)
    sio2 = models.FloatField(null=True, blank=True)
    sm = models.FloatField(null=True, blank=True)
    balance = models.FloatField()

    class Meta:
        db_table   = 'ore_sellings_blending_detail'
        app_label  = 'kqms'
