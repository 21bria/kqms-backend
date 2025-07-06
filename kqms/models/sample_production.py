from django.db import models
import uuid
class SampleProductions(models.Model):
    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tgl_sample      = models.DateField(default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10, default=None, null=True, blank=True)
    id_type_sample  = models.IntegerField(default=None, null=True, blank=True)
    id_method       = models.IntegerField(default=None, null=True, blank=True)
    id_material     = models.IntegerField(default=None, null=True, blank=True)
    sampling_area   = models.BigIntegerField(default=None, null=True, blank=True)
    sampling_point  = models.BigIntegerField(default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15,default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15,default=None, null=True, blank=True)
    batch_code      = models.CharField(max_length=15,default=None, null=True, blank=True)
    increments      = models.IntegerField(default=None, null=True, blank=True)
    fraction        = models.CharField(max_length=15,default=None, null=True, blank=True)
    size            = models.CharField(max_length=15,default=None, null=True, blank=True)
    sample_weight   = models.FloatField(default=None, null=True, blank=True)
    sample_number   = models.CharField(max_length=25,default=None, null=True, blank=True)
    remark          = models.CharField(max_length=255,default=None, null=True, blank=True)
    primer_raw      = models.FloatField(default=None, null=True, blank=True)
    duplicate_raw   = models.FloatField(default=None, null=True, blank=True)
    to_its          = models.TimeField(default=None, null=True, blank=True)
    unit_truck      = models.CharField(max_length=15,default=None, null=True, blank=True)
    kode_batch      = models.CharField(max_length=150,default=None, null=True, blank=True)
    selling_pulp    = models.CharField(max_length=150,default=None, null=True, blank=True)
    sampling_deskripsi = models.CharField(max_length=50,default=None, null=True, blank=True)
    type            = models.CharField(max_length=25,default=None, null=True, blank=True)
    usage_status    = models.CharField(max_length=5,default=None, null=True, blank=True)
    pile_original   = models.BigIntegerField(default=None, null=True, blank=True)
    no_sample       = models.CharField(max_length=15,default=None, null=True, blank=True)
    id_user         = models.IntegerField(default=None, null=True, blank=True)
    sample_dup      = models.CharField(max_length=15,default=None, null=True, blank=True)
    no_input        = models.BigIntegerField(default=None, null=True, blank=True)
    left_date       = models.IntegerField(default=None, null=True, blank=True)
    discharge_area  = models.BigIntegerField(default=None, null=True, blank=True)
    product_code    = models.BigIntegerField(default=None, null=True, blank=True)
    gc_expect       = models.CharField(max_length=10,default=None, null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at      = models.DateTimeField(auto_now_add=True,null=True, blank=True)
 
    class Meta:
        db_table  = 'samples_productions'
        app_label = 'kqms'

        indexes = [
            models.Index(fields=['sample_number']),   # Index for sample_number
            models.Index(fields=['selling_pulp']),
            models.Index(fields=['kode_batch']),
            models.Index(fields=['gc_expect'])
        ]
        
    @classmethod
    def get_samples(cls, sample_from, sample_to):
        return cls.objects.filter(sample_number__gte=sample_from, sample_number__lte=sample_to)
