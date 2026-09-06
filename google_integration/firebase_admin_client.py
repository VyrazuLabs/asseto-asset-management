import json
import threading

import firebase_admin
from firebase_admin import credentials

from .models import GoogleCloudFirebaseConfig

_lock = threading.Lock()
_cached_app = None


class GoogleCloudNotConfiguredError(Exception):
    """Raised when Firebase Admin is used before Google Cloud has been connected.

    Callers (notification send paths) must catch this specifically and skip
    push delivery rather than let it crash the rest of the notification
    pipeline (email/Slack must still go out).
    """


def get_firebase_admin_app() -> firebase_admin.App:
    """Lazily initialize and cache the Firebase Admin SDK app for this process.

    Reads the singleton `GoogleCloudFirebaseConfig` row, decrypts its stored
    service account JSON, and calls `firebase_admin.initialize_app()` on
    first use only — never at Django settings-import time, so this is safe
    to import from anywhere, including before migrations have created the
    table (the DB read simply happens on first real call, not at module load).

    Returns:
        The initialized (or cached) `firebase_admin.App` instance.

    Raises:
        GoogleCloudNotConfiguredError: If no config row exists, or Google
            Cloud has not been connected yet.
    """
    global _cached_app
    if _cached_app is not None:
        return _cached_app

    with _lock:
        if _cached_app is not None:
            return _cached_app

        config = GoogleCloudFirebaseConfig.objects.filter(pk=1, is_connected=True).first()
        if not config or not config.encrypted_service_account_json:
            raise GoogleCloudNotConfiguredError(
                "Google Cloud is not connected yet — visit Settings > Extensions "
                "> Firebase and click Connect."
            )

        cred_dict = json.loads(config.encrypted_service_account_json)
        cred = credentials.Certificate(cred_dict)
        _cached_app = firebase_admin.initialize_app(cred)
        return _cached_app


def reset_cached_app() -> None:
    """Clear the cached app — used after a reconnect, and in tests.

    Also tears down firebase_admin's own default-app registry entry, since
    `initialize_app()` raises if called again while a default app already
    exists there.
    """
    global _cached_app
    with _lock:
        if _cached_app is not None:
            firebase_admin.delete_app(_cached_app)
        _cached_app = None
