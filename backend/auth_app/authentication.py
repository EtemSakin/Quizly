"""JWT authentication backed by Quizly's HttpOnly access-token cookie."""

from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Authenticate a request with the JWT stored in ``access_token``."""

    def authenticate(self, request):
        """Return the authenticated user and token from the access cookie."""
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token
