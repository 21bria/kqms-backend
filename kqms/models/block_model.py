from django.db import models
class Block(models.Model):
    mine_block  = models.CharField(max_length=50, unique=True)
    keterangan  = models.CharField(max_length=250, default=None, null=True, blank=True)
    status      = models.IntegerField(default=None, null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.mine_block

    class Meta:
        db_table  = 'blocks'
        app_label = 'kqms'




