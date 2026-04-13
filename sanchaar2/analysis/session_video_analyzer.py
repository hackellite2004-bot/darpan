from __future__ import annotations

from collections import Counter, deque
from statistics import mean
from typing import Any

import numpy as np

from analysis.emotion_analyzer import EmotionAnalyzer
from analysis.eye_gaze_analyzer import EyeGazeAnalyzer
from analysis.gesture_analyzer import GestureAnalyzer
from analysis.pose_analyzer import PoseAnalyzer

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


def _safe_mean(values: list[float], default: float = 0.0) -> float:
    if not values:
        return default
    return float(mean(values))


def analyze_video_session(video_path: str, target_fps: float = 8.0) -> dict[str, Any]:
    defaults = {
        "emotion_happy": 0.0,
        "emotion_neutral": 1.0,
        "emotion_sad": 0.0,
        "emotion_anxious": 0.0,
        "emotion_surprised": 0.0,
        "emotion_dominant": "neutral",
        "eye_center_pct": 0.0,
        "eye_away_pct": 100.0,
        "blink_count": 0,
        "posture_score": 0.5,
        "slouch_pct": 0.0,
        "gesture_positive_pct": 0.0,
        "gesture_nervous_pct": 0.0,
        "gesture_type": "neutral",
        "duration_seconds": 0.0,
        "frame_scores": [],
    }
    if cv2 is None:
        return defaults

    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return defaults

    emotion_analyzer = EmotionAnalyzer()
    gaze_analyzer = EyeGazeAnalyzer()
    pose_analyzer = PoseAnalyzer()
    gesture_analyzer = GestureAnalyzer()

    gaze_counts: Counter[str] = Counter()
    gesture_counts: Counter[str] = Counter()
    emotion_history: list[dict[str, float]] = []
    posture_scores: list[float] = []
    slouch_frames = 0
    blink_count = 0
    frame_scores: list[tuple[float, float]] = []

    emotion_window: deque[dict[str, float]] = deque(maxlen=5)
    posture_window: deque[float] = deque(maxlen=5)

    fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration_seconds = (total_frames / fps) if fps > 0 else 0.0
    sample_every = max(1, int(round(fps / max(target_fps, 1.0))))

    frame_index = 0
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        if frame_index % sample_every != 0:
            frame_index += 1
            continue

        emotion = emotion_analyzer.analyze(frame)
        gaze = gaze_analyzer.analyze(frame)
        pose = pose_analyzer.analyze(frame)
        gesture = gesture_analyzer.analyze(frame)

        if bool(gaze.get("blink", False)):
            blink_count += 1

        gaze_label = str(gaze.get("gaze", "away"))
        gesture_label = str(gesture.get("gesture_type", "neutral"))
        gaze_counts[gaze_label] += 1
        gesture_counts[gesture_label] += 1

        e = {
            "happy": float(emotion.get("happy", 0.0)),
            "neutral": float(emotion.get("neutral", 1.0)),
            "sad": float(emotion.get("sad", 0.0)),
            "anxious": float(emotion.get("anxious", 0.0)),
            "surprised": float(emotion.get("surprised", 0.0)),
        }
        emotion_window.append(e)
        smoothed_emotion = {
            key: _safe_mean([item[key] for item in emotion_window], 0.0)
            for key in ("happy", "neutral", "sad", "anxious", "surprised")
        }
        emotion_history.append(smoothed_emotion)

        posture_score = float(pose.get("posture_score", 0.5))
        posture_window.append(posture_score)
        smoothed_posture = _safe_mean(list(posture_window), 0.5)
        posture_scores.append(smoothed_posture)
        if bool(pose.get("slouching", False)):
            slouch_frames += 1

        eye_center = 100.0 if gaze_label == "center" else 0.0
        emotion_component = (smoothed_emotion["happy"] + smoothed_emotion["neutral"] * 0.7) * 100.0
        posture_component = smoothed_posture * 100.0
        gesture_component = 100.0 if gesture_label == "expressive" else 55.0 if gesture_label == "neutral" else 30.0
        frame_score = float(np.clip(eye_center * 0.35 + emotion_component * 0.25 + posture_component * 0.25 + gesture_component * 0.15, 0.0, 100.0))
        timestamp = frame_index / fps if fps > 0 else float(frame_index)
        frame_scores.append((round(timestamp, 2), round(frame_score, 2)))

        frame_index += 1

    capture.release()

    analyzed_frames = max(1, sum(gaze_counts.values()))
    frame_values = [score for _, score in frame_scores]
    emotion_avg = {
        "happy": _safe_mean([entry["happy"] for entry in emotion_history], 0.0),
        "neutral": _safe_mean([entry["neutral"] for entry in emotion_history], 1.0),
        "sad": _safe_mean([entry["sad"] for entry in emotion_history], 0.0),
        "anxious": _safe_mean([entry["anxious"] for entry in emotion_history], 0.0),
        "surprised": _safe_mean([entry["surprised"] for entry in emotion_history], 0.0),
    }
    dominant = max(emotion_avg, key=emotion_avg.get)

    center_pct = (gaze_counts.get("center", 0) / analyzed_frames) * 100.0
    non_center = analyzed_frames - gaze_counts.get("center", 0)
    away_pct = (non_center / analyzed_frames) * 100.0
    slouch_pct = (slouch_frames / analyzed_frames) * 100.0
    posture_score = _safe_mean(posture_scores, 0.5)
    gesture_positive = ((gesture_counts.get("expressive", 0) + gesture_counts.get("neutral", 0) * 0.4) / analyzed_frames) * 100.0
    gesture_nervous = ((gesture_counts.get("nervous", 0) + gesture_counts.get("hidden", 0)) / analyzed_frames) * 100.0
    dominant_gesture = max(gesture_counts, key=gesture_counts.get) if gesture_counts else "neutral"
    frame_mean = _safe_mean(frame_values, 0.0)
    frame_min = float(min(frame_values)) if frame_values else 0.0
    frame_max = float(max(frame_values)) if frame_values else 0.0
    frame_std = float(np.std(frame_values)) if len(frame_values) > 1 else 0.0
    stable_frames = sum(1 for value in frame_values if abs(value - frame_mean) <= 12.0)
    frame_stability = float((stable_frames / max(1, len(frame_values))) * 100.0)

    return {
        "emotion_happy": float(np.clip(emotion_avg["happy"], 0.0, 1.0)),
        "emotion_neutral": float(np.clip(emotion_avg["neutral"], 0.0, 1.0)),
        "emotion_sad": float(np.clip(emotion_avg["sad"], 0.0, 1.0)),
        "emotion_anxious": float(np.clip(emotion_avg["anxious"], 0.0, 1.0)),
        "emotion_surprised": float(np.clip(emotion_avg["surprised"], 0.0, 1.0)),
        "emotion_dominant": dominant,
        "eye_center_pct": float(np.clip(center_pct, 0.0, 100.0)),
        "eye_away_pct": float(np.clip(away_pct, 0.0, 100.0)),
        "blink_count": int(blink_count),
        "posture_score": float(np.clip(posture_score, 0.0, 1.0)),
        "slouch_pct": float(np.clip(slouch_pct, 0.0, 100.0)),
        "gesture_positive_pct": float(np.clip(gesture_positive, 0.0, 100.0)),
        "gesture_nervous_pct": float(np.clip(gesture_nervous, 0.0, 100.0)),
        "gesture_type": dominant_gesture,
        "duration_seconds": float(max(duration_seconds, 0.0)),
        "frame_scores": frame_scores,
        "frame_score_mean": float(frame_mean),
        "frame_score_min": float(frame_min),
        "frame_score_max": float(frame_max),
        "frame_score_std": float(frame_std),
        "frame_stability": float(frame_stability),
        "frame_sample_count": int(len(frame_values)),
    }
