from __future__ import annotations

from typing import Any

from config import (
    WEIGHT_EMOTION,
    WEIGHT_EYE_CONTACT,
    WEIGHT_GESTURE,
    WEIGHT_POSTURE,
    WEIGHT_SPEECH,
    WEIGHT_VOICE,
)


def compute_speech_score(wpm: float, filler_count: int, pause_count: int) -> float:
    wpm_score = 100 if 110 <= wpm <= 150 else max(0.0, 100.0 - abs(wpm - 130.0) * 1.5)
    filler_score = max(0.0, 100.0 - filler_count * 5.0)
    pause_score = max(0.0, 100.0 - pause_count * 10.0)
    return float((wpm_score + filler_score + pause_score) / 3.0)


def compute_confidence_score(session_metrics: dict[str, Any]) -> dict[str, Any]:
    eye_score = float(session_metrics.get("eye_center_pct") or 0.0)
    happy = float(session_metrics.get("emotion_happy") or 0.0)
    neutral = float(session_metrics.get("emotion_neutral") or 0.0)
    sad = float(session_metrics.get("emotion_sad") or 0.0)
    anxious = float(session_metrics.get("emotion_anxious") or 0.0)
    surprised = float(session_metrics.get("emotion_surprised") or 0.0)
    calmness = max(0.0, 1.0 - max(anxious, surprised) * 0.9)
    emotion_score = (neutral * 0.50 + happy * 0.15 + sad * 0.20 + calmness * 0.15) * 100.0
    posture_score = float(session_metrics.get("posture_score") or 0.0) * 100.0
    gesture_score = float(session_metrics.get("gesture_positive_pct") or 0.0)
    speech_score = compute_speech_score(
        float(session_metrics.get("wpm") or 0.0),
        int(session_metrics.get("filler_count") or 0),
        int(session_metrics.get("pause_count") or 0),
    )
    voice_score = float(session_metrics.get("voice_score") or 0.0) * 100.0
    quality_score = float(
        min(
            100.0,
            max(
                0.0,
                (eye_score * 0.18)
                + (emotion_score * 0.16)
                + (posture_score * 0.22)
                + (gesture_score * 0.14)
                + (speech_score * 0.18)
                + (voice_score * 0.12)
            ),
        )
    )

    score = (
        eye_score * WEIGHT_EYE_CONTACT
        + emotion_score * WEIGHT_EMOTION
        + posture_score * WEIGHT_POSTURE
        + gesture_score * WEIGHT_GESTURE
        + speech_score * WEIGHT_SPEECH
        + voice_score * WEIGHT_VOICE
    )
    if score >= 85:
        grade = "A"
    elif score >= 70:
        grade = "B"
    elif score >= 55:
        grade = "C"
    else:
        grade = "D"

    breakdown = {
        "eye_score": eye_score,
        "emotion_score": emotion_score,
        "emotion_sad": sad * 100.0,
        "posture_score": posture_score,
        "gesture_score": gesture_score,
        "speech_score": speech_score,
        "voice_score": voice_score,
        "quality_score": quality_score,
    }
    return {"score": float(round(score, 2)), "grade": grade, "breakdown": breakdown, "quality_score": quality_score}


def classify_confidence(score: float, quality_score: float, threshold: float = 55.0) -> dict[str, Any]:
    if score < threshold or quality_score < 45.0:
        return {"label": "uncertain", "message": "Detection confidence is low, so this result should be treated as uncertain."}
    if score >= 80 and quality_score >= 70:
        return {"label": "confident", "message": "Detection confidence is strong."}
    return {"label": "moderate", "message": "Detection confidence is usable but still somewhat noisy."}
