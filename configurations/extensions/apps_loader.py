"""Boot-time INSTALLED_APPS extension loader.

settings.py calls load_enabled_extension_apps(BASE_DIR) to build the
extension portion of INSTALLED_APPS. Runs before the ORM/app registry
exists, so it only touches the filesystem and must never raise — a missing
extensions/ dir, missing registry.json, or corrupt registry.json all
degrade to an empty list rather than crashing Django startup, per
docs/extension-architecture.md §2.
"""

from pathlib import Path

from configurations.extensions.registry import read_enabled


def load_enabled_extension_apps(base_dir) -> list:
    """Return the list of enabled extension app import paths.

    Each enabled entry is "extensions.core.<name>" (the core app itself).
    Override folders at "extensions/<name>/" (no core/ prefix) are never
    registered as separate Django apps here — an override is templates and
    static assets only, not its own app, so it can't collide with the
    core app's app label, models, or migrations. See
    get_extension_override_dirs() for how overrides are wired in, and
    docs/extension-architecture.md §9.

    Args:
        base_dir: project BASE_DIR (settings.py's BASE_DIR).

    Returns:
        List of app import paths to append to INSTALLED_APPS. Empty list
        if extensions/registry.json is absent or unreadable.
    """
    extensions_dir = Path(base_dir) / "extensions"
    registry_path = extensions_dir / "registry.json"
    return list(read_enabled(registry_path))


def get_extension_override_dirs(base_dir) -> list:
    """Return override folder paths for enabled core extensions.

    For each enabled "extensions.core.<name>" entry, if a same-named
    override folder exists at "extensions/<name>/" (no core/ prefix), its
    path is included here so settings.py can list it first in TEMPLATES
    DIRS / STATICFILES_DIRS — the filesystem loader is checked before
    APP_DIRS, so an override's templates/static win over the core app's
    own, without the override needing an apps.py or any app registration
    at all. A bare folder with no matching core/ entry is ignored (not
    silently auto-enabled — it must be enabled like any other extension).
    See docs/extension-architecture.md §9.

    Args:
        base_dir: project BASE_DIR (settings.py's BASE_DIR).

    Returns:
        List of Path objects for override folders that exist on disk.
        Empty list if extensions/registry.json is absent or unreadable.
    """
    extensions_dir = Path(base_dir) / "extensions"
    registry_path = extensions_dir / "registry.json"
    enabled = read_enabled(registry_path)

    prefix = "extensions.core."
    dirs = []
    for app_path in enabled:
        if not app_path.startswith(prefix):
            continue
        name = app_path[len(prefix):]
        override_dir = extensions_dir / name
        if override_dir.is_dir():
            dirs.append(override_dir)
    return dirs
