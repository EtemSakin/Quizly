"""Tests for Quizly quiz functionality."""

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

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


class QuizApiTests(APITestCase):
    """Cover quiz CRUD responses and ownership rules."""

    @classmethod
    def setUpTestData(cls):
        """Create owned and foreign quiz fixtures."""
        cls.owner = User.objects.create_user("owner-api", password="Strong1")
        cls.other = User.objects.create_user("other-api", password="Strong1")
        cls.owned_quiz = cls._create_quiz(cls.owner, "Owned Quiz")
        cls.foreign_quiz = cls._create_quiz(cls.other, "Foreign Quiz")
        cls.question = cls._create_question(cls.owned_quiz)

    @classmethod
    def _create_quiz(cls, user, title):
        """Create a quiz fixture for one user."""
        return Quiz.objects.create(
            user=user,
            title=title,
            description="Quiz description.",
            video_url="https://www.youtube.com/watch?v=abcdefghijk",
        )

    @classmethod
    def _create_question(cls, quiz):
        """Create one nested question for a quiz fixture."""
        return Question.objects.create(
            quiz=quiz,
            question_title="Question?",
            question_options=["A", "B", "C", "D"],
            answer="A",
        )

    def setUp(self):
        """Authenticate API requests as the quiz owner."""
        self.client.force_authenticate(user=self.owner)

    def _detail_url(self, quiz_id):
        """Return the detail URL for a quiz identifier."""
        return reverse("quiz-detail", args=[quiz_id])

    def test_list_returns_only_owned_quizzes(self):
        """Exclude quizzes owned by other users from the list."""
        response = self.client.get(reverse("quiz-list"))
        quiz_ids = [quiz["id"] for quiz in response.data]
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(quiz_ids, [self.owned_quiz.id])
        self.assertEqual(response.data[0]["questions"][0]["answer"], "A")

    def test_detail_returns_owned_quiz(self):
        """Return the full serialized quiz for its owner."""
        response = self.client.get(self._detail_url(self.owned_quiz.id))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.owned_quiz.id)
        self.assertEqual(response.data["questions"][0]["question_title"], "Question?")

    def test_detail_foreign_quiz_returns_403(self):
        """Distinguish an existing foreign quiz from a missing quiz."""
        response = self.client.get(self._detail_url(self.foreign_quiz.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_detail_missing_quiz_returns_404(self):
        """Return 404 when the requested quiz does not exist."""
        response = self.client.get(self._detail_url(999999))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_patch_updates_title_and_description(self):
        """Allow partial updates of the two editable quiz fields."""
        payload = {"title": "Updated", "description": "New description."}
        response = self.client.patch(self._detail_url(self.owned_quiz.id), payload)
        self.owned_quiz.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.owned_quiz.title, "Updated")
        self.assertEqual(self.owned_quiz.description, "New description.")

    def test_patch_does_not_change_read_only_fields(self):
        """Ignore attempts to replace protected quiz data."""
        original_url = self.owned_quiz.video_url
        payload = {"video_url": "https://example.com/video", "questions": []}
        response = self.client.patch(self._detail_url(self.owned_quiz.id), payload)
        self.owned_quiz.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.owned_quiz.video_url, original_url)
        self.assertEqual(self.owned_quiz.questions.count(), 1)

    def test_patch_foreign_quiz_returns_403(self):
        """Prevent users from editing another user's quiz."""
        response = self.client.patch(
            self._detail_url(self.foreign_quiz.id), {"title": "Blocked"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_owned_quiz_cascades_questions(self):
        """Delete an owned quiz and its related questions."""
        question_id = self.question.id
        response = self.client.delete(self._detail_url(self.owned_quiz.id))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=self.owned_quiz.id).exists())
        self.assertFalse(Question.objects.filter(id=question_id).exists())

    def test_delete_foreign_quiz_returns_403(self):
        """Prevent users from deleting another user's quiz."""
        response = self.client.delete(self._detail_url(self.foreign_quiz.id))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Quiz.objects.filter(id=self.foreign_quiz.id).exists())

    def test_unauthenticated_list_returns_401(self):
        """Require authentication for the quiz collection."""
        response = APIClient().get(reverse("quiz-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unauthenticated_detail_returns_401(self):
        """Require authentication for quiz detail requests."""
        response = APIClient().get(self._detail_url(self.owned_quiz.id))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
