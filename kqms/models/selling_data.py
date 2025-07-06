from django.db import models
import uuid

class SellingProductions(models.Model):
    id                  = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tgl_hauling         = models.DateField(default=None, null=True, blank=True)
    time_hauling        = models.TimeField(default=None, null=True, blank=True)
    shift               = models.CharField(max_length=10, default=None, null=True, blank=True)
    id_material         = models.IntegerField(default=None, null=True, blank=True)
    id_stockpile        = models.IntegerField(default=None, null=True, blank=True)
    id_pile             = models.IntegerField(default=None, null=True, blank=True)
    unit_code	        = models.CharField(max_length=50,default=None, null=True, blank=True)
    empety_weigth       = models.FloatField( default=None, null=True, blank=True)
    fill_weigth         = models.FloatField( default=None, null=True, blank=True)
    netto_weigth        = models.FloatField( default=None, null=True, blank=True)
    qa_control          = models.CharField(max_length=100, default=None, null=True, blank=True)
    batch               = models.CharField(max_length=25, default=None, null=True, blank=True)
    delivery_order      = models.CharField(max_length=25, default=None, null=True, blank=True)
    nota                = models.CharField(max_length=50, default=None, null=True, blank=True)
    id_factory          = models.IntegerField(default=None, null=True, blank=True)
    type_selling        = models.CharField(max_length=50, default=None, null=True, blank=True)
    empety_weigth_f     = models.FloatField( default=None, null=True, blank=True)
    fill_weigth_f       = models.FloatField( default=None, null=True, blank=True)
    netto_weigth_f      = models.FloatField( default=None, null=True, blank=True)
    ore_transport       = models.CharField(max_length=100, default=None, null=True, blank=True)
    id_stock_temp       = models.IntegerField(default=None, null=True, blank=True)
    id_dome_temp        = models.IntegerField(default=None, null=True, blank=True)
    no_input            = models.CharField(max_length=15, default=None, null=True, blank=True)
    remarks             = models.CharField(max_length=255, default=None, null=True, blank=True)
    batch_g             = models.CharField(max_length=25, default=None, null=True, blank=True)
    kode_batch_g        = models.CharField(max_length=150, default=None, null=True, blank=True)
    left_date           = models.IntegerField(default=None, null=True, blank=True)
    new_awk             = models.CharField(max_length=25, default=None, null=True, blank=True)
    new_awk_sub         = models.CharField(max_length=150, default=None, null=True, blank=True)
    new_kode_batch_awk  = models.CharField(max_length=150, default=None, null=True, blank=True)
    new_batch_awk_pulp  = models.CharField(max_length=150, default=None, null=True, blank=True)
    awk_order           = models.CharField(max_length=10, default=None, null=True, blank=True)
    load_code           = models.CharField(max_length=150, default=None, null=True, blank=True)
    haulage_code        = models.CharField(max_length=150, default=None, null=True, blank=True)
    date_wb             = models.DateField(default=None, null=True, blank=True)
    timbang_isi         = models.DateTimeField(default=None, null=True, blank=True)
    timbang_kosong      = models.DateTimeField(default=None, null=True, blank=True)
    id_user             = models.IntegerField(default=None, null=True, blank=True)
    sale_adjust         = models.CharField(max_length=5,default=None, null=True, blank=True)
    sale_dome           = models.CharField(max_length=10,default=None, null=True, blank=True)
    created_at          = models.DateTimeField(auto_now_add=True)
    updated_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table   = 'ore_sellings'
        app_label  = 'kqms'

    indexes = [
            models.Index(fields=['delivery_order']),
            models.Index(fields=['new_kode_batch_awk']),
            models.Index(fields=['new_batch_awk_pulp']),
            models.Index(fields=['sale_adjust'])
    ]


