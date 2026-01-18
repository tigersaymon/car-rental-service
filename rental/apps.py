from django.apps import AppConfig


class RentalConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rental"

    def ready(self) -> None:
        """Import signals when the app is ready."""
        import rental.signals  # noqa
