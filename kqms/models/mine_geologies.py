from django.db import models

class MineGeologies(models.Model):
    mg_code     = models.CharField(max_length=15, unique=True)
    mg_name     = models.CharField(max_length=100,default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.mg_code
    
    class Meta:
        db_table  = 'mine_geologies'
        app_label = 'kqms'
