"""Application configuration for the quiz app."""

from django.apps import AppConfig


class QuizAppConfig(AppConfig):
    """Configure the quiz application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "quiz_app"
