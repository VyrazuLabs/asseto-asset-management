"""Tests for extensions/registry.json read/write helpers.

configurations.extensions.registry is the single source both settings.py
(at boot, read-only) and the management commands (read-modify-write) use to
track which extension apps are enabled, per docs/extension-architecture.md §2.
"""

import json

from configurations.extensions.registry import read_enabled, write_enabled


def test_read_enabled_returns_empty_list_when_file_missing(tmp_path):
    # Arrange
    registry_path = tmp_path / "registry.json"

    # Act
    result = read_enabled(registry_path)

    # Assert
    assert result == []


def test_read_enabled_returns_empty_list_when_json_corrupt(tmp_path):
    # Arrange
    registry_path = tmp_path / "registry.json"
    registry_path.write_text("{not valid json")

    # Act
    result = read_enabled(registry_path)

    # Assert
    assert result == []


def test_write_enabled_then_read_enabled_round_trips(tmp_path):
    # Arrange
    registry_path = tmp_path / "registry.json"

    # Act
    write_enabled(registry_path, ["extensions.core.sample_extension"])
    result = read_enabled(registry_path)

    # Assert
    assert result == ["extensions.core.sample_extension"]


def test_write_enabled_is_atomic_no_partial_file_on_disk(tmp_path):
    # Arrange
    registry_path = tmp_path / "registry.json"

    # Act
    write_enabled(registry_path, ["extensions.core.sample_extension"])

    # Assert — final file is valid JSON with the expected shape, and no
    # leftover temp file from the atomic-rename write.
    data = json.loads(registry_path.read_text())
    assert data == {"enabled": ["extensions.core.sample_extension"]}
    leftovers = list(tmp_path.glob("*.tmp"))
    assert leftovers == []
