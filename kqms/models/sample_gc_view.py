from django.db import models

class GradeExpectationsMral(models.Model):
    tgl_production  = models.DateField(default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10,default=None, null=True, blank=True)
    tgl             = models.CharField(max_length=8,default=None, null=True, blank=True)
    prospect_area   = models.CharField(max_length=50, default=None, null=True, blank=True)
    mine_block      = models.CharField(max_length=50, default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15,default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15,default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=20,default=None, null=True, blank=True)
    ore_class       = models.CharField(max_length=15,default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    batch_code      = models.CharField(max_length=15,default=None, null=True, blank=True)
    grade_control   = models.CharField(max_length=50,default=None, null=True, blank=True)
    sample_number   = models.CharField(max_length=25,default=None, null=True, blank=True)
    ex_ni           = models.FloatField(default=None, null=True, blank=True)
    ni_act          = models.FloatField(default=None, null=True, blank=True)
    ni_diff         = models.CharField(max_length=25,default=None, null=True, blank=True)
    ni_abs          = models.FloatField(default=None, null=True, blank=True)
    avg_ex          = models.FloatField(default=None, null=True, blank=True)
    avg_act         = models.FloatField(default=None, null=True, blank=True)
 
    class Meta:
        managed   = False
        db_table  = 'grade_expectations_mral'
        app_label = 'kqms'

class GradeExpectationsRoa(models.Model):
    tgl_production  = models.DateField(default=None, null=True, blank=True)
    shift           = models.CharField(max_length=10,default=None, null=True, blank=True)
    tgl             = models.CharField(max_length=8,default=None, null=True, blank=True)
    prospect_area   = models.CharField(max_length=50, default=None, null=True, blank=True)
    mine_block      = models.CharField(max_length=50, default=None, null=True, blank=True)
    from_rl         = models.CharField(max_length=15,default=None, null=True, blank=True)
    to_rl           = models.CharField(max_length=15,default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=20,default=None, null=True, blank=True)
    ore_class       = models.CharField(max_length=15,default=None, null=True, blank=True)
    ritase          = models.IntegerField(default=None, null=True, blank=True)
    tonnage         = models.FloatField(default=None, null=True, blank=True)
    batch_code      = models.CharField(max_length=15,default=None, null=True, blank=True)
    grade_control   = models.CharField(max_length=50,default=None, null=True, blank=True)
    sample_number   = models.CharField(max_length=25,default=None, null=True, blank=True)
    ex_ni           = models.FloatField(default=None, null=True, blank=True)
    ni_act          = models.FloatField(default=None, null=True, blank=True)
    ni_diff         = models.CharField(max_length=25,default=None, null=True, blank=True)
    ni_abs          = models.FloatField(default=None, null=True, blank=True)
    avg_ex          = models.FloatField(default=None, null=True, blank=True)
    avg_act         = models.FloatField(default=None, null=True, blank=True)
 
    class Meta:
        managed   = False
        db_table  = 'grade_expectations_roa'
        app_label = 'kqms'

class GradeControlSamples(models.Model):
    tgl_sample      = models.DateField(default=None, null=True, blank=True)
    tgl_deliver     = models.DateField(default=None, null=True, blank=True)
    sampling_area   = models.CharField(max_length=50, default=None, null=True, blank=True)
    sample_id       = models.CharField(max_length=25,default=None, null=True, blank=True)
    type_sample     = models.CharField(max_length=25, default=None, null=True, blank=True)
    sample_method   = models.CharField(max_length=25,default=None, null=True, blank=True)
    nama_material   = models.CharField(max_length=20,default=None, null=True, blank=True)
    job_number      = models.CharField(max_length=25,default=None, null=True, blank=True)
    release_date    = models.DateField(default=None, null=True, blank=True)
    ni              = models.FloatField(default=None, null=True, blank=True)
    co              = models.FloatField(default=None, null=True, blank=True)
    fe2o3           = models.FloatField(default=None, null=True, blank=True)
    fe              = models.FloatField(default=None, null=True, blank=True)
    mgo             = models.FloatField(default=None, null=True, blank=True)
    sio2            = models.FloatField(default=None, null=True, blank=True)
    sm              = models.FloatField(default=None, null=True, blank=True)
 
    class Meta:
        managed   = False
        db_table  = 'samples_gc'
        app_label = 'kqms'