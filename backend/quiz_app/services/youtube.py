"""YouTube URL validation and audio download helpers."""

import re
from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from yt_dlp import YoutubeDL

VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com"}


def _candidate_video_id(parsed_url):
    """Return a possible video id from a supported YouTube URL."""
    host = parsed_url.netloc.lower()
    if host == "youtu.be":
        return parsed_url.path.strip("/").split("/", 1)[0]
    if host not in YOUTUBE_HOSTS:
        return None
    if parsed_url.path == "/watch":
        return parse_qs(parsed_url.query).get("v", [None])[0]
    if parsed_url.path.startswith(("/shorts/", "/embed/")):
        return parsed_url.path.strip("/").split("/", 1)[1]
    return None


def extract_video_id(url):
    """Extract and validate the eleven-character YouTube video id."""
    parsed_url = urlparse(url)
    if parsed_url.scheme not in {"http", "https"}:
        raise ValueError("Invalid YouTube URL.")
    video_id = _candidate_video_id(parsed_url)
    if not video_id or not VIDEO_ID_PATTERN.fullmatch(video_id):
        raise ValueError("Invalid YouTube URL.")
    return video_id


def canonical_youtube_url(url):
    """Return the canonical watch URL persisted by Quizly."""
    video_id = extract_video_id(url)
    return f"https://www.youtube.com/watch?v={video_id}"


def _download_options(output_template):
    """Build yt-dlp options for extracting one audio track."""
    options = {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"},
        ],
    }
    if settings.FFMPEG_LOCATION:
        options["ffmpeg_location"] = settings.FFMPEG_LOCATION
    return options


@contextmanager
def download_audio(url):
    """Download YouTube audio temporarily and yield its MP3 path."""
    canonical_url = canonical_youtube_url(url)
    with TemporaryDirectory(prefix="quizly_") as temp_dir:
        output_template = str(Path(temp_dir) / "audio.%(ext)s")
        with YoutubeDL(_download_options(output_template)) as downloader:
            downloader.download([canonical_url])
        audio_path = Path(temp_dir) / "audio.mp3"
        if not audio_path.exists():
            raise RuntimeError("Audio extraction failed.")
        yield audio_path
