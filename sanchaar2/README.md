# Darpan

Darpan is a desktop communication skills analyzer built with PySide6. It records video and audio, analyzes facial emotions, eye contact, posture, hand gestures, speech, and voice tone, then generates an AI coaching report and session history.

## Features

- Dark-first Qt desktop UI with a light mode toggle
- Live webcam preview and microphone recording
- MediaPipe-based face, eye gaze, pose, and hand gesture analysis
- Whisper transcription with filler-word and pause detection
- librosa-based voice tone analysis
- Unified confidence score and grade
- Optional Gemini-powered coaching tips and interview questions
- Session history and progress charts backed by SQLite
- Mock interview mode
- Teacher dashboard with Excel export
- Highlight reel export support

## Prerequisites

- Python 3.10 or newer
- pip
- ffmpeg installed and available on PATH for moviepy export

## Installation

```bash
git clone <your-repo-url>
cd sanchaar2
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On macOS/Linux:

```bash
source .venv/bin/activate
```

## Gemini API Key

Create a `.env` file in the project root and add your Gemini API key there:

```env
GEMINI_API_KEY=your_key_here
```

You can still set it as an environment variable if you prefer, but `.env` is the recommended setup for this project.

If you want to set it manually instead, use:

Windows:

```powershell
set GEMINI_API_KEY=your_key_here
```

macOS/Linux:

```bash
export GEMINI_API_KEY=your_key_here
```

If the key is missing, the app still runs and shows a fallback coaching message.

## Run

```bash
python main.py
```

## Package as an EXE

```bash
pyinstaller --onefile --windowed main.py
```

## Project Structure

- `main.py`: application entry point
- `config.py`: shared paths, thresholds, colors, and model names
- `core/`: database, session lifecycle, and recording helpers
- `analysis/`: emotion, gaze, posture, gesture, speech, voice, and score logic
- `ai/`: Gemini integration and interview prompts
- `ui/`: Qt styles, main window, pages, and reusable widgets
- `data/`: SQLite database and saved sessions
- `assets/`: icons and optional sounds

## Notes

- The app is Windows-first, but the code structure stays portable.
- Most analysis failures are handled gracefully and fall back to neutral values.
- Session artifacts are written to `data/sessions/<timestamp>/`.
