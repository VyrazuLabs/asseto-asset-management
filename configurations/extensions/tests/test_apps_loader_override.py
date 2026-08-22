"""Tests for core/override pairing in load_enabled_extension_apps.

Per docs/extension-architecture.md §9: extensions/core/<name>/ is the
shipped extension; extensions/<name>/ (same name, no core/ prefix) is an
optional override, detected purely by filesystem presence — never
separately tracked in registry.json. When present, the override app must
be listed BEFORE the core app in INSTALLED_APPS so Django's template/app
loader precedence picks its templates/static over core's.
"""

from configurations.extensions.apps_loader import load_enabled_extension_apps
from configurations.extensions.registry import write_enabled


def test_returns_core_app_unchanged_when_no_override_folder(tmp_path):
    # Arrange
    extensions_dir = tmp_path / "extensions"
    extensions_dir.mkdir()
    write_enabled(extensions_dir / "registry.json", ["extensions.core.sample_extension"])

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert
    assert result == ["extensions.core.sample_extension"]


def test_prepends_override_app_before_core_app_when_override_folder_exists(tmp_path):
    # Arrange
    extensions_dir = tmp_path / "extensions"
    extensions_dir.mkdir()
    write_enabled(extensions_dir / "registry.json", ["extensions.core.sample_extension"])
    (extensions_dir / "sample_extension").mkdir()

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert — override listed first, both present
    assert result == ["extensions.sample_extension", "extensions.core.sample_extension"]


def test_ignores_bare_folder_with_no_matching_core_entry(tmp_path):
    # Arrange — a standalone extension with no core/ counterpart, and no
    # registry entry either — must not be silently auto-enabled.
    extensions_dir = tmp_path / "extensions"
    extensions_dir.mkdir()
    write_enabled(extensions_dir / "registry.json", [])
    (extensions_dir / "unrelated_extension").mkdir()

    # Act
    result = load_enabled_extension_apps(tmp_path)

    # Assert
    assert result == []
