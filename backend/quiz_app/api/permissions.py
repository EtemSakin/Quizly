"""Object-level permissions for Quizly quiz resources."""

from rest_framework.permissions import BasePermission


class IsQuizOwner(BasePermission):
    """Allow access only to the user who owns a quiz."""

    message = "You do not have permission to access this quiz."

    def has_object_permission(self, request, view, obj):
        """Return whether the authenticated user owns the quiz."""
        return obj.user_id == request.user.id
