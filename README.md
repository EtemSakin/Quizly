# Quizly — Django REST Backend

Quizly is a Django REST API that turns YouTube videos into interactive, AI-generated multiple-choice quizzes. This repository contains the **backend** for the Developer Akademie Quizly project. The [official Quizly frontend](https://github.com/Developer-Akademie-Backendkurs/project.Quizly) is maintained separately and can be cloned locally for end-to-end testing.

## Features

- Registration, login, token refresh, and logout with JWTs stored in HttpOnly cookies
- Authenticated quiz creation, listing, detail retrieval, editing, and deletion
- Quiz ownership checks: only the owner can view or modify their quizzes
- YouTube URL validation and audio download with `yt-dlp`
- MP3 extraction with FFmpeg and transcription with local OpenAI Whisper (`base` model)
- Google Gemini generation of **10 questions with 4 answer options each**
- Validation of generated questions and atomic database persistence
- SQLite for local development; Django REST Framework API for the frontend

## Technology

Python, Django 5.2, Django REST Framework, SimpleJWT, django-cors-headers, python-dotenv, yt-dlp, FFmpeg, OpenAI Whisper, and the Google Gen AI SDK.

Python **3.11 or newer is recommended**. Python 3.10 may still work with the installed dependencies but can produce deprecation warnings.

## Repository layout

```text
Quizly/
├── backend/
│   ├── auth_app/          # Registration, login, JWT cookies
│   ├── core/              # Django settings and root URLs
│   ├── quiz_app/          # Models, REST endpoints, AI services, tests
│   ├── .env.example       # Environment variable template
│   ├── manage.py
│   └── requirements.txt
├── .gitignore
└── README.md
```

The separately cloned `frontend/` folder is **ignored by Git**. It is not part of this backend repository.

## Backend setup

### Windows PowerShell

From a terminal:

```powershell
git clone https://github.com/EtemSakin/Quizly.git
cd Quizly
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
```

Edit `backend/.env` to set your own `GEMINI_API_KEY` and development settings. Then run:

```powershell
python backend\manage.py migrate
python backend\manage.py runserver 127.0.0.1:8000
```

### macOS / Linux

```bash
git clone https://github.com/EtemSakin/Quizly.git
cd Quizly
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
# Edit backend/.env with your Gemini API key.
python backend/manage.py migrate
python backend/manage.py runserver 127.0.0.1:8000
```

The backend API is served at **http://127.0.0.1:8000/api/**.

## Environment variables

Copy `backend/.env.example` to `backend/.env` and configure:

| Variable | Purpose |
| --- | --- |
| `SECRET_KEY` | Django secret key; use a strong private value outside local development |
| `DEBUG` | `True` only for local development |
| `ALLOWED_HOSTS` | Comma-separated permitted backend hostnames |
| `CORS_ALLOWED_ORIGINS` | Comma-separated allowed frontend origins |
| `GEMINI_API_KEY` | Your Google Gemini API key; required to generate quizzes |
| `GEMINI_MODEL` | Gemini model ID; the template uses `gemini-3.8-flash` |
| `FFMPEG_LOCATION` | Optional directory containing `ffmpeg` and `ffprobe` for `yt-dlp` |

The Django settings also support an optional `JWT_SIGNING_KEY`; otherwise it derives a signing key from `SECRET_KEY`.

**Never commit `backend/.env`, API keys, or personal credentials.** The included `.gitignore` excludes the local environment file and development SQLite database.

### FFmpeg and Whisper requirements

Both `ffmpeg` **and** `ffprobe` are required. Install FFmpeg and make sure its `bin` directory is on your operating system's **PATH**. Whisper invokes `ffmpeg` directly via a subprocess; setting `FFMPEG_LOCATION` alone is **not sufficient** for Whisper.

Windows (using winget):

```powershell
winget install --id Gyan.FFmpeg -e --source winget
where.exe ffmpeg
where.exe ffprobe
```

If the executables are not found, add the directory containing `ffmpeg.exe` and `ffprobe.exe` to your **user PATH**, then restart your terminal/IDE. You can also set `FFMPEG_LOCATION` in `backend/.env` to that directory to help `yt-dlp` locate them. No machine-specific paths are included in this repository.

macOS (Homebrew):

```bash
brew install ffmpeg
which ffmpeg
which ffprobe
```

Linux: install `ffmpeg` from your distribution's package manager and verify `ffmpeg -version` and `ffprobe -version`.

The first Whisper run may download the local `base` speech-recognition model. Quiz generation also needs internet access to YouTube and the Gemini API; processing a video can take several minutes.

## Run the official frontend locally

Open **a second terminal** at the Quizly repository root and clone the separately maintained frontend:

```powershell
git clone https://github.com/Developer-Akademie-Backendkurs/project.Quizly.git frontend
cd frontend
python -m http.server 5500 --bind 127.0.0.1
```

Visit **http://127.0.0.1:5500/** and register or log in to create a quiz from a YouTube video. Keep the Django server running on port 8000 in the other terminal.

Use `127.0.0.1` for **both servers** to keep the cookie-based login consistent. The frontend sends API requests with `credentials: "include"`, and Django permits the configured frontend origins via CORS.

The `frontend/` directory is ignored because it comes from a **different Git repository**; clone it only for local development and testing.

## REST API

All endpoints are relative to `http://127.0.0.1:8000`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/register/` | Register a new account |
| `POST` | `/api/login/` | Log in and set HttpOnly JWT cookies |
| `POST` | `/api/logout/` | Log out and clear authentication cookies |
| `POST` | `/api/token/refresh/` | Refresh the access-token cookie |
| `POST` | `/api/quizzes/` | Generate and save a quiz from a YouTube URL |
| `GET` | `/api/quizzes/` | List quizzes owned by the logged-in user |
| `GET` | `/api/quizzes/{id}/` | Retrieve a quiz with its questions |
| `PATCH` | `/api/quizzes/{id}/` | Change quiz title and/or description |
| `DELETE` | `/api/quizzes/{id}/` | Delete an owned quiz and its questions |

Registration expects `username`, `email`, `password`, and `confirmed_password`. Login expects `username` and `password`. Quiz creation accepts:

```json
{
  "url": "https://www.youtube.com/watch?v=BT5q46Es6e8"
}
```

Successful quiz creation returns HTTP `201` with the quiz, timestamps, video URL, and nested questions. Each question has a title, four answer options, and its matching answer. Quiz endpoints require the JWT access cookie obtained during login.

## Tests

Run the Django system check and automated tests from the repository root:

```powershell
python backend\manage.py check
python backend\manage.py test auth_app quiz_app
```

**Last local verification:** 56 tests passed, with no Django system-check issues. Tests cover authentication, JWT cookies, ownership rules, CRUD operations, URL validation, and quiz-processing components. External integrations are mocked in automated tests; the complete YouTube → Whisper → Gemini → browser quiz flow has also been tested manually.

## Notes

- The application is configured for **local development** by default, not production deployment.
- Protect the Gemini key and configure appropriate HTTPS, secrets, hosts, and CORS origins before any production deployment.
- The official frontend is separate from this repository; its files are intentionally not committed here.
