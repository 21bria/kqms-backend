from django.db import models


class SampleCrmCertified(models.Model):
    oreas_name = models.CharField(
        max_length=25,
        blank=True,
        null=True
    )
    ni = models.FloatField(blank=True, null=True)
    co = models.FloatField(blank=True, null=True)
    al2o3 = models.FloatField(blank=True, null=True)
    cao = models.FloatField(blank=True, null=True)
    cr2o3 = models.FloatField(blank=True, null=True)
    fe2o3 = models.FloatField(blank=True, null=True)
    fe = models.FloatField(blank=True, null=True)
    k2o = models.FloatField(blank=True, null=True)
    mgo = models.FloatField(blank=True, null=True)
    mno = models.FloatField(blank=True, null=True)
    na2o = models.FloatField(blank=True, null=True)
    p2o5 = models.FloatField(blank=True, null=True)
    p = models.FloatField(blank=True, null=True)
    sio2 = models.FloatField(blank=True, null=True)
    tio2 = models.FloatField(blank=True, null=True)
    s = models.FloatField(blank=True, null=True)
    cu = models.FloatField(blank=True, null=True)
    zn = models.FloatField(blank=True, null=True)
    ci = models.FloatField(blank=True, null=True)
    so3 = models.FloatField(blank=True, null=True)
    loi = models.FloatField(blank=True, null=True)
    sm = models.FloatField(blank=True, null=True)
    al203 = models.FloatField(blank=True, null=True)  # sesuai nama kolom DB (tanpa typo)

    class Meta:
        app_label   = 'kqms'
        db_table    = "sample_crm_certified"
        verbose_name = "Sample CRM Certified"
        verbose_name_plural = "Sample CRM Certified"

    def __str__(self):
        return self.oreas_name or f"CRM {self.id}"
