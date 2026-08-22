"""`python manage.py disable_extension <name>`

Removes an extension from extensions/registry.json — its folder and
migrations stay on disk (reversible). Takes effect after the next gunicorn
reload. See docs/extension-architecture.md §3.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.enabler import ExtensionEnableError, disable_extension


class Command(BaseCommand):
    help = "Disable an installed extension (folder/migrations stay on disk, reversible)."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Extension name")

    def handle(self, *args, **options):
        name = options["name"]
        extensions_dir = Path(settings.BASE_DIR) / "extensions"

        try:
            ext = disable_extension(name, extensions_dir=extensions_dir)
        except ExtensionEnableError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Disabled '{ext.name}' (status=pending_restart)."))
        self.stdout.write("Trigger a graceful restart to deactivate it.")
