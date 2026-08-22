"""`python manage.py list_extensions [--json]`

Status table cross-checking each InstalledExtension row against
extensions/registry.json and the running process's INSTALLED_APPS (i.e.
what's actually active right now vs. what's pending a restart). See
docs/extension-architecture.md §3.
"""

import json as json_module
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from configurations.extensions.registry import read_enabled
from configurations.models import InstalledExtension


def _derived_status(row, enabled_in_registry: bool, active_in_process: bool) -> str:
    if row.status == "error":
        return f"error: {row.error_message}"
    if row.status == "installed":
        return "installed"
    if enabled_in_registry and active_in_process:
        return "enabled (active)"
    if enabled_in_registry and not active_in_process:
        return "enabled (pending restart)"
    if not enabled_in_registry and row.status == "pending_restart":
        return "disabled (pending restart)"
    return "disabled"


class Command(BaseCommand):
    help = "List installed extensions and their effective status."

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", help="Output as JSON")

    def handle(self, *args, **options):
        extensions_dir = Path(settings.BASE_DIR) / "extensions"
        registry_enabled = set(read_enabled(extensions_dir / "registry.json"))
        active_apps = set(settings.INSTALLED_APPS)

        rows = []
        for ext in InstalledExtension.objects.all().order_by("name"):
            app_path = ext.manifest_json.get("entry_app", "")
            rows.append(
                {
                    "name": ext.name,
                    "version": ext.version,
                    "status": _derived_status(
                        ext, app_path in registry_enabled, app_path in active_apps
                    ),
                    "source": ext.source,
                }
            )

        if options["json"]:
            self.stdout.write(json_module.dumps(rows, indent=2))
            return

        if not rows:
            self.stdout.write("No extensions installed.")
            return
        for row in rows:
            self.stdout.write(f"{row['name']:<30} v{row['version']:<10} {row['status']:<28} ({row['source']})")
