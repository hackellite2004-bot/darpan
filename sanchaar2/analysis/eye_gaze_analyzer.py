from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from analysis.model_manager import get_model_manager

from config import BLINK_EAR_THRESHOLD, GAZE_CENTER_THRESHOLD

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import mediapipe as mp
except Exception:  # pragma: no cover
    mp = None


@dataclass(slots=True)
class EyeGazeResult:
    gaze: str = "away"
    blink: bool = False
    ear: float = 0.0


class EyeGazeAnalyzer:
    def __init__(self) -> None:
        manager = get_model_manager()
        self._face_mesh = manager.get_model("gaze")
        self._blink_frames = 0
        self._blink_active = False

    @staticmethod
    def _distance(a: Any, b: Any) -> float:
        return float(np.linalg.norm(np.array([a.x, a.y]) - np.array([b.x, b.y])))

    @staticmethod
    def _eye_aspect_ratio(landmarks: list[Any], indices: tuple[int, int, int, int, int, int]) -> float:
        p1, p2, p3, p4, p5, p6 = [landmarks[index] for index in indices]
        vertical_1 = np.linalg.norm(np.array([p2.x, p2.y]) - np.array([p6.x, p6.y]))
        vertical_2 = np.linalg.norm(np.array([p3.x, p3.y]) - np.array([p5.x, p5.y]))
        horizontal = np.linalg.norm(np.array([p1.x, p1.y]) - np.array([p4.x, p4.y]))
        if horizontal <= 1e-6:
            return 0.0
        return float((vertical_1 + vertical_2) / (2.0 * horizontal))

    def analyze(self, frame: np.ndarray | None) -> dict[str, float | str | bool]:
        if frame is None or self._face_mesh is None or cv2 is None or mp is None:
            return asdict(EyeGazeResult())

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._face_mesh.detect(image)
            if not getattr(result, "face_landmarks", None):
                return {"gaze": "away", "blink": False, "ear": 0.0}

            landmarks = result.face_landmarks[0]
            left_iris = landmarks[468]
            right_iris = landmarks[473]
            left_corner_outer, left_corner_inner = landmarks[33], landmarks[133]
            right_corner_inner, right_corner_outer = landmarks[362], landmarks[263]
            left_upper, left_lower = landmarks[159], landmarks[145]
            right_upper, right_lower = landmarks[386], landmarks[374]

            left_x = (left_iris.x - left_corner_outer.x) / max(1e-6, left_corner_inner.x - left_corner_outer.x)
            left_y = (left_iris.y - left_upper.y) / max(
                1e-6, abs(left_lower.y - left_upper.y)
            )
            right_x = (right_iris.x - right_corner_inner.x) / max(1e-6, right_corner_outer.x - right_corner_inner.x)
            right_y = (right_iris.y - right_upper.y) / max(
                1e-6, abs(right_lower.y - right_upper.y)
            )

            center_x = (left_x + right_x) / 2.0
            center_y = (left_y + right_y) / 2.0
            offset_x = center_x - 0.5
            offset_y = center_y - 0.5

            if abs(offset_x) <= GAZE_CENTER_THRESHOLD and abs(offset_y) <= GAZE_CENTER_THRESHOLD:
                gaze = "center"
            elif offset_x < -GAZE_CENTER_THRESHOLD:
                gaze = "left"
            elif offset_x > GAZE_CENTER_THRESHOLD:
                gaze = "right"
            elif offset_y > GAZE_CENTER_THRESHOLD:
                gaze = "down"
            else:
                gaze = "center"

            ear_left = self._eye_aspect_ratio(landmarks, (33, 160, 158, 133, 153, 144))
            ear_right = self._eye_aspect_ratio(landmarks, (362, 385, 387, 263, 373, 380))
            ear = (ear_left + ear_right) / 2.0
            blink_now = ear < BLINK_EAR_THRESHOLD
            self._blink_frames = self._blink_frames + 1 if blink_now else 0
            blink_event = False
            if self._blink_frames >= 2 and not self._blink_active:
                blink_event = True
                self._blink_active = True
            elif not blink_now:
                self._blink_active = False
            return {"gaze": gaze, "blink": blink_event, "ear": float(ear)}
        except Exception:
            return asdict(EyeGazeResult())

    def reset(self) -> None:
        self._blink_frames = 0
        self._blink_active = False


def analyze_eye_gaze(frame: np.ndarray | None) -> dict[str, float | str | bool]:
    return EyeGazeAnalyzer().analyze(frame)
