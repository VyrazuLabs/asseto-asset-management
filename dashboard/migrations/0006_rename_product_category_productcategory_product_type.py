# Generated by Django 3.2 on 2022-08-30 07:25

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0005_alter_organization_logo'),
    ]

    operations = [
        migrations.RenameField(
            model_name='productcategory',
            old_name='product_category',
            new_name='product_type',
        ),
    ]
