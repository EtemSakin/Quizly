"""Local Whisper transcription helpers for Quizly audio files."""

from pathlib import Path

import whisper

DEFAULT_WHISPER_MODEL = "base"
_whisper_model = None


def get_whisper_model():
    """Load Whisper once and reuse the local model between requests."""
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = whisper.load_model(DEFAULT_WHISPER_MODEL)
    return _whisper_model


def transcribe_audio(audio_path):
    """Transcribe an audio file and return non-empty plain text."""
    model = get_whisper_model()
    result = model.transcribe(str(Path(audio_path)))
    transcript = result.get("text", "").strip()
    if not transcript:
        raise ValueError("Whisper returned an empty transcript.")
    return transcript
