from django.db import models

class Tanggal(models.Model):
    left_date  = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return self.left_date  

    class Meta:
        db_table  = 'tanggal'
        app_label = 'kqms'
    
    indexes = [
            models.Index(fields=['left_date'])
    ]

       
class TanggalJam(models.Model):
    left_time  = models.IntegerField(default=None, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return self.left_time  

    class Meta:
        db_table  = 'tanggal_jam'
        app_label = 'kqms'
    
    indexes = [
            models.Index(fields=['left_time'])
    ]

       