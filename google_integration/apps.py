from django.apps import AppConfig


class GoogleIntegrationConfig(AppConfig):
    """Owns instance-wide Google Cloud / Firebase provisioning.

    Deliberately does nothing at startup (`ready()` stays a no-op) — the
    Firebase Admin SDK must only ever be initialized lazily, on first real
    use, via `google_integration.firebase_admin_client.get_firebase_admin_app()`.
    Initializing anything here would reintroduce the settings-import-time
    coupling this app exists to remove.
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "google_integration"
