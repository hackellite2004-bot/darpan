from __future__ import annotations

from dataclasses import asdict, dataclass
import importlib
from pathlib import Path
from typing import Any

import numpy as np

from analysis.model_manager import get_model_manager

from config import MONOTONE_THRESHOLD


@dataclass(slots=True)
class VoiceToneResult:
    pitch_mean: float = 0.0
    pitch_variation: float = 0.0
    energy_mean: float = 0.0
    energy_variation: float = 0.0
    voice_emotion: str = "neutral"
    emotion_confidence: float = 0.0
    is_monotone: bool = False
    is_too_quiet: bool = False
    is_too_loud: bool = False
    voice_score: float = 0.0


class VoiceToneAnalyzer:
    def __init__(self) -> None:
        manager = get_model_manager()
        self._speech_emotion_model = manager.get_model("speech_emotion")

    @staticmethod
    def _normalize_emotion_label(label: str) -> str:
        label = label.strip().lower()
        if label.startswith("ang"):
            return "angry"
        if label.startswith("hap") or label.startswith("joy"):
            return "happy"
        if label.startswith("neu"):
            return "neutral"
        if label.startswith("sad"):
            return "sad"
        if label.startswith("fea") or label.startswith("fear"):
            return "fear"
        if label.startswith("dis"):
            return "disgusted"
        if label.startswith("sur"):
            return "surprised"
        return label

    def analyze(self, audio_path: str | Path) -> dict[str, Any]:
        try:
            librosa = importlib.import_module("librosa")
        except Exception:
            return asdict(VoiceToneResult())

        try:
            y, sr = librosa.load(str(Path(audio_path)), sr=None, mono=True)
            if y.size == 0:
                return asdict(VoiceToneResult())

            f0, voiced_flag, _ = librosa.pyin(y, fmin=80, fmax=400)
            voiced_values = f0[voiced_flag] if f0 is not None and voiced_flag is not None else np.array([])
            voiced_values = voiced_values[~np.isnan(voiced_values)] if voiced_values.size else voiced_values
            pitch_mean = float(np.mean(voiced_values)) if voiced_values.size else 0.0
            pitch_variation = float(np.std(voiced_values)) if voiced_values.size else 0.0

            rms = librosa.feature.rms(y=y)[0]
            energy_mean = float(np.mean(rms)) if rms.size else 0.0
            energy_variation = float(np.std(rms)) if rms.size else 0.0

            voice_emotion = "neutral"
            emotion_confidence = 0.0
            if self._speech_emotion_model is not None and energy_mean >= 0.01:
                try:
                    predictions = self._speech_emotion_model({"array": y, "sampling_rate": sr})
                    if predictions:
                        top = max(predictions, key=lambda item: float(item.get("score", 0.0)))
                        voice_emotion = self._normalize_emotion_label(str(top.get("label", "neutral")))
                        emotion_confidence = float(top.get("score", 0.0))
                except Exception:
                    pass
            if energy_mean < 0.01:
                voice_emotion = "neutral"
                emotion_confidence = 0.0

            chunk_size = max(sr, 1)
            chunk_rates = []
            for start in range(0, len(y), chunk_size):
                chunk = y[start : start + chunk_size]
                if chunk.size == 0:
                    continue
                chunk_rates.append(float(np.count_nonzero(librosa.zero_crossings(chunk, pad=False))))
            rate_variation = float(np.std(chunk_rates)) if chunk_rates else 0.0

            is_monotone = pitch_variation < MONOTONE_THRESHOLD
            is_too_quiet = energy_mean < 0.02
            is_too_loud = energy_mean > 0.15

            voice_score = 1.0
            if is_monotone:
                voice_score -= 0.3
            if is_too_quiet or is_too_loud:
                voice_score -= 0.2
            voice_score -= min(0.2, rate_variation / 250.0)

            if voice_emotion in {"angry", "fear", "sad"}:
                voice_score -= 0.15 * emotion_confidence
            elif voice_emotion in {"happy", "calm", "neutral"}:
                voice_score += 0.1 * emotion_confidence

            voice_score = float(np.clip(voice_score, 0.0, 1.0))

            return {
                "pitch_mean": pitch_mean,
                "pitch_variation": pitch_variation,
                "energy_mean": energy_mean,
                "energy_variation": energy_variation,
                "voice_emotion": voice_emotion,
                "emotion_confidence": emotion_confidence,
                "is_monotone": is_monotone,
                "is_too_quiet": is_too_quiet,
                "is_too_loud": is_too_loud,
                "voice_score": voice_score,
            }
        except Exception:
            return asdict(VoiceToneResult())


def analyze_voice_tone(audio_path: str | Path) -> dict[str, Any]:
    return VoiceToneAnalyzer().analyze(audio_path)
