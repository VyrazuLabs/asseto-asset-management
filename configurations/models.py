import uuid
import base64
import binascii

from django.db import models
from dashboard.models import Organization
from authentication.models import User


class BrandingImages(models.Model):

    logo_path = "/logo/"
    favicon_path = "/favicon/"
    login_page_logo_path = "/login_page_logo/"

    id = models.AutoField(primary_key=True)
    logo = models.TextField(max_length=255, null=True)
    favicon = models.TextField(max_length=255, null=True)
    login_page_logo = models.TextField(
        max_length=255,
        null=True,
    )
    organization = models.ForeignKey(
        Organization,
        null=True,
        on_delete=models.CASCADE,
        related_name="organization_logo",
    )


class TagConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    prefix = models.CharField(max_length=50, blank=True, null=True)
    number_suffix = models.CharField(max_length=50, blank=True, null=True)
    use_default_settings = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.organization.name} - {self.prefix}"


class LocalizationConfiguration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization, models.DO_NOTHING, blank=True, null=True
    )
    date_format = models.IntegerField(blank=True, null=True)
    time_format = models.IntegerField(blank=True, null=True)
    timezone = models.IntegerField(blank=True, null=True)
    currency = models.IntegerField(blank=True, null=True)
    name_display_format = models.IntegerField(blank=True, null=True)
    country_format = models.IntegerField(blank=True, null=True)
    default_language = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.organization.name} - Localization Settings"


class Extensions(models.Model):
    STATUS_CHOICES = [(0, "Inactive"), (1, "Active")]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    description = models.TextField(blank=True, null=True)
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="integrations"
    )
    entity_name = models.CharField(
        max_length=150,
    )
    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    payment_date = models.DateTimeField(auto_now_add=True)
    validity = models.IntegerField(default=0)


class SlackConfiguration(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="slack_configuration"
    )
    slack_user_id = models.CharField(max_length=100, null=True, blank=True)
    access_token = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    team_id = models.CharField(max_length=100, null=True, blank=True)
    channel_id = models.CharField(max_length=100, null=True, blank=True)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    client_secret = models.CharField(max_length=100, null=True, blank=True)


class InstalledExtension(models.Model):
    """Platform-level record of an installed extension.

    Org-agnostic — an extension is installed once per deployment (unlike
    ``Extensions`` above, which is a per-org feature toggle). Maintained by
    the install_extension/enable_extension/disable_extension management
    commands, never edited directly. See docs/extension-architecture.md §6.
    """

    STATUS_CHOICES = [
        ("installed", "Installed"),
        ("pending_restart", "Pending Restart"),
        ("active", "Active"),
        ("disabled", "Disabled"),
        ("error", "Error"),
    ]
    SOURCE_CHOICES = [("local", "Local"), ("github", "GitHub")]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    app_label = models.CharField(max_length=100, unique=True)
    version = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="installed")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES)
    source_url = models.CharField(max_length=500, null=True, blank=True)
    manifest_json = models.JSONField()
    installed_at = models.DateTimeField(auto_now_add=True)
    enabled_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.status})"


class ExtensionLicense(models.Model):
    """Per-org activation state for a paid extension.

    Activated via `python manage.py activate_extension` against an external
    license server (out of this repo — see docs/extension-architecture.md
    §5) and re-validated daily by a Celery beat task. `require_license()`
    (configurations.extensions.license) checks this table before letting a
    licensed extension do gated work.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("expired", "Expired"),
        ("invalid", "Invalid"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    extension = models.ForeignKey(
        InstalledExtension, on_delete=models.CASCADE, related_name="licenses"
    )
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    activation_token = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="invalid")
    valid_until = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.extension.name} - {self.organization.name} ({self.status})"
