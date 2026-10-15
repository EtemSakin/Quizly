"""Views for Quizly authentication endpoints."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import LoginSerializer, RegisterSerializer
from auth_app.api.utils import (
    blacklist_refresh_token,
    delete_auth_cookies,
    refresh_access_token,
    set_access_cookie,
    set_auth_cookies,
    user_payload,
)


class RegisterView(APIView):
    """Create a new Quizly user account."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Register a user after validating the submitted account data."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate a user and set JWT HttpOnly cookies."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Validate credentials and return the documented login payload."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        response = Response(
            {"detail": "Login successfully!", "user": user_payload(user)},
            status=status.HTTP_200_OK,
        )
        return set_auth_cookies(response, user)


class TokenRefreshView(APIView):
    """Issue a new access token from the refresh-token cookie."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """Refresh the access-token cookie."""
        access_token = refresh_access_token(request)
        response = Response(
            {"detail": "Token refreshed"},
            status=status.HTTP_200_OK,
        )
        return set_access_cookie(response, access_token)


class LogoutView(APIView):
    """Blacklist the refresh token and remove authentication cookies."""

    def post(self, request):
        """Log out the authenticated user."""
        blacklist_refresh_token(request)
        response = Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted."},
            status=status.HTTP_200_OK,
        )
        return delete_auth_cookies(response)
