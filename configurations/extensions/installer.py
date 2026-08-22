"""Core logic behind `manage.py install_extension`.

Copies (or, for a github source, clones) an extension into
extensions/core/<name>/, validates its manifest, and records an
InstalledExtension row with status="installed" — does NOT enable it
(registry.json/INSTALLED_APPS untouched). See
docs/extension-architecture.md §3.

Deliberately never imports/executes the extension's own Python code: the
AppConfig.label cross-check is done via ast.parse, matching the "no code
execution at install time" security stance in §9 of the design doc.
"""

import ast
import json
import shutil
import subprocess
from pathlib import Path

from configurations.extensions.manifest import ManifestValidationError, validate_manifest
from configurations.models import InstalledExtension


class ExtensionInstallError(Exception):
    """Raised when install_extension fails; installer guarantees no partial state on disk or in the DB."""


def extract_app_label_static(apps_py_path: Path):
    """Read AppConfig.label from apps.py without importing it.

    Args:
        apps_py_path: path to the extension's apps.py.

    Returns:
        The string value assigned to `label` on the first class found, or
        None if no such assignment exists.
    """
    apps_py_path = Path(apps_py_path)
    tree = ast.parse(apps_py_path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for stmt in node.body:
                if isinstance(stmt, ast.Assign):
                    for target in stmt.targets:
                        if isinstance(target, ast.Name) and target.id == "label":
                            if isinstance(stmt.value, ast.Constant):
                                return stmt.value.value
    return None


def _looks_like_url(source: str) -> bool:
    return source.startswith("https://") or source.startswith("git@")


def install_extension(source: str, extensions_dir: Path, name: str) -> InstalledExtension:
    """Install an extension from a local path or a github URL.

    Args:
        source: local directory path, or a github/git URL.
        extensions_dir: the project's extensions/ directory.
        name: the extension's folder name (also expected manifest "name").

    Returns:
        The created InstalledExtension row (status="installed").

    Raises:
        ExtensionInstallError: on any validation/copy failure. Guarantees
            no partial folder is left on disk and no DB row is created.
    """
    extensions_dir = Path(extensions_dir)
    target_dir = extensions_dir / "core" / name

    if target_dir.exists():
        raise ExtensionInstallError(
            f"extensions/core/{name}/ already exists; disable and remove it first, or choose a different name"
        )

    target_dir.parent.mkdir(parents=True, exist_ok=True)

    if _looks_like_url(source):
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", source, str(target_dir)],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ExtensionInstallError(f"git clone failed: {exc.stderr}") from exc
    else:
        shutil.copytree(source, target_dir)

    try:
        manifest_path = target_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ExtensionInstallError("manifest.json not found in extension source")
        manifest = json.loads(manifest_path.read_text())
        validate_manifest(manifest)

        apps_py_path = target_dir / "apps.py"
        if not apps_py_path.is_file():
            raise ExtensionInstallError("apps.py not found in extension source")
        static_label = extract_app_label_static(apps_py_path)
        if static_label != manifest.get("app_label"):
            raise ExtensionInstallError(
                f"apps.py AppConfig.label ({static_label!r}) does not match "
                f"manifest.json app_label ({manifest.get('app_label')!r})"
            )
        return InstalledExtension.objects.create(
            name=name,
            app_label=manifest["app_label"],
            version=manifest["version"],
            status="installed",
            source="github" if _looks_like_url(source) else "local",
            source_url=source if _looks_like_url(source) else None,
            manifest_json=manifest,
        )
    except Exception as exc:
        # Any failure past this point — validation, label mismatch, or the
        # DB insert itself — must leave no partial folder on disk.
        shutil.rmtree(target_dir, ignore_errors=True)
        if isinstance(exc, ExtensionInstallError):
            raise
        raise ExtensionInstallError(str(exc)) from exc
