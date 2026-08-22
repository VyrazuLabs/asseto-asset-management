"""Core logic behind `manage.py enable_extension` / `disable_extension`.

enable_extension re-validates an installed extension's on-disk manifest,
adds its app path to extensions/registry.json, runs its migrations, and
marks it pending_restart — activation only takes effect after the next
gunicorn SIGHUP reload (configurations.extensions.reload). See
docs/extension-architecture.md §3.

The migration step is injected as migrate_runner so callers (the real
management command) pass the actual `manage.py migrate <app_label>`
subprocess call, while tests pass a stub — avoids needing a real
migratable Django app on disk for every enable/disable test.
"""

import json
import subprocess
import sys
from pathlib import Path

from configurations.extensions.manifest import ManifestValidationError, validate_manifest
from configurations.extensions.permissions import sync_extension_permissions
from configurations.extensions.registry import read_enabled, write_enabled
from configurations.models import InstalledExtension


class ExtensionEnableError(Exception):
    """Raised when enable_extension/disable_extension fails."""


def _run_migrate_subprocess(app_label: str, base_dir=None) -> None:
    """Real migrate runner: re-executes manage.py in a subprocess.

    A fresh process re-reads registry.json, so it sees the just-added app
    in INSTALLED_APPS — the current (already-running) process does not,
    since INSTALLED_APPS was computed once at its own startup.
    """
    base_dir = Path(base_dir) if base_dir else Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "manage.py", "migrate", app_label],
        cwd=str(base_dir),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def enable_extension(name: str, extensions_dir: Path, migrate_runner=None) -> InstalledExtension:
    """Enable an installed extension.

    Args:
        name: extension name (matches InstalledExtension.name).
        extensions_dir: the project's extensions/ directory.
        migrate_runner: callable(app_label) running that app's migrations;
            defaults to a real `manage.py migrate` subprocess call.

    Returns:
        The updated InstalledExtension row (status="pending_restart").

    Raises:
        ExtensionEnableError: if the row doesn't exist, the on-disk
            manifest is invalid, or migration fails. On migration failure,
            the registry write is rolled back and status is set to
            "error" rather than leaving registry.json pointing at an
            unmigrated app.
    """
    migrate_runner = migrate_runner or (lambda app_label: _run_migrate_subprocess(app_label))
    extensions_dir = Path(extensions_dir)

    try:
        row = InstalledExtension.objects.get(name=name)
    except InstalledExtension.DoesNotExist as exc:
        raise ExtensionEnableError(f"extension '{name}' is not installed") from exc

    manifest_path = extensions_dir / "core" / name / "manifest.json"
    if not manifest_path.is_file():
        raise ExtensionEnableError(f"manifest.json not found for '{name}' — was it removed from disk?")
    manifest = json.loads(manifest_path.read_text())
    try:
        validate_manifest(manifest)
    except ManifestValidationError as exc:
        raise ExtensionEnableError(str(exc)) from exc

    app_path = manifest["entry_app"]
    registry_path = extensions_dir / "registry.json"
    enabled = read_enabled(registry_path)
    if app_path not in enabled:
        write_enabled(registry_path, enabled + [app_path])

    try:
        migrate_runner(row.app_label)
    except Exception as exc:
        # Roll back: registry must never point at an unmigrated app.
        write_enabled(registry_path, [a for a in read_enabled(registry_path) if a != app_path])
        row.status = "error"
        row.error_message = str(exc)
        row.save(update_fields=["status", "error_message"])
        raise ExtensionEnableError(f"migration failed for '{name}': {exc}") from exc

    row.status = "pending_restart"
    row.version = manifest["version"]
    row.manifest_json = manifest
    row.error_message = None
    row.save(update_fields=["status", "version", "manifest_json", "error_message"])
    sync_extension_permissions(manifest)
    return row


def disable_extension(name: str, extensions_dir: Path) -> InstalledExtension:
    """Disable an installed extension.

    Removes it from extensions/registry.json (folder/migrations stay on
    disk — reversible via a later enable_extension call) and marks it
    pending_restart.

    Args:
        name: extension name.
        extensions_dir: the project's extensions/ directory.

    Returns:
        The updated InstalledExtension row (status="pending_restart").

    Raises:
        ExtensionEnableError: if the row doesn't exist.
    """
    extensions_dir = Path(extensions_dir)
    try:
        row = InstalledExtension.objects.get(name=name)
    except InstalledExtension.DoesNotExist as exc:
        raise ExtensionEnableError(f"extension '{name}' is not installed") from exc

    app_path = row.manifest_json.get("entry_app")
    registry_path = extensions_dir / "registry.json"
    enabled = read_enabled(registry_path)
    if app_path in enabled:
        write_enabled(registry_path, [a for a in enabled if a != app_path])

    row.status = "pending_restart"
    row.save(update_fields=["status"])
    return row
