# Generated by Django 3.2 on 2022-11-29 05:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('assets', '0016_auto_20221102_1438'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]