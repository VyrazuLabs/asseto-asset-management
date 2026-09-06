from django.conf import settings
from django.db import models

from .fields import EncryptedTextField


class GoogleCloudFirebaseConfig(models.Model):
    """Single, instance-wide record of the auto-provisioned Firebase project.

    Deliberately global, not per-organization — every other model in
    `configurations` carries an `organization` FK; this one doesn't, because
    push-notification delivery is one Firebase project per Asseto
    installation, not one per tenant. `pk=1` is enforced via a fixed default,
    so the table can only ever hold one row without extra validation.

    Not using `simple_history.HistoricalRecords` here on purpose — historical
    snapshots would duplicate encrypted secrets into a second table.
    """

    id = models.PositiveSmallIntegerField(primary_key=True, default=1)

    is_connected = models.BooleanField(default=False)

    gcp_project_id = models.CharField(max_length=100, blank=True, null=True)
    gcp_project_number = models.CharField(max_length=100, blank=True, null=True)
    firebase_web_app_id = models.CharField(max_length=150, blank=True, null=True)

    # Web config — Firebase's own documented stance is that these are public
    # identifiers, not secrets (https://firebase.google.com/docs/projects/api-keys),
    # so plain columns are fine; they get rendered straight into client-side JS.
    web_api_key = models.CharField(max_length=150, blank=True, null=True)
    web_auth_domain = models.CharField(max_length=150, blank=True, null=True)
    web_project_id = models.CharField(max_length=100, blank=True, null=True)
    web_storage_bucket = models.CharField(max_length=150, blank=True, null=True)
    web_messaging_sender_id = models.CharField(max_length=100, blank=True, null=True)
    web_app_id = models.CharField(max_length=150, blank=True, null=True)
    web_vapid_key = models.CharField(max_length=150, blank=True, null=True)

    # Secrets — Fernet-encrypted at rest via EncryptedTextField.
    encrypted_service_account_json = EncryptedTextField(blank=True, null=True)
    encrypted_oauth_refresh_token = EncryptedTextField(blank=True, null=True)

    oauth_token_scopes = models.TextField(blank=True, null=True)
    connected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )
    connected_at = models.DateTimeField(blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Google Cloud/Firebase config (connected={self.is_connected})"

    @classmethod
    def load(cls) -> "GoogleCloudFirebaseConfig":
        """Return the singleton row, creating an empty one if none exists yet."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
