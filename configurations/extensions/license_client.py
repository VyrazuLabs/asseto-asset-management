"""HTTP client for the external license server's /activate and /validate endpoints.

The license server itself is a separate project — this repo only ships
this client. Contract (docs/extension-architecture.md §5, open item):

    POST {base_url}/activate
        {"org_id", "domain", "license_key", "extension_name"}
        -> 200 {"activation_token", "valid_until"}

    POST {base_url}/validate
        {"activation_token"}
        -> 200 {"status": "active"|"invalid"|"revoked", "valid_until"}

http_post is injected (defaults to requests.post) so callers can test
without a real network call.
"""

import requests

DEFAULT_TIMEOUT_SECONDS = 10


class LicenseServerError(Exception):
    """Raised when the license server returns a non-200 response."""


def activate(base_url, org_id, domain, license_key, extension_name, http_post=requests.post):
    """Call POST {base_url}/activate.

    Returns:
        dict with "activation_token" and "valid_until".

    Raises:
        LicenseServerError: on a non-200 response.
    """
    response = http_post(
        f"{base_url}/activate",
        json={
            "org_id": org_id,
            "domain": domain,
            "license_key": license_key,
            "extension_name": extension_name,
        },
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise LicenseServerError(f"activate failed ({response.status_code}): {response.json()}")
    return response.json()


def validate(base_url, activation_token, http_post=requests.post):
    """Call POST {base_url}/validate.

    Returns:
        dict with "status" and "valid_until".

    Raises:
        LicenseServerError: on a non-200 response.
    """
    response = http_post(
        f"{base_url}/validate",
        json={"activation_token": activation_token},
        timeout=DEFAULT_TIMEOUT_SECONDS,
    )
    if response.status_code != 200:
        raise LicenseServerError(f"validate failed ({response.status_code}): {response.json()}")
    return response.json()
