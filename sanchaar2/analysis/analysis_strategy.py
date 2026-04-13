from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

import numpy as np


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    if not values:
        return default
    return float(mean(values))


def _safe_std(values: list[float], default: float = 0.0) -> float:
    if len(values) < 2:
        return default
    return float(pstdev(values))


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return float(np.clip(value, lower, upper))


def _wpm_band(age_group: str | None) -> tuple[int, int]:
    lookup = {
        "foundational": (85, 115),
        "preparatory": (95, 125),
        "middle": (105, 140),
        "secondary": (110, 150),
        "college": (120, 160),
    }
    return lookup.get((age_group or "").lower(), (110, 150))


def build_analysis_profile(
    video_metrics: dict[str, Any],
    speech_metrics: dict[str, Any],
    voice_metrics: dict[str, Any],
    calibration: dict[str, Any] | None = None,
    user: dict[str, Any] | None = None,
    frame_scores: list[tuple[float, float]] | None = None,
) -> dict[str, Any]:
    frame_scores = frame_scores or []
    frame_values = [float(score) for _, score in frame_scores]
    frame_mean = _safe_mean(frame_values, 0.0)
    frame_std = _safe_std(frame_values, 0.0)
    frame_min = min(frame_values) if frame_values else 0.0
    frame_max = max(frame_values) if frame_values else 0.0
    frame_range = frame_max - frame_min
    steady_frames = sum(1 for value in frame_values if abs(value - frame_mean) <= 12.0)
    frame_stability = _clamp((steady_frames / max(len(frame_values), 1)) * 100.0)
    temporal_confidence = _clamp(100.0 - (frame_std * 1.6) - (frame_range * 0.35))

    eye_center = float(video_metrics.get("eye_center_pct") or 0.0)
    posture_score = float(video_metrics.get("posture_score") or 0.0) * 100.0
    slouch_pct = float(video_metrics.get("slouch_pct") or 0.0)
    gesture_positive = float(video_metrics.get("gesture_positive_pct") or 0.0)
    gesture_nervous = float(video_metrics.get("gesture_nervous_pct") or 0.0)
    blink_count = float(video_metrics.get("blink_count") or 0.0)
    wpm = float(speech_metrics.get("wpm") or 0.0)
    filler_count = int(speech_metrics.get("total_fillers") or speech_metrics.get("filler_count") or 0)
    pause_count = int(speech_metrics.get("pause_count") or 0)
    voice_score = float(voice_metrics.get("voice_score") or 0.0) * 100.0
    pitch_variation = float(voice_metrics.get("pitch_variation") or 0.0)
    emotion_dominant = str(video_metrics.get("emotion_dominant") or "neutral")

    age_group = str((user or {}).get("age_group") or "secondary")
    lower_wpm, upper_wpm = _wpm_band(age_group)
    wpm_mid = (lower_wpm + upper_wpm) / 2.0
    wpm_distance = abs(wpm - wpm_mid)
    speech_fit = _clamp(100.0 - wpm_distance * 1.3 - filler_count * 2.2 - pause_count * 4.0)
    vision_fit = _clamp((eye_center * 0.38) + (posture_score * 0.24) + ((100.0 - slouch_pct) * 0.18) + (gesture_positive * 0.10) - (gesture_nervous * 0.12))
    vocal_fit = _clamp(voice_score * 0.7 + (100.0 - min(100.0, pitch_variation * 120.0)) * 0.3)
    emotion_balance = _clamp(
        100.0
        - (
            float(video_metrics.get("emotion_anxious") or 0.0) * 55.0
            + float(video_metrics.get("emotion_surprised") or 0.0) * 35.0
        )
    )

    reliability = _clamp(
        (frame_stability * 0.22)
        + (temporal_confidence * 0.18)
        + (vision_fit * 0.24)
        + (speech_fit * 0.18)
        + (vocal_fit * 0.10)
        + (emotion_balance * 0.08)
    )

    calibration_threshold = float((calibration or {}).get("confidence_threshold") or 55.0)
    recommended_threshold = _clamp(calibration_threshold + max(-8.0, min(8.0, (50.0 - reliability) / 8.0)), 35.0, 75.0)

    if reliability >= 75 and frame_stability >= 65:
        analysis_mode = "high-confidence"
    elif reliability >= 50:
        analysis_mode = "guarded"
    else:
        analysis_mode = "uncertain"

    dominant_pattern = "steady"
    if gesture_nervous > 35 or slouch_pct > 40 or eye_center < 40:
        dominant_pattern = "needs_attention"
    elif emotion_dominant in {"happy", "neutral"} and reliability >= 60:
        dominant_pattern = "balanced"

    return {
        "analysis_mode": analysis_mode,
        "dominant_pattern": dominant_pattern,
        "signal_quality": reliability,
        "temporal_confidence": temporal_confidence,
        "frame_stability": frame_stability,
        "frame_mean": frame_mean,
        "frame_std": frame_std,
        "frame_range": frame_range,
        "sampled_frames": len(frame_values),
        "wpm_band": [lower_wpm, upper_wpm],
        "speech_fit": speech_fit,
        "vision_fit": vision_fit,
        "vocal_fit": vocal_fit,
        "emotion_balance": emotion_balance,
        "recommended_threshold": recommended_threshold,
        "summary": f"{analysis_mode.replace('-', ' ').title()} analysis with {reliability:.0f}/100 signal quality.",
        "trend": {
            "start": frame_scores[0][1] if frame_scores else None,
            "middle": frame_scores[len(frame_scores) // 2][1] if frame_scores else None,
            "end": frame_scores[-1][1] if frame_scores else None,
        },
        "baseline_notes": {
            "calibration_threshold": calibration_threshold,
            "dominant_emotion": emotion_dominant,
            "blink_count": int(blink_count),
            "pitch_variation": pitch_variation,
        },
    }