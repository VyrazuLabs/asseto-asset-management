# Generated by Django 3.2 on 2022-06-21 13:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='created_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='updated_by',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]