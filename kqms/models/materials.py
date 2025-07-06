from django.db import models

class Material(models.Model):
    nama_material = models.CharField(max_length=50, unique=True)
    keterangan    = models.CharField(max_length=250, default=None, null=True, blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nama_material  

    class Meta:
        db_table  = 'materials'
        app_label = 'kqms'
    
    indexes = [
            models.Index(fields=['nama_material'])
    ]

       