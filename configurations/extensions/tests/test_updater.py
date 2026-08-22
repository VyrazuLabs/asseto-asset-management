"""Tests for configurations.extensions.updater.update_extension.

`manage.py update_extension <name>` refreshes extensions/core/<name>/ in
place — from a new local source, or (for a github-sourced extension) via
git pull, injected here as pull_fn so tests never touch a real repo. Only
extensions/core/<name>/ is ever touched — a same-named override folder at
extensions/<name>/ is untouched, per docs/extension-architecture.md §8/§9.
"""

import json

import pytest

from configurations.extensions.updater import ExtensionUpdateError, update_extension
from configurations.models import InstalledExtension


def _write_extension(dir_path, name="sample_extension", app_label="ext_sample_extension", version="1.0.0"):
    dir_path.mkdir(parents=True, exist_ok=True)
    (dir_path / "__init__.py").write_text("")
    (dir_path / "manifest.json").write_text(
        json.dumps(
            {
                "name": name,
                "version": version,
                "app_label": app_label,
                "entry_app": f"extensions.core.{name}",
                "license_required": False,
            }
        )
    )
    (dir_path / "apps.py").write_text(
        f"from django.apps import AppConfig\n\nclass Config(AppConfig):\n    label = \"{app_label}\"\n"
    )


def _install_row(name="sample_extension", app_label="ext_sample_extension", version="1.0.0"):
    return InstalledExtension.objects.create(
        name=name,
        app_label=app_label,
        version=version,
        status="active",
        source="local",
        manifest_json={"name": name, "app_label": app_label, "entry_app": f"extensions.core.{name}"},
    )


@pytest.mark.django_db
def test_update_extension_replaces_core_folder_from_new_local_source(tmp_path):
    # Arrange
    row = _install_row()
    extensions_dir = tmp_path / "extensions"
    _write_extension(extensions_dir / "core" / row.name, version="1.0.0")
    new_source = tmp_path / "new_src"
    _write_extension(new_source, version="2.0.0")

    # Act
    update_extension(row.name, extensions_dir=extensions_dir, new_source=str(new_source), migrate_runner=lambda l: None)

    # Assert
    row.refresh_from_db()
    assert row.version == "2.0.0"
    manifest = json.loads((extensions_dir / "core" / row.name / "manifest.json").read_text())
    assert manifest["version"] == "2.0.0"


@pytest.mark.django_db
def test_update_extension_leaves_override_folder_untouched(tmp_path):
    # Arrange
    row = _install_row()
    extensions_dir = tmp_path / "extensions"
    _write_extension(extensions_dir / "core" / row.name, version="1.0.0")
    override_dir = extensions_dir / row.name
    override_dir.mkdir(parents=True)
    (override_dir / "marker.txt").write_text("my customization")
    new_source = tmp_path / "new_src"
    _write_extension(new_source, version="2.0.0")

    # Act
    update_extension(row.name, extensions_dir=extensions_dir, new_source=str(new_source), migrate_runner=lambda l: None)

    # Assert — override folder and its contents untouched
    assert (override_dir / "marker.txt").read_text() == "my customization"


@pytest.mark.django_db
def test_update_extension_rejects_app_label_change(tmp_path):
    # Arrange — identity (app_label) must not change mid-update, would orphan migrations/data
    row = _install_row(app_label="ext_sample_extension")
    extensions_dir = tmp_path / "extensions"
    _write_extension(extensions_dir / "core" / row.name, app_label="ext_sample_extension")
    new_source = tmp_path / "new_src"
    _write_extension(new_source, app_label="ext_renamed_extension")

    # Act / Assert
    with pytest.raises(ExtensionUpdateError):
        update_extension(row.name, extensions_dir=extensions_dir, new_source=str(new_source), migrate_runner=lambda l: None)


@pytest.mark.django_db
def test_update_extension_uses_pull_fn_when_no_new_source_given(tmp_path):
    # Arrange — github-sourced extension, updated via git pull in place
    row = _install_row()
    row.source = "github"
    row.source_url = "https://example.com/repo.git"
    row.save()
    extensions_dir = tmp_path / "extensions"
    core_dir = extensions_dir / "core" / row.name
    _write_extension(core_dir, version="1.0.0")
    calls = []

    def fake_pull(path):
        calls.append(path)
        # simulate the pull bumping the version on disk
        manifest_path = path / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "1.1.0"
        manifest_path.write_text(json.dumps(manifest))

    # Act
    update_extension(row.name, extensions_dir=extensions_dir, migrate_runner=lambda l: None, pull_fn=fake_pull)

    # Assert
    row.refresh_from_db()
    assert row.version == "1.1.0"
    assert calls == [core_dir]
