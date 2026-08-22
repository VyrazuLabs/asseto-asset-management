"""`python manage.py enable_extension <name>`

Registers an installed extension in extensions/registry.json and runs its
migrations. Takes effect only after a gunicorn reload (Extensions page →
Apply Changes, or `kill -HUP $(cat gunicorn.pid)`). See
docs/extension-architecture.md §3/§4.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.enabler import ExtensionEnableError, enable_extension


class Command(BaseCommand):
    help = "Enable an installed extension: register it and run its migrations."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Extension name (as installed)")

    def handle(self, *args, **options):
        name = options["name"]
        extensions_dir = Path(settings.BASE_DIR) / "extensions"

        try:
            ext = enable_extension(name, extensions_dir=extensions_dir)
        except ExtensionEnableError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Enabled '{ext.name}' (status=pending_restart)."))
        self.stdout.write(
            "Trigger a graceful restart (Extensions page → Apply Changes, or "
            "`kill -HUP $(cat gunicorn.pid)`) to activate it."
        )
