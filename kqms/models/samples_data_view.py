from django.db import models

class SamplesView(models.Model):
    tgl_sample     = models.DateField(default=None, null=True, blank=True)
    minggu         = models.IntegerField(default=None, null=True, blank=True)
    bulan          = models.IntegerField(default=None, null=True, blank=True)
    tahun          = models.IntegerField(default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_sample    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method  = models.CharField(max_length=50, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_area  = models.CharField(max_length=200, default=None, null=True, blank=True)
    sampling_point = models.CharField(max_length=100, default=None, null=True, blank=True)
    area_sampling  = models.CharField(max_length=50, default=None, null=True, blank=True)
    factory_stock  = models.CharField(max_length=150, default=None, null=True, blank=True)
    point_sampling = models.CharField(max_length=50, default=None, null=True, blank=True)
    product_code   = models.CharField(max_length=50, default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=15, default=None, null=True, blank=True)
    increments     = models.IntegerField(default=None, null=True, blank=True)
    size           = models.CharField(max_length=15, default=None, null=True, blank=True)
    sample_weight  = models.FloatField(default=None, null=True, blank=True)
    sample_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    remark         = models.CharField(max_length=255, default=None, null=True, blank=True)
    primer_raw     = models.FloatField(default=None, null=True, blank=True)
    duplicate_raw  = models.FloatField(default=None, null=True, blank=True)
    to_its         = models.TimeField(default=None, null=True, blank=True)
    sampling_deskripsi = models.CharField(max_length=50, default=None, null=True, blank=True)
    kode_batch     = models.CharField(max_length=150, default=None, null=True, blank=True)
    no_input       = models.BigIntegerField(default=None, null=True, blank=True)
    gc_expect      = models.CharField(max_length=10, default=None, null=True, blank=True)
    no_sample      = models.CharField(max_length=15, default=None, null=True, blank=True)
    username       = models.CharField(max_length=50,default=None, null=True, blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed   = False
        db_table  = 'sample_production_view'
        app_label = 'kqms'

class samplesNoOrders(models.Model):
    tgl_sample     = models.DateField(default=None, null=True, blank=True)
    minggu         = models.IntegerField(default=None, null=True, blank=True)
    bulan          = models.IntegerField(default=None, null=True, blank=True)
    tahun          = models.IntegerField(default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_sample    = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method  = models.CharField(max_length=50, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_area  = models.CharField(max_length=200, default=None, null=True, blank=True)
    sampling_point = models.CharField(max_length=100, default=None, null=True, blank=True)
    sampling_deskripsi = models.CharField(max_length=50, default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=15, default=None, null=True, blank=True)
    increments     = models.IntegerField(default=None, null=True, blank=True)
    size           = models.CharField(max_length=15, default=None, null=True, blank=True)
    sample_weight  = models.FloatField(default=None, null=True, blank=True)
    sample_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    remark         = models.CharField(max_length=255, default=None, null=True, blank=True)
    primer_raw     = models.FloatField(default=None, null=True, blank=True)
    duplicate_raw  = models.FloatField(default=None, null=True, blank=True)
    to_its         = models.TimeField(default=None, null=True, blank=True)
    waybill_number = models.CharField(max_length=25, default=None, null=True, blank=True)

    class Meta:
        managed   = False
        db_table  = 'samples_not_orders'
        app_label = 'kqms' 

class samplesNaPds(models.Model):
    tgl_sample     = models.DateField(default=None, null=True, blank=True)
    minggu         = models.IntegerField(default=None, null=True, blank=True)
    bulan          = models.IntegerField(default=None, null=True, blank=True)
    tahun          = models.IntegerField(default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    type_sample    = models.CharField(max_length=25, default=None, null=True, blank=True)
    units          = models.CharField(max_length=25, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_area  = models.CharField(max_length=200, default=None, null=True, blank=True)
    sampling_point = models.CharField(max_length=100, default=None, null=True, blank=True)
    batch_code     = models.CharField(max_length=15, default=None, null=True, blank=True)
    increments     = models.IntegerField(default=None, null=True, blank=True)
    size           = models.CharField(max_length=15, default=None, null=True, blank=True)
    sample_weight  = models.FloatField(default=None, null=True, blank=True)
    sample_number  = models.CharField(max_length=25, default=None, null=True, blank=True)
    remark         = models.CharField(max_length=255, default=None, null=True, blank=True)
    primer_raw     = models.FloatField(default=None, null=True, blank=True)
    duplicate_raw  = models.FloatField(default=None, null=True, blank=True)
    to_its         = models.TimeField(default=None, null=True, blank=True)
    kode_batch     = models.CharField(max_length=15, default=None, null=True, blank=True)

    class Meta:
        managed   = False
        db_table  = 'sample_pds_na'
        app_label = 'kqms'        