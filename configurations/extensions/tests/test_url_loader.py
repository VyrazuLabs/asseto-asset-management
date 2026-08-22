"""Tests for the pure name/namespace derivation used to wire extension URLs.

configurations.extensions.url_loader.extension_url_parts turns an app import
path from registry.json ("extensions.core.sample_extension" or
"extensions.sample_extension") into the /ext/<name>/ prefix and namespace
used when including that extension's urls.py in AssetManagement/urls.py,
per docs/extension-architecture.md §2/§9. Kept pure/testable — the actual
django.urls.include() wiring is exercised by the sample_extension
integration check, not unit tests.
"""

from configurations.extensions.url_loader import extension_url_parts


def test_extension_url_parts_derives_name_from_core_app_path():
    # Act
    prefix, namespace = extension_url_parts("extensions.core.sample_extension")

    # Assert
    assert prefix == "ext/sample_extension/"
    assert namespace == "ext_sample_extension"


def test_extension_url_parts_derives_name_from_override_app_path():
    # Act
    prefix, namespace = extension_url_parts("extensions.sample_extension")

    # Assert
    assert prefix == "ext/sample_extension/"
    assert namespace == "ext_sample_extension"
