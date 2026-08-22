"""Validation for extension manifest.json files.

An extension's manifest.json declares what it is (name, version, app label,
entry point) before install_extension/enable_extension act on it. Validation
is fail-closed and hand-rolled — no jsonschema dependency, per the scope cut
in docs/extension-architecture.md §1.
"""

import re

REQUIRED_KEYS = {"name", "version", "app_label", "entry_app", "license_required"}
ALLOWED_KEYS = REQUIRED_KEYS

NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
# Not "ext_"-prefixed: an app moved into extensions/core/ from the original
# codebase (e.g. "support") must keep its original Django app_label to
# preserve migration history — renaming it would orphan applied migrations.
# "ext_" is a naming convention new extensions are encouraged to follow,
# not an enforced requirement. See docs/extension-architecture.md §7 (Stage 7).
APP_LABEL_RE = re.compile(r"^[a-z][a-z0-9_]*$")
VERSION_RE = re.compile(r"^\d+\.\d+\.\d+$")


class ManifestValidationError(Exception):
    """Raised when a manifest.json fails validation.

    Carries every violation found, not just the first, so a single failed
    run reports the full checklist to fix.
    """

    def __init__(self, violations):
        self.violations = violations
        super().__init__("; ".join(violations))


def validate_manifest(data: dict) -> None:
    """Validate an extension manifest dict.

    Args:
        data: parsed manifest.json contents.

    Raises:
        ManifestValidationError: listing every violation found, if any.
    """
    violations = []

    missing = REQUIRED_KEYS - data.keys()
    for key in sorted(missing):
        violations.append(f"missing required key: {key}")

    extra = data.keys() - ALLOWED_KEYS
    for key in sorted(extra):
        violations.append(f"unexpected_key not allowed: {key}")

    name = data.get("name")
    if name is not None and not NAME_RE.match(name):
        violations.append(f"name '{name}' must match {NAME_RE.pattern}")

    app_label = data.get("app_label")
    if app_label is not None and not APP_LABEL_RE.match(app_label):
        violations.append(f"app_label '{app_label}' must match {APP_LABEL_RE.pattern}")

    version = data.get("version")
    if version is not None and not VERSION_RE.match(version):
        violations.append(f"version '{version}' must be semver-like (X.Y.Z)")

    entry_app = data.get("entry_app")
    if entry_app is not None and name is not None:
        expected_core = f"extensions.core.{name}"
        expected_override = f"extensions.{name}"
        if entry_app not in (expected_core, expected_override):
            violations.append(
                f"entry_app '{entry_app}' must be '{expected_core}' or '{expected_override}'"
            )

    if violations:
        raise ManifestValidationError(violations)
