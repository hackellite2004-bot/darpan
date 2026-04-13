from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
SESSION_DIR = DATA_DIR / "sessions"
DB_PATH = DATA_DIR / "sanchaar.db"
ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
SOUNDS_DIR = ASSETS_DIR / "sounds"

# Load environment variables from .env file
load_dotenv(BASE_DIR / ".env")


def _load_env_file(env_path: Path) -> None:
    if not env_path.exists():
        return
    try:
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
    except Exception:
        pass


_load_env_file(BASE_DIR / ".env")

DATA_DIR.mkdir(exist_ok=True)
SESSION_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
ICONS_DIR.mkdir(exist_ok=True)
SOUNDS_DIR.mkdir(exist_ok=True)

BLINK_EAR_THRESHOLD = 0.20
GAZE_CENTER_THRESHOLD = 0.20
SLOUCH_Y_THRESHOLD = 0.60
IDEAL_WPM_MIN = 110
IDEAL_WPM_MAX = 150
FILLER_PENALTY = 5
LONG_PAUSE_THRESHOLD = 2.0
MONOTONE_THRESHOLD = 15.0

WEIGHT_EYE_CONTACT = 0.25
WEIGHT_EMOTION = 0.20
WEIGHT_POSTURE = 0.15
WEIGHT_GESTURE = 0.15
WEIGHT_SPEECH = 0.15
WEIGHT_VOICE = 0.10

WHISPER_MODEL_SIZE = "base"
GEMINI_MODEL = "gemini-1.5-flash"

COLOR_PRIMARY = "#0B6E99"
COLOR_ACCENT = "#1F9D73"
COLOR_DANGER = "#C0392B"
COLOR_BG_DARK = "#0E1A24"
COLOR_SURFACE = "#132635"
COLOR_CARD = "#173345"
COLOR_TEXT = "#F2F6F9"
COLOR_MUTED = "#8EA3B4"
COLOR_BORDER = "#2C4A5D"
COLOR_SUCCESS = "#1F9D73"
COLOR_WARNING = "#C17F00"

ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"

AGE_GROUPS = {
    "foundational": "Foundational (5-8 yrs)",
    "preparatory": "Preparatory (9-12 yrs)",
    "middle": "Middle (13-16 yrs)",
    "secondary": "Secondary (16-19 yrs)",
    "college": "College / Youth (19+ yrs)",
}

DEPENDENCY_PACKAGE_MAP = {
    "PySide6": "PySide6>=6.6.0",
    "cv2": "opencv-python>=4.9.0",
    "mediapipe": "mediapipe>=0.10.0",
    "whisper": "openai-whisper>=20231117",
    "librosa": "librosa>=0.10.0",
    "pyaudio": "pyaudio>=0.2.14",
    "google.generativeai": "google-generativeai>=0.8.3",
    "moviepy": "moviepy>=1.0.3",
    "pyqtgraph": "pyqtgraph>=0.13.0",
    "matplotlib": "matplotlib>=3.8.0",
    "numpy": "numpy>=1.26.0",
    "scipy": "scipy>=1.12.0",
    "openpyxl": "openpyxl>=3.1.0",
    "PIL": "Pillow>=10.0.0",
    "tqdm": "tqdm>=4.66.0",
}

REQUIRED_DEPENDENCIES = [
    "PySide6",
    "cv2",
    "mediapipe",
    "whisper",
    "librosa",
    "pyaudio",
    "moviepy",
    "pyqtgraph",
    "matplotlib",
    "numpy",
    "scipy",
]
