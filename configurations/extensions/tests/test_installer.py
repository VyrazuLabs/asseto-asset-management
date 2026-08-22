"""Tests for configurations.extensions.installer.

install_extension() is the core logic behind `manage.py install_extension`
— copies a local extension source into extensions/core/<name>/, validates
its manifest, and statically checks apps.py's AppConfig.label against the
manifest without ever importing/executing the extension's code (per
docs/extension-architecture.md §3). Github-clone sourcing is exercised
manually/in the CLI smoke test, not unit tests (network call).
"""

import pytest

from configurations.extensions.installer import (
    ExtensionInstallError,
    extract_app_label_static,
    install_extension,
)
from configurations.models import InstalledExtension


def _write_sample_extension(src_dir, app_label="ext_sample_extension", entry_app=None):
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "manifest.json").write_text(
        """{
        "name": "sample_extension",
        "version": "1.0.0",
        "app_label": "%s",
        "entry_app": "%s",
        "license_required": false
        }"""
        % (app_label, entry_app or "extensions.core.sample_extension")
    )
    (src_dir / "apps.py").write_text(
        "from django.apps import AppConfig\n\n"
        "class SampleExtensionConfig(AppConfig):\n"
        f"    label = \"{app_label}\"\n"
        "    name = \"extensions.core.sample_extension\"\n"
    )
    return src_dir


def test_extract_app_label_static_reads_label_without_importing(tmp_path):
    # Arrange
    apps_py = tmp_path / "apps.py"
    apps_py.write_text(
        "from django.apps import AppConfig\n\n"
        "class FooConfig(AppConfig):\n"
        "    label = \"ext_foo\"\n"
    )

    # Act
    label = extract_app_label_static(apps_py)

    # Assert
    assert label == "ext_foo"


def test_extract_app_label_static_returns_none_when_no_label(tmp_path):
    # Arrange
    apps_py = tmp_path / "apps.py"
    apps_py.write_text("from django.apps import AppConfig\n\nclass FooConfig(AppConfig):\n    pass\n")

    # Act
    label = extract_app_label_static(apps_py)

    # Assert
    assert label is None


@pytest.mark.django_db
def test_install_extension_copies_source_and_creates_row(tmp_path):
    # Arrange
    src = _write_sample_extension(tmp_path / "src")
    extensions_dir = tmp_path / "extensions"

    # Act
    ext = install_extension(str(src), extensions_dir=extensions_dir, name="sample_extension")

    # Assert
    assert (extensions_dir / "core" / "sample_extension" / "manifest.json").is_file()
    assert ext.status == "installed"
    assert ext.name == "sample_extension"
    assert InstalledExtension.objects.filter(name="sample_extension").exists()


@pytest.mark.django_db
def test_install_extension_rejects_invalid_manifest_and_leaves_no_partial_dir(tmp_path):
    # Arrange — manifest missing required "version" key
    src = tmp_path / "src"
    src.mkdir()
    (src / "manifest.json").write_text(
        '{"name": "broken_ext", "app_label": "ext_broken_ext", '
        '"entry_app": "extensions.core.broken_ext", "license_required": false}'
    )
    (src / "apps.py").write_text(
        "from django.apps import AppConfig\n\nclass BrokenExtConfig(AppConfig):\n    label = \"ext_broken_ext\"\n"
    )
    extensions_dir = tmp_path / "extensions"

    # Act / Assert
    with pytest.raises(ExtensionInstallError):
        install_extension(str(src), extensions_dir=extensions_dir, name="broken_ext")
    assert not (extensions_dir / "core" / "broken_ext").exists()
    assert not InstalledExtension.objects.filter(name="broken_ext").exists()


@pytest.mark.django_db
def test_install_extension_rejects_app_label_mismatch(tmp_path):
    # Arrange — manifest says ext_sample_extension, apps.py says something else
    src = _write_sample_extension(tmp_path / "src", app_label="ext_sample_extension")
    (src / "apps.py").write_text(
        "from django.apps import AppConfig\n\nclass SampleExtensionConfig(AppConfig):\n    label = \"ext_wrong_label\"\n"
    )
    extensions_dir = tmp_path / "extensions"

    # Act / Assert
    with pytest.raises(ExtensionInstallError):
        install_extension(str(src), extensions_dir=extensions_dir, name="sample_extension")
    assert not (extensions_dir / "core" / "sample_extension").exists()


@pytest.mark.django_db
def test_install_extension_cleans_up_folder_when_db_insert_fails(tmp_path, monkeypatch):
    # Arrange — manifest/apps.py are valid, but the DB insert itself fails
    # (e.g. transient DB error, or a pre-existing row conflict) after the
    # folder has already been copied.
    src = _write_sample_extension(tmp_path / "src")
    extensions_dir = tmp_path / "extensions"

    def failing_create(*args, **kwargs):
        raise Exception("simulated DB failure")

    monkeypatch.setattr(InstalledExtension.objects, "create", failing_create)

    # Act / Assert
    with pytest.raises(ExtensionInstallError):
        install_extension(str(src), extensions_dir=extensions_dir, name="sample_extension")
    assert not (extensions_dir / "core" / "sample_extension").exists()


@pytest.mark.django_db
def test_install_extension_rejects_when_target_already_exists(tmp_path):
    # Arrange
    src = _write_sample_extension(tmp_path / "src")
    extensions_dir = tmp_path / "extensions"
    install_extension(str(src), extensions_dir=extensions_dir, name="sample_extension")

    # Act / Assert — no silent overwrite
    with pytest.raises(ExtensionInstallError):
        install_extension(str(src), extensions_dir=extensions_dir, name="sample_extension")
