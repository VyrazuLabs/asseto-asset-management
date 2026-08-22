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

    For each enabled "extensions.core.<name>" entry, if a same-named
    override folder exists at "extensions/<name>/" (no core/ prefix), the
    override app is prepended before the core app — Django's template/app
    loader resolves by INSTALLED_APPS order, so listing the override first
    makes its templates/static win over core's. Detected purely by
    filesystem presence, never tracked in registry.json itself. A bare
    folder with no matching core/ entry is ignored (not silently
    auto-enabled — it must be enabled like any other extension). See
    docs/extension-architecture.md §9.

    Args:
        base_dir: project BASE_DIR (settings.py's BASE_DIR).

    Returns:
        List of app import paths to append to INSTALLED_APPS. Empty list
        if extensions/registry.json is absent or unreadable.
    """
    extensions_dir = Path(base_dir) / "extensions"
    registry_path = extensions_dir / "registry.json"
    enabled = read_enabled(registry_path)

    result = []
    for app_path in enabled:
        prefix = "extensions.core."
        if app_path.startswith(prefix):
            name = app_path[len(prefix):]
            if (extensions_dir / name).is_dir():
                result.append(f"extensions.{name}")
        result.append(app_path)
    return result
