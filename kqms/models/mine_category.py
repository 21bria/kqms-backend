from django.db import models


class MineCategory(models.Model):
    # id = models.BigAutoField(primary_key=True)
    category = models.CharField(
        max_length=25
    )

    remarks = models.CharField(
        max_length=250,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        blank=True,
        null=True
    )

    updated_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        app_label   = 'kqms'
        db_table    = "mine_category"
        verbose_name = "Mine Category"
        verbose_name_plural = "Mine Categories"

    def __str__(self):
        return self.category
