# Generated by Django 3.2 on 2022-09-29 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0011_location_is_deleted'),
        ('assets', '0008_remove_asset_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='dashboard.location'),
        ),
    ]
