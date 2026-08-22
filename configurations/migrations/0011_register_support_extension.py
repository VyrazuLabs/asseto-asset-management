"""Register the `support` app as an active InstalledExtension.

Bookkeeping only — `extensions/registry.json` (not this row) is what
actually puts `extensions.core.support` into INSTALLED_APPS. This just
makes the Extensions admin page / `list_extensions` reflect that the
support app was moved into extensions/core/, per
docs/extension-architecture.md §7 (Stage 7).
"""

from django.db import migrations


def register_support_extension(apps, schema_editor):
    InstalledExtension = apps.get_model("configurations", "InstalledExtension")
    InstalledExtension.objects.get_or_create(
        name="support",
        defaults={
            "app_label": "support",
            "version": "1.0.0",
            "status": "active",
            "source": "local",
            "manifest_json": {
                "name": "support",
                "version": "1.0.0",
                "app_label": "support",
                "entry_app": "extensions.core.support",
                "license_required": False,
            },
        },
    )


def unregister_support_extension(apps, schema_editor):
    InstalledExtension = apps.get_model("configurations", "InstalledExtension")
    InstalledExtension.objects.filter(name="support").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("configurations", "0010_installedextension_extensionlicense"),
    ]

    operations = [
        migrations.RunPython(register_support_extension, unregister_support_extension),
    ]
