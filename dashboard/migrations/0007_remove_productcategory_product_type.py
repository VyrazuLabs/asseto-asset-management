# Generated by Django 3.2 on 2022-09-21 11:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0006_rename_product_category_productcategory_product_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productcategory',
            name='product_type',
        ),
    ]
