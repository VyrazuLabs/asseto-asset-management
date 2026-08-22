"""Tests for the INSTALLED_APPS extension loader used by settings.py.

configurations.extensions.apps_loader.load_enabled_extension_apps is the
function settings.py calls at import time (before the ORM exists) to build
the extension portion of INSTALLED_APPS, per docs/extension-architecture.md
§2. Must degrade to [] on a missing extensions/ dir, missing registry.json,
or corrupt registry.json — never raise, since a broken registry must not
crash Django startup.
"""

from configurations.extensions.apps_loader import load_enabled_extension_apps
from configurations.extensions.registry import write_enabled


def test_load_enabled_extension_apps_returns_empty_when_extensions_dir_missing(tmp_path):
    # Arrange — base_dir with no extensions/ subdirectory at all
    base_dir = tmp_path

    # Act
    result = load_enabled_extension_apps(base_dir)

    # Assert
    assert result == []


def test_load_enabled_extension_apps_returns_empty_when_registry_missing(tmp_path):
    # Arrange — extensions/ dir exists but registry.json does not
    (tmp_path / "extensions").mkdir()

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert
    assert result == []


def test_load_enabled_extension_apps_returns_empty_when_registry_corrupt(tmp_path):
    # Arrange
    extensions_dir = tmp_path / "extensions"
    extensions_dir.mkdir()
    (extensions_dir / "registry.json").write_text("not json")

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert
    assert result == []


def test_load_enabled_extension_apps_returns_enabled_list(tmp_path):
    # Arrange
    extensions_dir = tmp_path / "extensions"
    extensions_dir.mkdir()
    write_enabled(extensions_dir / "registry.json", ["extensions.core.sample_extension"])

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert
    assert result == ["extensions.core.sample_extension"]
