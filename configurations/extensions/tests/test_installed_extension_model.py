"""Tests for configurations.models.InstalledExtension.

The platform-level record of an installed/enabled extension — org-agnostic
(installed once per deployment, unlike the existing per-org Extensions
toggle model), per docs/extension-architecture.md §3/§6.
"""

import pytest

from configurations.models import InstalledExtension


@pytest.mark.django_db
def test_installed_extension_creates_with_defaults():
    # Act
    ext = InstalledExtension.objects.create(
        name="sample_extension",
        app_label="ext_sample_extension",
        version="1.0.0",
        source="local",
        manifest_json={"name": "sample_extension"},
    )

    # Assert
    assert ext.pk is not None
    assert ext.status == "installed"


@pytest.mark.django_db
def test_installed_extension_name_is_unique():
    # Arrange
    InstalledExtension.objects.create(
        name="sample_extension",
        app_label="ext_sample_extension",
        version="1.0.0",
        source="local",
        manifest_json={},
    )

    # Act / Assert
    with pytest.raises(Exception):
        InstalledExtension.objects.create(
            name="sample_extension",
            app_label="ext_sample_extension_2",
            version="1.0.0",
            source="local",
            manifest_json={},
        )
