# Generated by Django 4.2 on 2025-07-12 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kqms', '0013_menu_category_title_menu_is_category'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='mineproductions',
            index=models.Index(fields=['date_production', 'hauler', 'time_loading', 'id_material', 'dome_id', 'sources_area', 'loading_point', 'dumping_point'], name='idx_mineprod_dedupe'),
        ),
    ]
