"""Orchestrate audio transcription, AI generation, and atomic persistence."""

from django.db import transaction

from quiz_app.models import Question, Quiz
from quiz_app.services.gemini import generate_quiz_content
from quiz_app.services.transcription import transcribe_audio
from quiz_app.services.youtube import canonical_youtube_url, download_audio


def _transcribe_video(url):
    """Transcribe an extracted audio file before its temporary cleanup."""
    with download_audio(url) as audio_path:
        return transcribe_audio(audio_path)


def _store_quiz(user, url, content):
    """Persist a validated quiz and all ten questions in one transaction."""
    with transaction.atomic():
        quiz = Quiz.objects.create(
            user=user, title=content["title"],
            description=content["description"], video_url=url,
        )
        Question.objects.bulk_create(
            [Question(quiz=quiz, **item) for item in content["questions"]]
        )
    return Quiz.objects.prefetch_related("questions").get(pk=quiz.pk)


def generate_quiz(user, url):
    """Generate a complete owned quiz from one canonical YouTube URL."""
    canonical_url = canonical_youtube_url(url)
    transcript = _transcribe_video(canonical_url)
    content = generate_quiz_content(transcript)
    return _store_quiz(user, canonical_url, content)
