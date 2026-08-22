"""Tests for extension manifest.json validation.

Covers configurations.extensions.manifest.validate_manifest — the gate that
prevents install_extension/enable_extension from registering a malformed or
misdeclared extension, per docs/extension-architecture.md §1/§5.
"""

from configurations.extensions.manifest import ManifestValidationError, validate_manifest


def _valid_manifest(**overrides):
    data = {
        "name": "sample_extension",
        "version": "1.0.0",
        "app_label": "ext_sample_extension",
        "entry_app": "extensions.core.sample_extension",
        "license_required": False,
    }
    data.update(overrides)
    return data


def test_validate_manifest_accepts_well_formed_manifest():
    # Arrange
    manifest = _valid_manifest()

    # Act / Assert — should not raise
    validate_manifest(manifest)


def test_validate_manifest_rejects_missing_required_key():
    # Arrange
    manifest = _valid_manifest()
    del manifest["version"]

    # Act / Assert
    try:
        validate_manifest(manifest)
        assert False, "expected ManifestValidationError"
    except ManifestValidationError as exc:
        assert "version" in str(exc)


def test_validate_manifest_rejects_unknown_extra_key():
    # Arrange
    manifest = _valid_manifest(unexpected_key="smuggled")

    # Act / Assert
    try:
        validate_manifest(manifest)
        assert False, "expected ManifestValidationError"
    except ManifestValidationError as exc:
        assert "unexpected_key" in str(exc)


def test_validate_manifest_accepts_app_label_without_ext_prefix():
    # Arrange — apps moved into extensions/core/ from the original codebase
    # (e.g. "support") keep their original Django app_label to preserve
    # migration history; the "ext_" prefix is a naming convention for new
    # extensions, not an enforced requirement.
    manifest = _valid_manifest(app_label="support")

    # Act / Assert — should not raise
    validate_manifest(manifest)


def test_validate_manifest_rejects_invalid_app_label_characters():
    # Arrange
    manifest = _valid_manifest(app_label="Not-A-Valid-Label!")

    # Act / Assert
    try:
        validate_manifest(manifest)
        assert False, "expected ManifestValidationError"
    except ManifestValidationError as exc:
        assert "app_label" in str(exc)


def test_validate_manifest_rejects_entry_app_not_matching_name():
    # Arrange — entry_app must be extensions.core.<name> or extensions.<name>
    manifest = _valid_manifest(entry_app="extensions.core.other_name")

    # Act / Assert
    try:
        validate_manifest(manifest)
        assert False, "expected ManifestValidationError"
    except ManifestValidationError as exc:
        assert "entry_app" in str(exc)


def test_validate_manifest_accepts_override_style_entry_app():
    # Arrange — bare "extensions.<name>" is valid for an override/standalone extension
    manifest = _valid_manifest(entry_app="extensions.sample_extension")

    # Act / Assert — should not raise
    validate_manifest(manifest)


def test_validate_manifest_reports_every_violation_not_just_first():
    # Arrange — two independent violations at once
    manifest = _valid_manifest(app_label="Not Valid!")
    del manifest["version"]

    # Act / Assert
    try:
        validate_manifest(manifest)
        assert False, "expected ManifestValidationError"
    except ManifestValidationError as exc:
        message = str(exc)
        assert "version" in message
        assert "app_label" in message
