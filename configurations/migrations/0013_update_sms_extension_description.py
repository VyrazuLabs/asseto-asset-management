from django.db import migrations

OLD_TEXT = "Configure SMS service (MSG91, etc.) to send automated ticket alerts to employees and clients."
NEW_TEXT = "Configure SMS service to send automated ticket alerts to employees and clients."


def update_sms_extension_description(apps, schema_editor):
    Extensions = apps.get_model("configurations", "Extensions")
    Extensions.objects.filter(entity_name="SMS", description=OLD_TEXT).update(
        description=NEW_TEXT
    )


def revert_sms_extension_description(apps, schema_editor):
    Extensions = apps.get_model("configurations", "Extensions")
    Extensions.objects.filter(entity_name="SMS", description=NEW_TEXT).update(
        description=OLD_TEXT
    )


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0012_smslog_smsconfiguration"),
    ]

    operations = [
        migrations.RunPython(
            update_sms_extension_description, revert_sms_extension_description
        ),
    ]
