from django.db import models

class domeStatusClose(models.Model):
    id_dome       = models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_dome  = models.FloatField(default=None,null=True,blank=True)
    status_dome   = models.CharField(max_length=15,default=None,null=True,blank=True)
    description   = models.TextField(default=None,null=True,blank=True)
    cek_duplicated= models.CharField(max_length=255,default=None,null=True,blank=True)
    id_user       = models.IntegerField(default=None,null=True,blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='status_dome'
        app_label = 'kqms'

class domeStatusFinish(models.Model):
    id_dome       = models.BigIntegerField(default=None,null=True,blank=True)
    tonnage_dome  = models.FloatField(default=None,null=True,blank=True)
    status_dome   = models.CharField(max_length=15,default=None,null=True,blank=True)
    description   = models.TextField(default=None,null=True,blank=True)
    cek_duplicated= models.CharField(max_length=255,default=None,null=True,blank=True)
    id_user       = models.IntegerField(default=None,null=True,blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table  ='status_dome_finish'
        app_label = 'kqms'
