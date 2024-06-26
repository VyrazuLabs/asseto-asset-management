# Generated by Django 3.2 on 2022-10-18 10:15

import authentication.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication', '0011_auto_20221017_1111'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='access_level',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_pic',
            field=models.ImageField(blank=True, default='profile_pics/default.jpg', null=True, upload_to=authentication.models.path_and_rename),
        ),
    ]
