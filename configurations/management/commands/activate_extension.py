"""`python manage.py activate_extension <name> <license_key> --org <org_id>`

One-time activation against the external license server — stores the
returned activation_token in ExtensionLicense for daily revalidation. See
docs/extension-architecture.md §5.
"""

from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.license_client import LicenseServerError, activate
from configurations.models import ExtensionLicense, InstalledExtension
from dashboard.models import Organization


class Command(BaseCommand):
    help = "Activate a paid extension's license for an organization against the license server."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Extension name")
        parser.add_argument("license_key", help="License key issued by the license server")
        parser.add_argument("--org", required=True, help="Organization id to activate for")

    def handle(self, *args, **options):
        base_url = getattr(settings, "LICENSE_SERVER_URL", None)
        if not base_url:
            raise CommandError("LICENSE_SERVER_URL is not configured.")

        try:
            extension = InstalledExtension.objects.get(name=options["name"])
        except InstalledExtension.DoesNotExist as exc:
            raise CommandError(f"extension '{options['name']}' is not installed") from exc

        try:
            organization = Organization.objects.get(pk=options["org"])
        except Organization.DoesNotExist as exc:
            raise CommandError(f"organization '{options['org']}' not found") from exc

        try:
            result = activate(
                base_url=base_url,
                org_id=str(organization.pk),
                domain=organization.website or "",
                license_key=options["license_key"],
                extension_name=extension.name,
            )
        except LicenseServerError as exc:
            raise CommandError(f"activation failed: {exc}") from exc

        valid_until = result.get("valid_until")
        ExtensionLicense.objects.update_or_create(
            extension=extension,
            organization=organization,
            defaults={
                "activation_token": result["activation_token"],
                "status": "active",
                "valid_until": datetime.fromisoformat(valid_until.replace("Z", "+00:00"))
                if valid_until
                else None,
                "last_checked_at": None,
                "last_error": None,
            },
        )

        self.stdout.write(
            self.style.SUCCESS(f"Activated '{extension.name}' for organization '{organization}'.")
        )
