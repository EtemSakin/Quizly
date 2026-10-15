"""Views for Quizly quiz endpoints."""

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from quiz_app.api.permissions import IsQuizOwner
from quiz_app.api.serializers import QuizSerializer
from quiz_app.models import Quiz


class QuizViewSet(ModelViewSet):
    """Provide authenticated quiz list, detail, update, and delete actions."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsQuizOwner]
    http_method_names = ["get", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Limit lists to the owner while preserving 403 for foreign details."""
        queryset = Quiz.objects.select_related("user").prefetch_related("questions")
        if self.action == "list":
            return queryset.filter(user=self.request.user)
        return queryset
