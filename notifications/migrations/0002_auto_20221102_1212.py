# Generated by Django 3.2 on 2022-11-02 06:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='usernotification',
            name='notification',
        ),
        migrations.RemoveField(
            model_name='usernotification',
            name='user',
        ),
        migrations.DeleteModel(
            name='Notification',
        ),
        migrations.DeleteModel(
            name='UserNotification',
        ),
    ]
