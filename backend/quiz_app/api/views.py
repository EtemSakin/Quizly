"""Views for Quizly quiz endpoints."""

import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from quiz_app.api.permissions import IsQuizOwner
from quiz_app.api.serializers import QuizCreateSerializer, QuizSerializer
from quiz_app.models import Quiz
from quiz_app.services.generation import generate_quiz

logger = logging.getLogger(__name__)


class QuizViewSet(ModelViewSet):
    """Provide authenticated quiz creation, listing, updates, and deletion."""

    serializer_class = QuizSerializer
    permission_classes = [IsAuthenticated, IsQuizOwner]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_queryset(self):
        """Return owner-only lists and preserve 403 for foreign details."""
        queryset = (
            Quiz.objects.select_related("user").prefetch_related("questions")
        )
        if self.action == "list":
            return queryset.filter(user=self.request.user)
        return queryset

    def get_serializer_class(self):
        """Require only a video URL when creating generated quizzes."""
        if self.action == "create":
            return QuizCreateSerializer
        return QuizSerializer

    def create(self, request, *args, **kwargs):
        """Create and serialize a complete AI-generated quiz."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            quiz = generate_quiz(
                request.user, serializer.validated_data["url"]
            )
        except Exception:
            logger.exception("Quiz generation failed.")
            return Response({"detail": "Quiz generation failed."}, status=500)
        return Response(
            QuizSerializer(quiz).data, status=status.HTTP_201_CREATED
        )
