"""Application configuration for the authentication app."""

from django.apps import AppConfig


class AuthAppConfig(AppConfig):
    """Configure the authentication application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "auth_app"
