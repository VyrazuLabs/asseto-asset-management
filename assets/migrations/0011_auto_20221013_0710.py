# Generated by Django 3.2 on 2022-10-13 07:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0010_alter_asset_product'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='asset',
            name='specifications',
        ),
        migrations.RemoveField(
            model_name='assetspecification',
            name='specification',
        ),
        migrations.AddField(
            model_name='assetspecification',
            name='name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='assetspecification',
            name='value',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
