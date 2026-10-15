"""Serializers for Quizly quiz endpoints."""

from rest_framework import serializers

from quiz_app.models import Question, Quiz


class QuestionSerializer(serializers.ModelSerializer):
    """Serialize quiz questions as read-only nested data."""

    class Meta:
        """Expose the question fields used by the official frontend."""

        model = Question
        fields = ["id", "question_title", "question_options", "answer"]
        read_only_fields = fields


class QuizSerializer(serializers.ModelSerializer):
    """Serialize quiz data while limiting editable fields."""

    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        """Allow only title and description to be changed through CRUD."""

        model = Quiz
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "video_url",
            "questions",
        ]
