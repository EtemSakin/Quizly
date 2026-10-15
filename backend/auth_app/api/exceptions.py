"""Authentication API exceptions for Quizly."""

from rest_framework.exceptions import APIException


class Unauthorized(APIException):
    """Return an explicit HTTP 401 authentication response."""

    status_code = 401
    default_detail = "Authentication failed."
    default_code = "authentication_failed"
