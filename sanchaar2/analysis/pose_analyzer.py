from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np

from analysis.model_manager import get_model_manager

from config import SLOUCH_Y_THRESHOLD

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    import mediapipe as mp
except Exception:  # pragma: no cover
    mp = None


@dataclass(slots=True)
class PoseResult:
    posture_good: bool = True
    slouching: bool = False
    head_forward: bool = False
    shoulder_level: bool = True
    posture_score: float = 1.0


class PoseAnalyzer:
    def __init__(self) -> None:
        manager = get_model_manager()
        self._pose = manager.get_model("pose")

    def analyze(self, frame: np.ndarray | None) -> dict[str, float | bool]:
        default = PoseResult()
        if frame is None or self._pose is None or cv2 is None or mp is None:
            return asdict(default)

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = self._pose.detect(image)
            if not getattr(result, "pose_landmarks", None):
                return asdict(default)

            landmarks = result.pose_landmarks[0]
            left_shoulder = landmarks[11]
            right_shoulder = landmarks[12]
            nose = landmarks[0]
            left_ear = landmarks[7]
            right_ear = landmarks[8]

            shoulder_y = (left_shoulder.y + right_shoulder.y) / 2.0
            slouching = shoulder_y > SLOUCH_Y_THRESHOLD
            shoulder_z = (left_shoulder.z + right_shoulder.z) / 2.0
            head_forward = (nose.z - shoulder_z) < -0.08
            shoulder_level = abs(left_shoulder.y - right_shoulder.y) <= 0.05
            ear_line_delta = abs(left_ear.y - right_ear.y)
            head_tilt = ear_line_delta > 0.03
            posture_score = 1.0
            posture_score -= 0.40 if slouching else 0.0
            posture_score -= 0.22 if head_forward else 0.0
            posture_score -= 0.18 if not shoulder_level else 0.0
            posture_score -= 0.12 if head_tilt else 0.0
            posture_score = float(np.clip(posture_score, 0.0, 1.0))

            return {
                "posture_good": posture_score >= 0.7,
                "slouching": slouching,
                "head_forward": head_forward,
                "shoulder_level": shoulder_level,
                "posture_score": posture_score,
            }
        except Exception:
            return asdict(default)


def analyze_pose(frame: np.ndarray | None) -> dict[str, float | bool]:
    return PoseAnalyzer().analyze(frame)
