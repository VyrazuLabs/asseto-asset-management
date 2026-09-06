import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

# Sensitive/restricted Google scopes — see plan doc for the OAuth
# verification requirement this implies for production use.
SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/firebase",
]

STATE_SESSION_KEY = "google_oauth_state"


def build_authorization_url(request) -> str:
    """Build the Google OAuth consent URL and stash a CSRF `state` in session.

    Args:
        request: the current Django request (used to store `state` in
            `request.session`, unlike the existing Slack flow which
            correlates callbacks via a loosely-keyed cache entry).

    Returns:
        Full URL to redirect the superadmin's browser to.
    """
    state = secrets.token_urlsafe(32)
    request.session[STATE_SESSION_KEY] = state

    params = {
        "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",  # force refresh_token issuance even on repeat consent
        "state": state,
    }
    return f"{AUTHORIZATION_URL}?{urlencode(params)}"


def verify_state(request) -> bool:
    """Validate the callback's `state` param against the session-stored value.

    Args:
        request: the callback request, expected to carry `?state=...`.

    Returns:
        True if the state matches and has been consumed; False otherwise.
    """
    expected = request.session.pop(STATE_SESSION_KEY, None)
    received = request.GET.get("state")
    return bool(expected) and secrets.compare_digest(expected, received or "")


def exchange_code_for_tokens(code: str) -> dict:
    """Exchange an OAuth authorization code for access/refresh tokens.

    Args:
        code: the `code` query param Google redirected back with.

    Returns:
        Parsed JSON token response (access_token, refresh_token, scope, expires_in).

    Raises:
        requests.HTTPError: If Google's token endpoint returns a non-2xx status.
    """
    response = requests.post(
        TOKEN_URL,
        data={
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
            "code": code,
            "redirect_uri": settings.GOOGLE_OAUTH_REDIRECT_URI,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json()
