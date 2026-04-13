from __future__ import annotations

import json
import importlib
import re
import wave
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np

from config import IDEAL_WPM_MAX, IDEAL_WPM_MIN, LONG_PAUSE_THRESHOLD, WHISPER_MODEL_SIZE


FILLERS = [
    "umm",
    "um",
    "uh",
    "like",
    "basically",
    "you know",
    "sort of",
    "kind of",
    "right",
    "okay so",
    "so yeah",
    "actually",
    "literally",
    "honestly",
]


@dataclass(slots=True)
class SpeechAnalysisResult:
    transcript: str = ""
    word_count: int = 0
    duration: float = 0.0
    wpm: float = 0.0
    filler_words: dict[str, int] | None = None
    total_fillers: int = 0
    long_pauses: list[dict[str, float]] | None = None
    wpm_ideal: bool = False
    pause_count: int = 0
    speech_detected: bool = False
    mic_level: float = 0.0
    speech_issues: list[str] | None = None
    speech_solutions: list[str] | None = None


@lru_cache(maxsize=1)
def _load_model():
    try:
        whisper = importlib.import_module("whisper")
        return whisper.load_model(WHISPER_MODEL_SIZE)
    except Exception:
        return None


class SpeechAnalyzer:
    def __init__(self) -> None:
        self._model = _load_model()

    @staticmethod
    def _detect_fillers(transcript: str) -> dict[str, int]:
        transcript_lower = transcript.lower()
        counts: dict[str, int] = {}
        for filler in FILLERS:
            pattern = r"\\b" + re.escape(filler) + r"\\b"
            counts[filler] = len(re.findall(pattern, transcript_lower))
        return {word: count for word, count in counts.items() if count > 0}

    @staticmethod
    def _extract_words(result: dict[str, Any]) -> list[dict[str, Any]]:
        words: list[dict[str, Any]] = []
        for segment in result.get("segments", []):
            segment_words = segment.get("words") or []
            for word in segment_words:
                words.append(word)
        return words

    def _transcribe_with_fallback(self, audio_path: Path) -> dict[str, Any]:
        """Try normal Whisper transcription first, then fall back to in-memory audio for missing ffmpeg."""
        try:
            return self._model.transcribe(str(audio_path), word_timestamps=True, fp16=False)
        except Exception as exc:
            message = str(exc).lower()
            ffmpeg_missing = "winerror 2" in message or "no such file or directory" in message or "ffmpeg" in message
            if not ffmpeg_missing:
                raise

            librosa = importlib.import_module("librosa")
            audio_array, _ = librosa.load(str(audio_path), sr=16000, mono=True)
            # In-memory array path avoids shelling out to ffmpeg for local wav recordings.
            return self._model.transcribe(audio_array, word_timestamps=True, fp16=False)

    @staticmethod
    def _audio_stats(audio_path: Path) -> tuple[float, float]:
        """Return (duration_seconds, normalized_rms)."""
        try:
            with wave.open(str(audio_path), "rb") as wav_file:
                frames = wav_file.readframes(wav_file.getnframes())
                sample_rate = max(1, int(wav_file.getframerate() or 1))
                channels = max(1, int(wav_file.getnchannels() or 1))
                sample_width = int(wav_file.getsampwidth() or 2)
                duration = float(wav_file.getnframes()) / float(sample_rate)

            if not frames:
                return duration, 0.0

            if sample_width == 1:
                audio = np.frombuffer(frames, dtype=np.uint8).astype(np.float32)
                audio = (audio - 128.0) / 128.0
            elif sample_width == 2:
                audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
            else:
                audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0

            if channels > 1 and audio.size >= channels:
                audio = audio.reshape(-1, channels).mean(axis=1)

            rms = float(np.sqrt(np.mean(np.square(audio)))) if audio.size else 0.0
            return duration, rms
        except Exception:
            return 0.0, 0.0

    def analyze(self, audio_path: str | Path) -> dict[str, Any]:
        audio_path = Path(audio_path)
        duration_estimate, mic_level = self._audio_stats(audio_path)
        issues: list[str] = []
        solutions: list[str] = []

        if mic_level < 0.003:
            issues.append("Very low microphone signal detected")
            solutions.append("Move closer to the microphone and increase system mic input volume")
            solutions.append("Speak continuously for 10-15 seconds and avoid very quiet rooms with fan noise")

        if self._model is None:
            return {
                **asdict(SpeechAnalysisResult()),
                "duration": duration_estimate,
                "mic_level": mic_level,
                "speech_issues": issues + ["Speech model could not be loaded"],
                "speech_solutions": solutions + ["Install/update whisper dependencies and restart the app"],
                "filler_words": {},
                "long_pauses": [],
            }

        try:
            result = self._transcribe_with_fallback(audio_path)
            transcript = (result.get("text") or "").strip()
            words = self._extract_words(result)
            if not words:
                segments = result.get("segments", [])
                for segment in segments:
                    if segment.get("text"):
                        transcript = f"{transcript} {segment['text']}".strip()

            duration = float(result.get("duration") or 0.0)
            if duration <= 0.0 and words:
                duration = max(float(words[-1].get("end", 0.0)), 0.01)
            elif duration <= 0.0:
                duration = 0.01

            word_count = len(re.findall(r"\b\w+\b", transcript))
            wpm = (word_count / duration) * 60.0 if duration > 0 else 0.0
            filler_words = self._detect_fillers(transcript)
            total_fillers = int(sum(filler_words.values()))

            long_pauses: list[dict[str, float]] = []
            for index in range(len(words) - 1):
                current_end = float(words[index].get("end", 0.0))
                next_start = float(words[index + 1].get("start", 0.0))
                gap = next_start - current_end
                if gap > LONG_PAUSE_THRESHOLD:
                    long_pauses.append({"at": round(current_end, 2), "duration": round(gap, 2)})

            result_payload = {
                "transcript": transcript,
                "word_count": word_count,
                "duration": duration,
                "wpm": float(wpm),
                "filler_words": filler_words,
                "total_fillers": total_fillers,
                "long_pauses": long_pauses,
                "wpm_ideal": IDEAL_WPM_MIN <= wpm <= IDEAL_WPM_MAX,
                "pause_count": len(long_pauses),
                "speech_detected": bool(transcript and word_count > 0 and mic_level >= 0.003),
                "mic_level": mic_level,
                "speech_issues": issues,
                "speech_solutions": solutions,
            }

            if not transcript or word_count == 0:
                result_payload["speech_issues"] = issues + ["No clear words detected in recording"]
                result_payload["speech_solutions"] = solutions + ["Check Windows microphone privacy settings for Python/Terminal access"]
                result_payload["speech_detected"] = False

            return result_payload
        except Exception as exc:
            error_hint = str(exc).strip() or "unknown transcription error"
            return {
                **asdict(SpeechAnalysisResult()),
                "duration": duration_estimate,
                "mic_level": mic_level,
                "speech_issues": issues + [f"Speech transcription failed: {error_hint}"],
                "speech_solutions": solutions + ["Install ffmpeg and verify it is available on PATH, then retry recording"],
                "filler_words": {},
                "long_pauses": [],
            }


def analyze_speech(audio_path: str | Path) -> dict[str, Any]:
    return SpeechAnalyzer().analyze(audio_path)
