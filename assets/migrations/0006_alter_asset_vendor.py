# Generated by Django 3.2 on 2022-09-28 08:06

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('vendors', '0003_auto_20220703_1843'),
        ('assets', '0005_auto_20220926_1137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='vendor',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='vendors.vendor'),
        ),
    ]
