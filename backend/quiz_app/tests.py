"""Tests for Quizly quiz functionality."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase

from quiz_app.models import Question, Quiz

User = get_user_model()


class QuizModelTests(TestCase):
    """Cover quiz and question model behavior."""

    @classmethod
    def setUpTestData(cls):
        """Create one user, quiz, and question shared by model tests."""
        cls.user = User.objects.create_user("owner", password="Strong1")
        cls.quiz = cls._create_quiz()
        cls.question = cls._create_question()

    @classmethod
    def _create_quiz(cls):
        """Create the quiz fixture owned by the test user."""
        return Quiz.objects.create(
            user=cls.user,
            title="Sample Quiz",
            description="A generated quiz.",
            video_url="https://www.youtube.com/watch?v=abcdefghijk",
        )

    @classmethod
    def _create_question(cls):
        """Create the question fixture linked to the quiz."""
        return Question.objects.create(
            quiz=cls.quiz,
            question_title="Which option is correct?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def test_quiz_belongs_to_user(self):
        """Expose quizzes through the owner's related name."""
        self.assertEqual(self.user.quizzes.get(), self.quiz)

    def test_question_belongs_to_quiz(self):
        """Expose questions through the quiz related name."""
        self.assertEqual(self.quiz.questions.get(), self.question)

    def test_question_options_are_stored_as_list(self):
        """Persist the four answer options as JSON list data."""
        self.assertEqual(self.question.question_options, ["A", "B", "C", "D"])

    def test_deleting_quiz_deletes_questions(self):
        """Delete associated questions when their quiz is deleted."""
        question_id = self.question.id
        self.quiz.delete()
        self.assertFalse(Question.objects.filter(id=question_id).exists())

    def test_model_strings_are_readable(self):
        """Use quiz and question text in admin and debug output."""
        self.assertEqual(str(self.quiz), "Sample Quiz")
        self.assertEqual(str(self.question), "Which option is correct?")

    def test_models_are_registered_in_admin(self):
        """Make quizzes and individual questions editable in admin."""
        self.assertTrue(admin.site.is_registered(Quiz))
        self.assertTrue(admin.site.is_registered(Question))
