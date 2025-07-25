# Generated by Django 4.2 on 2025-06-21 13:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('kqms', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Menu',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('section_title', models.CharField(blank=True, help_text='Tulis jika ini adalah header kategori menu (bukan menu item).', max_length=100, null=True)),
                ('label', models.CharField(max_length=100)),
                ('icon_svg', models.TextField(blank=True, help_text='Paste SVG markup di sini, contoh: <svg ...>...</svg>', null=True)),
                ('key', models.CharField(max_length=50, unique=True)),
                ('url', models.CharField(blank=True, help_text='Boleh kosong untuk dropdown', max_length=200, null=True)),
                ('order', models.PositiveIntegerField(default=0)),
                ('groups', models.ManyToManyField(blank=True, help_text='Kosongkan jika menu ini bisa dilihat semua user.', to='auth.group')),
                ('parent', models.ForeignKey(blank=True, help_text='Hubungkan ke menu induk jika ini submenu.', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='kqms.menu')),
                ('permission', models.ForeignKey(blank=True, help_text='Opsional. Hanya tampil jika user memiliki permission ini.', null=True, on_delete=django.db.models.deletion.SET_NULL, to='auth.permission')),
            ],
            options={
                'ordering': ['order'],
            },
        ),
    ]
