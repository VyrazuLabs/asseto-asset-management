# Generated by Django 3.2 on 2023-01-04 09:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0012_alter_product_product_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='status',
            field=models.BooleanField(default=True),
        ),
    ]