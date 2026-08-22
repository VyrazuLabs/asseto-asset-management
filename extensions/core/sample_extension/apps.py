from django.apps import AppConfig


class SampleExtensionConfig(AppConfig):
    """Minimal proof-of-concept extension used to verify the loader end-to-end."""

    default_auto_field = "django.db.models.BigAutoField"
    label = "ext_sample_extension"
    name = "extensions.core.sample_extension"
