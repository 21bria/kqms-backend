from django.db import models

class sellingOfficialView(models.Model):
    type_selling     = models.CharField(max_length=50, default=None, null=True, blank=True)
    code_surveyor    = models.CharField(max_length=50, default=None, null=True, blank=True)
    name_surveyor    = models.CharField(max_length=150, default=None, null=True, blank=True)
    discharging_port = models.CharField(max_length=150, default=None, null=True, blank=True)
    so_number        = models.CharField(max_length=150,default=None, null=True, blank=True)
    product_code     = models.CharField(max_length=150,default=None, null=True, blank=True)
    tonnage          = models.FloatField(default=None, null=True, blank=True)
    ni               = models.FloatField(default=None, null=True, blank=True)
    co	             = models.FloatField(default=None, null=True, blank=True)
    al2o3	         = models.FloatField(default=None, null=True, blank=True)
    cao	             = models.FloatField(default=None, null=True, blank=True)
    cr2o3	         = models.FloatField(default=None, null=True, blank=True)
    fe	             = models.FloatField(default=None, null=True, blank=True)
    mgo	             = models.FloatField(default=None, null=True, blank=True)
    sio2	         = models.FloatField(default=None, null=True, blank=True)
    mno	             = models.FloatField(default=None, null=True, blank=True)
    mc	             = models.FloatField(default=None, null=True, blank=True)
    start_date       = models.DateField(default=None, null=True, blank=True)
    end_date         = models.DateField(default=None, null=True, blank=True)

    class Meta:
        managed    = False
        db_table   = 'sellings_official_view'
        app_label  = 'kqms'
