"""`python manage.py install_extension <github_url_or_path> [--name NAME]`

CLI-only entry point (SSH access required) per docs/extension-architecture.md
§3 — copies/clones an extension into extensions/core/<name>/ and validates
it, without enabling or executing it. Run `enable_extension` next.
"""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from configurations.extensions.installer import ExtensionInstallError, install_extension


class Command(BaseCommand):
    help = "Install an extension from a local path or a github URL into extensions/core/<name>/."

    def add_arguments(self, parser):
        parser.add_argument("source", help="Local directory path or github/git URL")
        parser.add_argument("--name", help="Extension folder name (defaults to source's basename)")

    def handle(self, *args, **options):
        source = options["source"]
        name = options["name"] or Path(source.rstrip("/")).stem
        extensions_dir = Path(settings.BASE_DIR) / "extensions"

        try:
            ext = install_extension(source, extensions_dir=extensions_dir, name=name)
        except ExtensionInstallError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Installed '{ext.name}' v{ext.version} (status=installed)."))
        self.stdout.write(
            f"Review extensions/core/{ext.name}/ contents, then run: "
            f"python manage.py enable_extension {ext.name}"
        )
