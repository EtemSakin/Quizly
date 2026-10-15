"""Helpers for Quizly JWT creation, refresh, blacklist, and cookies."""

from django.conf import settings
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.api.exceptions import Unauthorized

ACCESS_COOKIE = "access_token"
REFRESH_COOKIE = "refresh_token"


def create_token_pair(user):
    """Create access and refresh JWT strings for a user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def _cookie_max_age(lifetime):
    """Convert a SimpleJWT token lifetime to cookie seconds."""
    return int(lifetime.total_seconds())


def _set_cookie(response, name, value, lifetime):
    """Set one HttpOnly authentication cookie."""
    response.set_cookie(
        key=name,
        value=value,
        max_age=_cookie_max_age(lifetime),
        httponly=True,
        secure=settings.JWT_COOKIE_SECURE,
        samesite=settings.JWT_COOKIE_SAMESITE,
        path="/",
    )


def set_auth_cookies(response, user):
    """Set fresh access and refresh cookies on a response."""
    access_token, refresh_token = create_token_pair(user)
    _set_cookie(response, ACCESS_COOKIE, access_token, api_settings.ACCESS_TOKEN_LIFETIME)
    _set_cookie(
        response,
        REFRESH_COOKIE,
        refresh_token,
        api_settings.REFRESH_TOKEN_LIFETIME,
    )
    return response


def set_access_cookie(response, access_token):
    """Set a refreshed access-token cookie."""
    _set_cookie(
        response,
        ACCESS_COOKIE,
        access_token,
        api_settings.ACCESS_TOKEN_LIFETIME,
    )
    return response


def delete_auth_cookies(response):
    """Expire both Quizly authentication cookies."""
    for cookie_name in (ACCESS_COOKIE, REFRESH_COOKIE):
        response.delete_cookie(
            cookie_name,
            path="/",
            samesite=settings.JWT_COOKIE_SAMESITE,
        )
    return response


def _get_refresh_token(request):
    """Read the refresh token or raise an authentication error."""
    token = request.COOKIES.get(REFRESH_COOKIE)
    if token is None:
        raise Unauthorized("Refresh token missing.")
    return token


def refresh_access_token(request):
    """Validate the refresh cookie and return a new access token."""
    try:
        refresh = RefreshToken(_get_refresh_token(request))
        return str(refresh.access_token)
    except TokenError as error:
        raise Unauthorized("Invalid refresh token.") from error


def blacklist_refresh_token(request):
    """Blacklist the refresh cookie when a valid token is available."""
    token = request.COOKIES.get(REFRESH_COOKIE)
    if token is None:
        return
    try:
        RefreshToken(token).blacklist()
    except TokenError:
        return


def user_payload(user):
    """Return the user structure required by the login response."""
    return {"id": user.id, "username": user.username, "email": user.email}
