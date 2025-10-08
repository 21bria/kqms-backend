from django.db import models

class MineReserve(models.Model):
    ORE_TYPE_CHOICES = [
        ('ALL', 'All Type'),
        ('LIM', 'Limonite'),
        ('SAP', 'Saprolite'),
    ]
    id_reserve = models.AutoField(primary_key=True)
    block_model = models.CharField(max_length=100, blank=True, null=True)  # nama model blok geologi
    pit_name = models.CharField(max_length=100, blank=True, null=True)     # nama pit/lokasi tambang
    domain = models.CharField(max_length=50, blank=True, null=True)        # domain geologi (limonite/saprolite)
    
    ore_type = models.CharField(
        max_length=20,
        choices=ORE_TYPE_CHOICES,
        default='ALL',   # kalau tidak diisi, otomatis jadi 'ALL'
        blank=True,
        null=True,
    )

    # Tonase dan grade
    tonnage = models.FloatField(default=0.0)     # total tonase cadangan
    ni_grade = models.FloatField(default=0.0)    # kandungan Ni (%)
    fe_grade = models.FloatField(default=0.0)    # kandungan Fe (%)
    co_grade = models.FloatField(default=0.0)    # opsional, cobalt
    mgo_grade = models.FloatField(default=0.0)
    sio2_grade = models.FloatField(default=0.0)

    # Informasi ekonomi (opsional)
    strip_ratio = models.FloatField(default=0.0)  # waste/ore ratio
    cutoff_grade = models.FloatField(default=1.0) # batas kadar ekonomis

    # Relasi & metadata
    date_estimated = models.DateField()          # tanggal estimasi
    estimated_by = models.CharField(max_length=100)  # nama/geologist estimator
    remark = models.TextField(blank=True, null=True) # catatan tambahan

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'kqms'
        db_table  = 'mine_reserve'
        ordering  = ['-date_estimated']
