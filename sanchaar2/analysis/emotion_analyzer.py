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
class EmotionResult:
    happy: float = 0.0
    neutral: float = 1.0
    sad: float = 0.0
    anxious: float = 0.0
    surprised: float = 0.0
    angry: float = 0.0
    dominant: str = "neutral"


class EmotionAnalyzer:
    def __init__(self) -> None:
        manager = get_model_manager()
        self._emotion_model = manager.get_model("emotion")
        self._face_detector = None
        if cv2 is not None:
            try:
                cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                self._face_detector = cv2.CascadeClassifier(cascade_path)
            except Exception:
                self._face_detector = None

    @staticmethod
    def _distance(a: Any, b: Any) -> float:
        return float(np.linalg.norm(np.array([a.x, a.y]) - np.array([b.x, b.y])))

    @staticmethod
    def _clip01(value: float) -> float:
        return float(np.clip(value, 0.0, 1.0))

    @staticmethod
    def _blendshape_value(blendshapes: Any, name: str) -> float:
        if not blendshapes:
            return 0.0
        for category in blendshapes:
            category_name = str(getattr(category, "category_name", getattr(category, "label", ""))).lower()
            if category_name == name.lower():
                return float(getattr(category, "score", 0.0))
        return 0.0

    def analyze(self, frame: np.ndarray | None) -> dict[str, float | str]:
        neutral = EmotionResult()
        if frame is None or cv2 is None:
            return asdict(neutral)

        if self._emotion_model is not None and self._face_detector is not None:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self._face_detector.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(48, 48))
                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda item: item[2] * item[3])
                    crop = frame[y : y + h, x : x + w]
                    if crop.size > 0:
                        rgb_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                        if mp is not None:
                            image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_crop)
                            result = self._emotion_model.detect(image)
                            blendshapes = result.face_blendshapes[0] if getattr(result, "face_blendshapes", None) else []
                        else:
                            blendshapes = []

                        scores = {
                            "happy": self._blendshape_value(blendshapes, "mouthSmileLeft")
                            + self._blendshape_value(blendshapes, "mouthSmileRight")
                            + self._blendshape_value(blendshapes, "cheekSquintLeft")
                            + self._blendshape_value(blendshapes, "cheekSquintRight"),
                            "sad": self._blendshape_value(blendshapes, "mouthFrownLeft")
                            + self._blendshape_value(blendshapes, "mouthFrownRight")
                            + self._blendshape_value(blendshapes, "browInnerUp") * 0.5,
                            "anxious": self._blendshape_value(blendshapes, "eyeWideLeft")
                            + self._blendshape_value(blendshapes, "eyeWideRight")
                            + self._blendshape_value(blendshapes, "browInnerUp") * 0.3,
                            "surprised": self._blendshape_value(blendshapes, "jawOpen")
                            + self._blendshape_value(blendshapes, "eyeWideLeft")
                            + self._blendshape_value(blendshapes, "eyeWideRight"),
                            "angry": self._blendshape_value(blendshapes, "browDownLeft")
                            + self._blendshape_value(blendshapes, "browDownRight")
                            + self._blendshape_value(blendshapes, "mouthPressLeft")
                            + self._blendshape_value(blendshapes, "mouthPressRight"),
                            "neutral": self._blendshape_value(blendshapes, "eyeBlinkLeft")
                            + self._blendshape_value(blendshapes, "eyeBlinkRight"),
                        }
                        scores = {key: self._clip01(value) for key, value in scores.items()}
                        if scores["neutral"] == 0.0:
                            scores["neutral"] = self._clip01(1.0 - max(scores.values()) * 0.92)
                        dominant = max(scores, key=scores.get)
                        scores["dominant"] = dominant
                        return scores
            except Exception:
                pass

        try:
            return asdict(neutral)
        except Exception:
            return asdict(neutral)


def analyze_emotion(frame: np.ndarray | None) -> dict[str, float | str]:
    return EmotionAnalyzer().analyze(frame)
