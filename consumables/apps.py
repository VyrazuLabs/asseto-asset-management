from django.apps import AppConfig


class ConsumablesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "consumables"

    def ready(self):
        import consumables.signals
