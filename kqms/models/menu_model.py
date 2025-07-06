from django.db import models
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

class Menu(models.Model):

    section_title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Tulis jika ini adalah header kategori menu (bukan menu item)."
    )
    label = models.CharField(max_length=100)
    icon_svg = models.TextField(
        blank=True,
        null=True,
        help_text="Paste SVG markup di sini, contoh: <svg ...>...</svg>"
    )
    key = models.CharField(max_length=50, unique=True)
    url = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Boleh kosong untuk dropdown"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Hubungkan ke menu induk jika ini submenu."
    )
    order = models.PositiveIntegerField(default=0)
   
    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text="Kosongkan jika menu ini bisa dilihat semua user."
    )
    
    permission = models.ForeignKey(
        Permission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Opsional. Hanya tampil jika user memiliki permission ini."
    )

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.label
    