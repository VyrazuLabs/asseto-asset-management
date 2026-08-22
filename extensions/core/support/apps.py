from django.apps import AppConfig


class SupportConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    # Moved into extensions/core/ (docs/extension-architecture.md §7) — name
    # is the new import path, but label is left to default to "support"
    # (Django derives it from name's last component), preserving the
    # original app_label so existing applied migrations still match.
    name = "extensions.core.support"
