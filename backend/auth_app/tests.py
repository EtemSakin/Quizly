"""Tests for Quizly authentication functionality."""

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken

from auth_app.api.utils import ACCESS_COOKIE, REFRESH_COOKIE

User = get_user_model()


class RegistrationTests(APITestCase):
    """Cover successful and invalid registration requests."""

    def setUp(self):
        """Prepare a valid registration payload."""
        self.url = reverse("register")
        self.payload = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "Strong1",
            "confirmed_password": "Strong1",
        }

    def test_registration_creates_user(self):
        """Create a user and return the documented response."""
        response = self.client.post(self.url, self.payload, format="json")
        user = User.objects.get(username="newuser")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data, {"detail": "User created successfully!"}
        )
        self.assertTrue(user.check_password("Strong1"))

    def test_registration_rejects_password_mismatch(self):
        """Reject a confirmation password that does not match."""
        self.payload["confirmed_password"] = "Other1"
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_duplicate_username(self):
        """Reject an already registered username."""
        User.objects.create_user("newuser", "first@example.com", "Strong1")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_rejects_duplicate_email(self):
        """Reject an already registered email address."""
        User.objects.create_user("other", "new@example.com", "Strong1")
        response = self.client.post(self.url, self.payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTests(APITestCase):
    """Cover login, refresh, cookie authentication, and logout."""

    def setUp(self):
        """Create a user used by authentication tests."""
        self.user = User.objects.create_user(
            username="tester",
            email="tester@example.com",
            password="Strong1",
        )
        self.credentials = {"username": "tester", "password": "Strong1"}

    def _login(self):
        """Log in with the valid test credentials."""
        return self.client.post(
            reverse("login"), self.credentials, format="json"
        )

    def test_login_sets_http_only_cookies(self):
        """Set both JWT cookies and return the documented user data."""
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(ACCESS_COOKIE, response.cookies)
        self.assertIn(REFRESH_COOKIE, response.cookies)
        self.assertTrue(response.cookies[ACCESS_COOKIE]["httponly"])
        self.assertEqual(response.data["user"]["username"], "tester")

    def test_login_rejects_invalid_credentials(self):
        """Return 401 without revealing which credential was invalid."""
        self.credentials["password"] = "Wrong1"
        response = self._login()
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(
            response.data["detail"], "Invalid username or password."
        )

    def test_refresh_sets_new_access_cookie(self):
        """Use the refresh cookie to issue an access cookie."""
        self._login()
        response = self.client.post(
            reverse("token-refresh"), {}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(ACCESS_COOKIE, response.cookies)
        self.assertEqual(response.data, {"detail": "Token refreshed"})

    def test_refresh_without_cookie_returns_401(self):
        """Reject refresh requests without a refresh cookie."""
        client = APIClient()
        response = client.post(reverse("token-refresh"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_blacklists_refresh_and_deletes_cookies(self):
        """Blacklist refresh JWT and expire both browser cookies."""
        self._login()
        refresh_value = self.client.cookies[REFRESH_COOKIE].value
        jti = RefreshToken(refresh_value)["jti"]
        response = self.client.post(reverse("logout"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(
            BlacklistedToken.objects.filter(token__jti=jti).exists()
        )
        self.assertEqual(response.cookies[ACCESS_COOKIE].value, "")
        self.assertEqual(response.cookies[REFRESH_COOKIE].value, "")

    def test_logout_without_access_cookie_returns_401(self):
        """Protect logout with access-cookie authentication."""
        client = APIClient()
        response = client.post(reverse("logout"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
