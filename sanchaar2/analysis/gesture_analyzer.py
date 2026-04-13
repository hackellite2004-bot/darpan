from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from analysis.model_manager import get_model_manager

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import mediapipe as mp
except Exception:  # pragma: no cover
    mp = None


@dataclass(slots=True)
class GestureResult:
    gesture_type: str = "neutral"
    confidence: float = 0.0
    positive_pct: float = 0.0
    nervous_pct: float = 0.0


class GestureAnalyzer:
    def __init__(self) -> None:
        manager = get_model_manager()
        self._hands = manager.get_model("gesture")
        self._positive_frames = 0
        self._nervous_frames = 0
        self._total_frames = 0
        self._hidden_streak = 0

    @staticmethod
    def _tip_spread(landmarks: list[Any]) -> float:
        fingertip_indices = [4, 8, 12, 16, 20]
        points = [landmarks[index] for index in fingertip_indices]
        dists = []
        for i in range(len(points) - 1):
            for j in range(i + 1, len(points)):
                dists.append(np.linalg.norm(np.array([points[i].x, points[i].y]) - np.array([points[j].x, points[j].y])))
        return float(np.mean(dists)) if dists else 0.0

    @staticmethod
    def _palm_open_ratio(landmarks: list[Any]) -> float:
        wrist = landmarks[0]
        middle_tip = landmarks[12]
        index_tip = landmarks[8]
        pinky_tip = landmarks[20]
        palm_span = np.linalg.norm(np.array([index_tip.x, index_tip.y]) - np.array([pinky_tip.x, pinky_tip.y]))
        wrist_to_middle = np.linalg.norm(np.array([wrist.x, wrist.y]) - np.array([middle_tip.x, middle_tip.y]))
        if palm_span <= 1e-6:
            return 0.0
        return float(wrist_to_middle / palm_span)

    def analyze(self, frame: np.ndarray | None) -> dict[str, float | str]:
        self._total_frames += 1
        default = GestureResult()
        if frame is None or self._hands is None or cv2 is None or mp is None:
            return asdict(default)

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._hands.detect(image)
            if not getattr(result, "hand_landmarks", None):
                self._hidden_streak += 1
                if self._hidden_streak >= 10:
                    self._nervous_frames += 1
                return {
                    "gesture_type": "hidden",
                    "confidence": 0.25,
                    "positive_pct": self.positive_pct,
                    "nervous_pct": self.nervous_pct,
                }
            self._hidden_streak = 0

            spreads = []
            openness = []
            for hand_landmarks in result.hand_landmarks:
                spread = self._tip_spread(hand_landmarks)
                spreads.append(spread)
                openness.append(self._palm_open_ratio(hand_landmarks))

            spread_score = float(np.mean(spreads)) if spreads else 0.0
            open_score = float(np.mean(openness)) if openness else 0.0
            gesture_type = "expressive" if (spread_score > 0.11 and open_score > 1.0) else "neutral"
            if spread_score < 0.045 or open_score < 0.78:
                gesture_type = "nervous"
            confidence = float(np.clip((spread_score * 5.0 + open_score * 0.5), 0.0, 1.0))
            if gesture_type == "expressive":
                self._positive_frames += 1
            elif gesture_type in {"nervous", "hidden"}:
                self._nervous_frames += 1
            return {
                "gesture_type": gesture_type,
                "confidence": confidence,
                "positive_pct": self.positive_pct,
                "nervous_pct": self.nervous_pct,
            }
        except Exception:
            return asdict(default)

    @property
    def positive_pct(self) -> float:
        if self._total_frames <= 0:
            return 0.0
        return float((self._positive_frames / self._total_frames) * 100.0)

    @property
    def nervous_pct(self) -> float:
        if self._total_frames <= 0:
            return 0.0
        return float((self._nervous_frames / self._total_frames) * 100.0)


def analyze_gesture(frame: np.ndarray | None) -> dict[str, float | str]:
    return GestureAnalyzer().analyze(frame)
