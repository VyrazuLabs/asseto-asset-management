# Generated by Django 3.2 on 2022-09-26 11:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_remove_productcategory_product_type'),
        ('assets', '0004_asset_deleted'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='description',
            field=models.CharField(blank=True, max_length=999, null=True),
        ),
        migrations.AddField(
            model_name='asset',
            name='location',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='dashboard.location'),
        ),
        migrations.AlterField(
            model_name='asset',
            name='specifications',
            field=models.ManyToManyField(blank=True, related_name='asset_specification', through='assets.AssetSpecification', to='assets.Specification'),
        ),
    ]