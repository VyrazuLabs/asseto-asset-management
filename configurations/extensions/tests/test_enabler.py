"""Tests for configurations.extensions.enabler.

enable_extension()/disable_extension() drive `manage.py enable_extension`
and `manage.py disable_extension` — they mutate extensions/registry.json
and InstalledExtension.status. The actual `manage.py migrate <app_label>`
subprocess call is injected as migrate_runner so these tests exercise the
registry/DB bookkeeping without needing a real migratable Django app on
disk (that's covered by the sample_extension integration smoke test), per
docs/extension-architecture.md §3.
"""

import json

import pytest

from configurations.extensions.enabler import (
    ExtensionEnableError,
    disable_extension,
    enable_extension,
)
from configurations.extensions.registry import read_enabled
from configurations.models import InstalledExtension


def _install_row(name="sample_extension", app_label="ext_sample_extension"):
    return InstalledExtension.objects.create(
        name=name,
        app_label=app_label,
        version="1.0.0",
        status="installed",
        source="local",
        manifest_json={
            "name": name,
            "version": "1.0.0",
            "app_label": app_label,
            "entry_app": f"extensions.core.{name}",
            "license_required": False,
        },
    )


def _write_manifest_on_disk(extensions_dir, name, app_label):
    ext_dir = extensions_dir / "core" / name
    ext_dir.mkdir(parents=True)
    (ext_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": "1.0.0",
                "app_label": app_label,
                "entry_app": f"extensions.core.{name}",
                "license_required": False,
            }
        )
    )


@pytest.mark.django_db
def test_enable_extension_adds_to_registry_and_marks_pending_restart(tmp_path):
    # Arrange
    row = _install_row()
    extensions_dir = tmp_path / "extensions"
    _write_manifest_on_disk(extensions_dir, row.name, row.app_label)
    calls = []

    # Act
    enable_extension(
        row.name,
        extensions_dir=extensions_dir,
        migrate_runner=lambda app_label: calls.append(app_label),
    )

    # Assert
    row.refresh_from_db()
    assert row.status == "pending_restart"
    assert read_enabled(extensions_dir / "registry.json") == ["extensions.core.sample_extension"]
    assert calls == ["ext_sample_extension"]


@pytest.mark.django_db
def test_enable_extension_rolls_back_registry_when_migration_fails(tmp_path):
    # Arrange
    row = _install_row()
    extensions_dir = tmp_path / "extensions"
    _write_manifest_on_disk(extensions_dir, row.name, row.app_label)

    def failing_migrate(app_label):
        raise RuntimeError("boom")

    # Act
    with pytest.raises(ExtensionEnableError):
        enable_extension(row.name, extensions_dir=extensions_dir, migrate_runner=failing_migrate)

    # Assert — registry untouched, DB row marked error, not left "enabled but unmigrated"
    row.refresh_from_db()
    assert row.status == "error"
    assert read_enabled(extensions_dir / "registry.json") == []


@pytest.mark.django_db
def test_enable_extension_raises_when_row_missing(tmp_path):
    # Arrange
    extensions_dir = tmp_path / "extensions"

    # Act / Assert
    with pytest.raises(ExtensionEnableError):
        enable_extension("nonexistent", extensions_dir=extensions_dir, migrate_runner=lambda l: None)


@pytest.mark.django_db
def test_disable_extension_removes_from_registry_and_marks_pending_restart(tmp_path):
    # Arrange
    row = _install_row()
    extensions_dir = tmp_path / "extensions"
    _write_manifest_on_disk(extensions_dir, row.name, row.app_label)
    enable_extension(row.name, extensions_dir=extensions_dir, migrate_runner=lambda l: None)

    # Act
    disable_extension(row.name, extensions_dir=extensions_dir)

    # Assert
    row.refresh_from_db()
    assert row.status == "pending_restart"
    assert read_enabled(extensions_dir / "registry.json") == []
    # folder/migrations untouched — reversible
    assert (extensions_dir / "core" / row.name / "manifest.json").is_file()
