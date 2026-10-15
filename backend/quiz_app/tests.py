"""Tests for Quizly quiz functionality."""

from pathlib import Path
from unittest.mock import patch

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from quiz_app.models import Question, Quiz
from quiz_app.services.transcription import transcribe_audio
from quiz_app.services.youtube import (
    canonical_youtube_url,
    download_audio,
    extract_video_id,
)

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


class YouTubeServiceTests(TestCase):
    """Cover YouTube URL normalization and audio extraction setup."""

    def test_extracts_video_id_from_watch_url(self):
        """Read the id from a regular YouTube watch URL."""
        url = "https://www.youtube.com/watch?v=abcdefghijk"
        self.assertEqual(extract_video_id(url), "abcdefghijk")

    def test_extracts_video_id_from_short_url(self):
        """Read the id from a youtu.be share URL."""
        self.assertEqual(extract_video_id("https://youtu.be/abcdefghijk"), "abcdefghijk")

    def test_rejects_non_youtube_url(self):
        """Reject URLs outside supported YouTube hosts."""
        with self.assertRaises(ValueError):
            extract_video_id("https://example.com/watch?v=abcdefghijk")

    def test_rejects_invalid_video_id(self):
        """Reject malformed YouTube video identifiers."""
        with self.assertRaises(ValueError):
            extract_video_id("https://www.youtube.com/watch?v=short")

    def test_builds_canonical_watch_url(self):
        """Normalize supported links to the persisted watch URL."""
        result = canonical_youtube_url("https://youtu.be/abcdefghijk?t=5")
        self.assertEqual(result, "https://www.youtube.com/watch?v=abcdefghijk")

    @patch("quiz_app.services.youtube.YoutubeDL")
    def test_download_audio_uses_yt_dlp_and_ffmpeg(self, youtube_dl):
        """Configure one best-audio download and FFmpeg extraction."""
        downloader = youtube_dl.return_value.__enter__.return_value
        with patch("quiz_app.services.youtube.Path.exists", return_value=True):
            with download_audio("https://youtu.be/abcdefghijk") as audio_path:
                self.assertEqual(audio_path.name, "audio.mp3")
        options = youtube_dl.call_args.args[0]
        self.assertEqual(options["format"], "bestaudio/best")
        self.assertTrue(options["noplaylist"])
        self.assertEqual(options["postprocessors"][0]["key"], "FFmpegExtractAudio")
        downloader.download.assert_called_once_with(
            ["https://www.youtube.com/watch?v=abcdefghijk"]
        )


class TranscriptionServiceTests(TestCase):
    """Cover local Whisper transcription behavior without loading a model."""

    @patch("quiz_app.services.transcription.get_whisper_model")
    def test_transcribe_audio_returns_trimmed_text(self, get_model):
        """Return plain transcript text from Whisper output."""
        get_model.return_value.transcribe.return_value = {"text": "  Hello world.  "}
        result = transcribe_audio(Path("audio.mp3"))
        self.assertEqual(result, "Hello world.")
        get_model.return_value.transcribe.assert_called_once_with("audio.mp3")

    @patch("quiz_app.services.transcription.get_whisper_model")
    def test_transcribe_audio_rejects_empty_text(self, get_model):
        """Reject an empty Whisper result before quiz generation."""
        get_model.return_value.transcribe.return_value = {"text": "   "}
        with self.assertRaises(ValueError):
            transcribe_audio("audio.mp3")
