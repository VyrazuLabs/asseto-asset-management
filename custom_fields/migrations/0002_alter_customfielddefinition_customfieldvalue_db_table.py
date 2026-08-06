from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("custom_fields", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelTable(
            name="customfielddefinition",
            table="custom_fields_customfielddefinition",
        ),
        migrations.AlterModelTable(
            name="customfieldvalue",
            table="custom_fields_customfieldvalue",
        ),
    ]
