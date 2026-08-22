"""Tests for configurations.extensions.license_client.

Thin HTTP client for the external license server's /activate and
/validate endpoints (contract per docs/extension-architecture.md §5 — the
server itself is a separate project, not built here). http_post is
injected so these tests never make a real network call.
"""

import pytest

from configurations.extensions.license_client import (
    LicenseServerError,
    activate,
    validate,
)


class _FakeResponse:
    def __init__(self, status_code, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


def test_activate_posts_expected_payload_and_returns_token():
    # Arrange
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse(200, {"activation_token": "tok-123", "valid_until": "2027-01-01T00:00:00Z"})

    # Act
    result = activate(
        base_url="https://license.example.com",
        org_id="org-1",
        domain="asseto.example.com",
        license_key="KEY-ABC",
        extension_name="paid_extension",
        http_post=fake_post,
    )

    # Assert
    assert result == {"activation_token": "tok-123", "valid_until": "2027-01-01T00:00:00Z"}
    assert captured["url"] == "https://license.example.com/activate"
    assert captured["json"] == {
        "org_id": "org-1",
        "domain": "asseto.example.com",
        "license_key": "KEY-ABC",
        "extension_name": "paid_extension",
    }


def test_activate_raises_on_non_200():
    # Arrange
    def fake_post(url, json, timeout):
        return _FakeResponse(403, {"error": "invalid license key"})

    # Act / Assert
    with pytest.raises(LicenseServerError):
        activate(
            base_url="https://license.example.com",
            org_id="org-1",
            domain="asseto.example.com",
            license_key="BAD-KEY",
            extension_name="paid_extension",
            http_post=fake_post,
        )


def test_validate_posts_token_and_returns_status():
    # Arrange
    captured = {}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _FakeResponse(200, {"status": "active", "valid_until": "2027-01-01T00:00:00Z"})

    # Act
    result = validate(base_url="https://license.example.com", activation_token="tok-123", http_post=fake_post)

    # Assert
    assert result == {"status": "active", "valid_until": "2027-01-01T00:00:00Z"}
    assert captured["url"] == "https://license.example.com/validate"
    assert captured["json"] == {"activation_token": "tok-123"}


def test_validate_raises_on_non_200():
    # Arrange
    def fake_post(url, json, timeout):
        return _FakeResponse(500, {"error": "server error"})

    # Act / Assert
    with pytest.raises(LicenseServerError):
        validate(base_url="https://license.example.com", activation_token="tok-123", http_post=fake_post)
