# Generated by Django 3.2 on 2022-07-03 18:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '0003_auto_20220703_1843'),
        ('vendors', '0002_auto_20220621_1350'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='vendor',
            name='city',
        ),
        migrations.RemoveField(
            model_name='vendor',
            name='country',
        ),
        migrations.RemoveField(
            model_name='vendor',
            name='pin_code',
        ),
        migrations.RemoveField(
            model_name='vendor',
            name='state',
        ),
        migrations.AddField(
            model_name='vendor',
            name='deleted',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='address',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='dashboard.address'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
    ]