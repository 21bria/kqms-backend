from django.db import models

class SellingDetailsView(models.Model):
    tgl_hauling    = models.DateField(default=None, null=True, blank=True)
    minggu         = models.IntegerField(default=None, null=True, blank=True)
    bulan          = models.IntegerField(default=None, null=True, blank=True)
    tahun          = models.IntegerField(default=None, null=True, blank=True)
    shift          = models.CharField(max_length=10, default=None, null=True, blank=True)
    sampling_area  = models.CharField(max_length=50, default=None, null=True, blank=True)
    sampling_point = models.CharField(max_length=50, default=None, null=True, blank=True)
    nama_material  = models.CharField(max_length=50, default=None, null=True, blank=True)
    unit_code      = models.CharField(max_length=15, default=None, null=True, blank=True)
    empety_weigth  = models.FloatField(default=None, null=True, blank=True)
    fill_weigth    = models.FloatField(default=None, null=True, blank=True)
    batch          = models.CharField(max_length=25, default=None, null=True, blank=True)
    new_scci_sub   = models.CharField(max_length=25, default=None, null=True, blank=True)
    new_awk_sub    = models.CharField(max_length=25, default=None, null=True, blank=True)
    fill_weigth_f  = models.FloatField(default=None, null=True, blank=True)
    empety_weigth_f= models.FloatField(default=None, null=True, blank=True)
    netto_kg       = models.FloatField(default=None, null=True, blank=True)
    netto_ton      = models.FloatField(default=None, null=True, blank=True)
    tonnage        = models.FloatField(default=None, null=True, blank=True)
    remarks        = models.CharField(max_length=255, default=None, null=True, blank=True)
    id_user        = models.IntegerField(default=None, null=True, blank=True)
    factory_stock  = models.CharField(max_length=150, default=None, null=True, blank=True)
    timbang_isi    = models.DateField(default=None, null=True, blank=True)
    timbang_kosong = models.DateField(default=None, null=True, blank=True)
    no_input       = models.CharField(max_length=15, default=None, null=True, blank=True)
    delivery_order = models.CharField(max_length=25, default=None, null=True, blank=True)
    haulage_code   = models.CharField(max_length=150, default=None, null=True, blank=True)
    left_date      = models.IntegerField(default=None, null=True, blank=True)
    date_wb        = models.DateField(default=None, null=True, blank=True)
    sale_adjust   = models.CharField(max_length=10, default=None, null=True, blank=True)
   
    class Meta:
        managed   = False
        db_table  = 'details_selling'
        app_label = 'kqms'