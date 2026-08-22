"""Read/write helpers for extensions/registry.json.

registry.json is the boot-time snapshot of which extension apps are
enabled — settings.py reads it synchronously before the ORM/app registry
exists, so it must degrade to an empty list on any missing/corrupt file
rather than raise, per docs/extension-architecture.md §2.
"""

import json
import os
from pathlib import Path


def read_enabled(registry_path: Path) -> list:
    """Read the list of enabled extension app paths from registry.json.

    Args:
        registry_path: path to registry.json.

    Returns:
        List of app import paths (e.g. "extensions.core.sample_extension").
        Empty list if the file is missing, unreadable, or not valid JSON —
        fail-closed so a corrupt registry never crashes Django startup.
    """
    registry_path = Path(registry_path)
    if not registry_path.is_file():
        return []
    try:
        data = json.loads(registry_path.read_text())
    except (OSError, json.JSONDecodeError):
        return []
    return data.get("enabled", [])


def write_enabled(registry_path: Path, enabled: list) -> None:
    """Atomically write the list of enabled extension app paths.

    Writes to a temp file in the same directory then renames it into place
    (os.replace is atomic on POSIX and Windows), so a crash mid-write never
    leaves a partially-written registry.json on disk.

    Args:
        registry_path: path to registry.json.
        enabled: list of app import paths to persist as enabled.
    """
    registry_path = Path(registry_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = registry_path.with_suffix(".json.tmp")
    tmp_path.write_text(json.dumps({"enabled": enabled}, indent=2))
    os.replace(tmp_path, registry_path)
