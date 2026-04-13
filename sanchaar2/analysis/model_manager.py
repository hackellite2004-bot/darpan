"""
Model Manager for Darpan
Manages loading and caching of pre-trained ML models for enhanced accuracy.
Supports emotion, gesture, gaze, and speech emotion recognition.
"""

from __future__ import annotations

import os
import urllib.request
from pathlib import Path
from typing import Any, Optional
import warnings

# Suppress TensorFlow warnings
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("ABSL_MIN_LOG_LEVEL", "3")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("DISABLE_TQDM", "1")
warnings.filterwarnings('ignore')
warnings.filterwarnings("ignore", message=".*unauthenticated requests to the HF Hub.*")

try:
    from transformers.utils import logging as transformers_logging

    transformers_logging.set_verbosity_error()
except Exception:
    pass

try:
    from huggingface_hub.utils import logging as hf_logging

    hf_logging.set_verbosity_error()
except Exception:
    pass

# Model cache directory
MODELS_DIR = Path(__file__).parent.parent / "data" / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task"
HAND_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
POSE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"


def _download_model(url: str, target_path: Path) -> Path | None:
    if target_path.exists() and target_path.stat().st_size > 0:
        return target_path
    try:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(url, target_path)
        return target_path if target_path.exists() else None
    except Exception:
        return None


def _load_mediapipe_vision_task(task_name: str) -> Any:
    """Load a MediaPipe vision task module if available."""
    try:
        module = __import__(
            f"mediapipe.tasks.python.vision.{task_name}",
            fromlist=["dummy"],
        )
        return module
    except Exception:
        return None


def _load_mediapipe_task_instance(task_name: str, model_path: Path) -> Any:
    try:
        from mediapipe.tasks.python.core.base_options import BaseOptions
        from mediapipe.tasks.python import vision
        from mediapipe import Image, ImageFormat  # noqa: F401
    except Exception:
        return None

    try:
        if task_name == "face":
            options = vision.FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_path)),
                num_faces=1,
                output_face_blendshapes=True,
                output_facial_transformation_matrixes=True,
            )
            return vision.FaceLandmarker.create_from_options(options)
        if task_name == "hand":
            options = vision.HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_path)),
                num_hands=2,
            )
            return vision.HandLandmarker.create_from_options(options)
        if task_name == "pose":
            options = vision.PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(model_path)),
                num_poses=1,
                output_segmentation_masks=False,
            )
            return vision.PoseLandmarker.create_from_options(options)
    except Exception:
        return None

    return None


class ModelManager:
    """Centralized management of pre-trained ML models."""

    _instance = None
    _models = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.device = self._get_device()
        self.models_loaded = {}

    def _load_model_by_name(self, model_name: str) -> Any:
        if model_name == "emotion":
            return self.load_emotion_model()
        if model_name == "gesture":
            return self.load_gesture_model()
        if model_name == "gaze":
            return self.load_gaze_estimation_model()
        if model_name == "speech_emotion":
            return self.load_speech_emotion_model()
        if model_name == "face_quality":
            return self.load_face_quality_model()
        if model_name == "pose":
            return self.load_pose_model()
        return None

    @staticmethod
    def _get_device() -> str:
        """Detect CUDA/GPU availability."""
        try:
            import torch

            if torch.cuda.is_available():
                return "cuda"
        except ImportError:
            pass
        return "cpu"

    @staticmethod
    def load_emotion_model() -> Any:
        """
        Load pre-trained emotion detection model.
        Uses FER2013-trained CNN via TensorFlow/Keras.
        
        Returns:
            Loaded emotion detection model
        """
        try:
            model_path = _download_model(FACE_MODEL_URL, MODELS_DIR / "face_emotion_landmarker.task")
            if model_path is None:
                return None
            return _load_mediapipe_task_instance("face", model_path)

        except Exception as e:
            print(f"⚠️ Could not load emotion model: {e}")
            return None

    @staticmethod
    def load_gesture_model() -> Any:
        """
        Load pre-trained gesture recognition model.
        Uses MediaPipe Hands + custom gesture classifier.
        
        Returns:
            Loaded gesture recognition model
        """
        try:
            model_path = _download_model(HAND_MODEL_URL, MODELS_DIR / "hand_landmarker.task")
            if model_path is None:
                return None
            return _load_mediapipe_task_instance("hand", model_path)

        except Exception as e:
            print(f"⚠️ Could not load gesture model: {e}")
            return None

    @staticmethod
    def load_gaze_estimation_model() -> Any:
        """
        Load gaze estimation model using mediapipe + landmarks.
        Returns gaze estimator function.
        
        Returns:
            Gaze estimator function
        """
        try:
            model_path = _download_model(FACE_MODEL_URL, MODELS_DIR / "face_landmarker.task")
            if model_path is None:
                return None
            return _load_mediapipe_task_instance("face", model_path)

        except Exception as e:
            print(f"⚠️ Could not load gaze model: {e}")
            return None

    @staticmethod
    def load_speech_emotion_model() -> Any:
        """
        Load speech emotion recognition model.
        Uses Hugging Face transformers (wav2vec2 + emotion classifier).
        
        Returns:
            Speech emotion classification pipeline
        """
        try:
            from transformers import pipeline

            device = 0 if ModelManager().device == "cuda" else -1
            model_candidates = [
                "superb/wav2vec2-base-superb-er",
                "ehcalabres/wav2vec2-lg-xlsr-en-speech-emotion-recognition",
                "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
            ]

            for model_name in model_candidates:
                try:
                    classifier = pipeline("audio-classification", model=model_name, device=device)
                    return classifier
                except Exception:
                    continue

            return None

        except Exception as e:
            print(f"⚠️ Could not load speech emotion model: {e}")
            print("   Install: pip install transformers torch librosa")
            return None

    @staticmethod
    def load_face_quality_model() -> Any:
        """
        Load face quality assessment model.
        Detects face blur, lighting, pose quality.
        
        Returns:
            Face quality assessor
        """
        try:
            model_path = _download_model(FACE_MODEL_URL, MODELS_DIR / "face_landmarker.task")
            if model_path is None:
                return None
            return _load_mediapipe_task_instance("face", model_path)

        except Exception as e:
            print(f"⚠️ Could not load face quality model: {e}")
            return None

    @staticmethod
    def load_pose_model() -> Any:
        """
        Load pose estimation model (MediaPipe Pose).
        
        Returns:
            Pose estimator
        """
        try:
            model_path = _download_model(POSE_MODEL_URL, MODELS_DIR / "pose_landmarker_lite.task")
            if model_path is None:
                return None
            return _load_mediapipe_task_instance("pose", model_path)

        except Exception as e:
            print(f"⚠️ Could not load pose model: {e}")
            return None

    def get_all_models(self) -> dict[str, Any]:
        """
        Return the current model cache.
        
        Returns:
            Dictionary of loaded models
        """
        return self.models_loaded

    def get_model(self, model_name: str) -> Optional[Any]:
        """
        Get a specific model by name.
        
        Args:
            model_name: Name of model (emotion, gesture, gaze, speech_emotion, etc.)
            
        Returns:
            Loaded model or None
        """
        if model_name not in self.models_loaded:
            self.models_loaded[model_name] = self._load_model_by_name(model_name)
        return self.models_loaded.get(model_name)

    def is_model_available(self, model_name: str) -> bool:
        """Check if a specific model is loaded."""
        return self.get_model(model_name) is not None


# Singleton instance
_model_manager = None


def get_model_manager() -> ModelManager:
    """Get the global model manager instance."""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager
