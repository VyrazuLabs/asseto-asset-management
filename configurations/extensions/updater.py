"""Core logic behind `manage.py update_extension`.

Refreshes extensions/core/<name>/ in place — from a new local source, or
via a git pull for a github-sourced extension — then re-migrates. Only the
core/ copy is ever touched; a same-named override folder at
extensions/<name>/ is a physically separate path, so it's untouched.
identity fields (name/app_label) must not change mid-update — that would
orphan existing migrations/data. See docs/extension-architecture.md §8/§9.
"""

import json
import shutil
import subprocess
from pathlib import Path

from configurations.extensions.manifest import ManifestValidationError, validate_manifest
from configurations.extensions.permissions import sync_extension_permissions
from configurations.models import InstalledExtension


class ExtensionUpdateError(Exception):
    """Raised when update_extension fails."""


def _default_pull(core_dir: Path) -> None:
    result = subprocess.run(["git", "pull"], cwd=str(core_dir), capture_output=True, text=True)
    if result.returncode != 0:
        raise ExtensionUpdateError(f"git pull failed: {result.stderr}")


def update_extension(
    name: str,
    extensions_dir: Path,
    new_source: str = None,
    migrate_runner=None,
    pull_fn=None,
) -> InstalledExtension:
    """Update an extension's core/ copy in place.

    Args:
        name: extension name.
        extensions_dir: the project's extensions/ directory.
        new_source: optional local path to replace the core folder with
            (wholesale copy). If omitted, a github-sourced extension is
            updated via `git pull` in place instead.
        migrate_runner: callable(app_label) running new migrations.
        pull_fn: callable(core_dir) performing the git pull; defaults to
            a real `git pull` subprocess call.

    Returns:
        The updated InstalledExtension row.

    Raises:
        ExtensionUpdateError: if the row doesn't exist, the update source
            changes the extension's identity (name/app_label), or
            migration fails.
    """
    extensions_dir = Path(extensions_dir)
    core_dir = extensions_dir / "core" / name

    try:
        row = InstalledExtension.objects.get(name=name)
    except InstalledExtension.DoesNotExist as exc:
        raise ExtensionUpdateError(f"extension '{name}' is not installed") from exc

    if new_source:
        backup_dir = core_dir.with_suffix(".bak")
        shutil.copytree(core_dir, backup_dir)
        shutil.rmtree(core_dir)
        try:
            shutil.copytree(new_source, core_dir)
        except Exception:
            shutil.move(str(backup_dir), str(core_dir))
            raise
    else:
        pull_fn = pull_fn or _default_pull
        pull_fn(core_dir)
        backup_dir = None

    try:
        manifest = json.loads((core_dir / "manifest.json").read_text())
        validate_manifest(manifest)
        if manifest["name"] != row.name or manifest["app_label"] != row.app_label:
            raise ExtensionUpdateError(
                "update source changes the extension's identity "
                f"(name/app_label) — was '{row.name}'/'{row.app_label}', "
                f"got '{manifest.get('name')}'/'{manifest.get('app_label')}'"
            )
    except (ManifestValidationError, ExtensionUpdateError, json.JSONDecodeError) as exc:
        if backup_dir and backup_dir.exists():
            shutil.rmtree(core_dir, ignore_errors=True)
            shutil.move(str(backup_dir), str(core_dir))
        raise ExtensionUpdateError(str(exc)) from exc

    if backup_dir and backup_dir.exists():
        shutil.rmtree(backup_dir)

    migrate_runner = migrate_runner or (lambda app_label: None)
    migrate_runner(row.app_label)

    row.version = manifest["version"]
    row.manifest_json = manifest
    row.save(update_fields=["version", "manifest_json"])
    sync_extension_permissions(manifest)
    return row
