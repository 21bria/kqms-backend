from django.db import models
class Vendors(models.Model):
    vendor_name = models.CharField(max_length=50, unique=True)
    code        = models.CharField(max_length=15, default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    description = models.CharField(max_length=255, default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    class Meta:
        db_table  = 'vendors'
        app_label = 'kqms'


