# Generated by Django 3.2 on 2022-05-27 06:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='specifications',
            field=models.ManyToManyField(related_name='asset_specification', through='assets.AssetSpecification', to='assets.Specification'),
        ),
    ]
