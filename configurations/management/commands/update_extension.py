"""`python manage.py update_extension <name> [--source PATH]`

Refreshes extensions/core/<name>/ in place — from --source (local path) if
given, else via `git pull` for a github-sourced extension. Never touches a
same-named override folder. See docs/extension-architecture.md §8/§9.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.updater import ExtensionUpdateError, update_extension


class Command(BaseCommand):
    help = "Update an installed extension's core/ copy in place and re-run its migrations."

    def add_arguments(self, parser):
        parser.add_argument("name", help="Extension name")
        parser.add_argument("--source", help="Local path to update from (defaults to git pull)")

    def handle(self, *args, **options):
        extensions_dir = Path(settings.BASE_DIR) / "extensions"

        try:
            ext = update_extension(options["name"], extensions_dir=extensions_dir, new_source=options["source"])
        except ExtensionUpdateError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Updated '{ext.name}' to v{ext.version}."))
        self.stdout.write("Trigger a graceful restart to activate the update.")
