# Generated by Django 3.2 on 2022-09-28 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0007_remove_productcategory_product_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='producttype',
            name='is_deleted',
            field=models.BooleanField(default=False),
        ),
    ]
