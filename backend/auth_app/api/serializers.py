"""Serializers for Quizly authentication endpoints."""

import re

from django.contrib.auth import authenticate, get_user_model
from rest_framework import serializers

from auth_app.api.exceptions import Unauthorized

User = get_user_model()
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{6,}$")


class RegisterSerializer(serializers.ModelSerializer):
    """Validate and create a Quizly user account."""

    email = serializers.EmailField(required=True, allow_blank=False)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        """Configure fields accepted by the registration endpoint."""

        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """Reject email addresses that are already registered."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Email is already in use.")
        return value

    def validate_password(self, value):
        """Apply the password rules used by the official frontend."""
        if not PASSWORD_PATTERN.fullmatch(value):
            raise serializers.ValidationError(
                "Password needs 6 characters, upper/lower case and a number."
            )
        return value

    def validate(self, attrs):
        """Ensure both submitted password fields match."""
        if attrs["password"] != attrs["confirmed_password"]:
            error = {"confirmed_password": "Passwords differ."}
            raise serializers.ValidationError(error)
        return attrs

    def create(self, validated_data):
        """Create the user with Django's password hashing."""
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validate username and password without revealing which value failed."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate the submitted credentials."""
        user = authenticate(
            username=attrs["username"],
            password=attrs["password"],
        )
        if user is None:
            raise Unauthorized("Invalid username or password.")
        attrs["user"] = user
        return attrs
