# Generated by Django 3.2 on 2023-01-04 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0017_alter_organization_logo'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='department',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='productcategory',
            name='status',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='producttype',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]