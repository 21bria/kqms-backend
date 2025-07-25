# Generated by Django 4.2 on 2025-06-23 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kqms', '0003_batchstatusview_detailsmral_detailsroa_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='SellingCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('product_code', models.CharField(max_length=50, unique=True)),
                ('description', models.CharField(blank=True, default=None, max_length=250, null=True)),
                ('type', models.CharField(blank=True, default=None, max_length=10, null=True)),
                ('active', models.IntegerField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'ore_selling_code_product',
            },
        ),
    ]
