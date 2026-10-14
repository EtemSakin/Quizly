# Quizly Backend

Quizly is the Django REST backend for the Developer Akademie Quizly project. The official frontend is maintained separately and communicates with this backend through a REST API.

## Current Status

Initial Django project structure only. Authentication, quiz management, and AI-based quiz generation are implemented in later development steps.

## Planned Features

- User registration, login, token refresh, and logout
- JWT authentication using HttpOnly cookies
- User-owned quiz management
- Quiz generation from YouTube videos
- Audio extraction with yt-dlp and FFmpeg
- Transcription with Whisper AI
- Quiz generation with Gemini Flash

## Technology Stack

- Python
- Django
- Django REST Framework
- SimpleJWT
- django-cors-headers
- python-dotenv

## Project Structure

```text
Quizly/
├── backend/
│   ├── auth_app/
│   ├── core/
│   ├── quiz_app/
│   ├── .env.example
│   ├── manage.py
│   └── requirements.txt
├── .gitignore
└── README.md
```

## Quick Start

### Windows PowerShell

```powershell
git clone https://github.com/EtemSakin/Quizly.git
cd Quizly
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
Copy-Item backend\.env.example backend\.env
python backend\manage.py migrate
python backend\manage.py runserver
```

### macOS / Linux

```bash
git clone https://github.com/EtemSakin/Quizly.git
cd Quizly
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
python backend/manage.py migrate
python backend/manage.py runserver
```

## Environment Configuration

Copy `backend/.env.example` to `backend/.env` and replace development placeholders where necessary. Never commit the real `.env` file.

## External Requirements

FFmpeg must be installed globally before the later YouTube/Whisper pipeline can be used.

### Windows

```powershell
winget install --id Gyan.FFmpeg -e --source winget
```

### macOS

```bash
brew install ffmpeg
```

## API Base URL

The official frontend expects the backend at:

```text
http://127.0.0.1:8000/api/
```

The documented API includes registration, login, logout, token refresh, and quiz CRUD endpoints. These endpoints are added in later commits.

## Tests

Run Django checks with:

```powershell
python backend\manage.py check
```

Full test and coverage commands will be documented when application functionality is implemented.
