"""
Enhanced Emotion Analyzer with ML Model Integration
Combines geometric heuristics with CNN predictions for improved accuracy.
"""

from __future__ import annotations

from typing import Any, Optional
import numpy as np

try:
    import cv2
    import mediapipe as mp
except ImportError:
    cv2 = None
    mp = None


class EnhancedEmotionAnalyzer:
    """
    Emotion detection combining:
    1. Geometric heuristics (current implementation)
    2. Pre-trained CNN model (FER2013)
    3. Voting ensemble for confidence
    """

    # Emotion weighting for ensemble
    HEURISTIC_WEIGHT = 0.5  # Geometric features
    MODEL_WEIGHT = 0.5  # CNN predictions

    EMOTION_LABELS = ["angry", "disgusted", "fearful", "happy", "neutral", "sad", "surprised"]

    def __init__(self, use_model: bool = True):
        """
        Initialize emotion analyzer.
        
        Args:
            use_model: Whether to use pre-trained model if available
        """
        self.use_model = use_model
        self.model = None
        self.face_cascade = None

        if use_model:
            self._load_model()

        self._init_face_cascade()

    def _load_model(self):
        """Load pre-trained emotion model."""
        try:
            from analysis.model_manager import get_model_manager

            manager = get_model_manager()
            self.model = manager.get_model("emotion")

            if self.model:
                print("✅ Enhanced emotion analyzer loaded (using CNN model)")
            else:
                print("⚠️ Using geometric heuristics only (model not available)")

        except Exception as e:
            print(f"Warning: Could not load emotion model: {e}")
            self.model = None

    def _init_face_cascade(self):
        """Initialize Haar cascade for face detection (fallback)."""
        try:
            cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
        except Exception:
            self.face_cascade = None

    def predict_emotion_cnn(self, face_roi: np.ndarray) -> dict[str, float]:
        """
        Predict emotion using CNN model.
        
        Args:
            face_roi: Face region of interest image (grayscale, 48x48)
            
        Returns:
            Dictionary with emotion probabilities
        """
        if self.model is None:
            return {}

        try:
            # Normalize input
            face_input = face_roi.astype("float32") / 255.0
            face_input = np.expand_dims(face_input, axis=0)
            face_input = np.expand_dims(face_input, axis=-1)

            # Predict
            predictions = self.model.predict(face_input, verbose=0)[0]

            # Map to emotion labels
            emotion_probs = {
                label: float(prob) for label, prob in zip(self.EMOTION_LABELS, predictions)
            }

            return emotion_probs

        except Exception as e:
            print(f"Error in CNN prediction: {e}")
            return {}

    def predict_emotion_geometric(self, face_landmarks: Any) -> dict[str, float]:
        """
        Predict emotion using geometric features (current heuristic method).
        
        Args:
            face_landmarks: MediaPipe face landmarks
            
        Returns:
            Dictionary with emotion scores
        """
        try:
            from analysis.emotion_analyzer import EmotionAnalyzer

            # Use existing heuristic analyzer
            analyzer = EmotionAnalyzer()
            emotions = analyzer.analyze(face_landmarks)

            return emotions

        except Exception as e:
            print(f"Error in geometric prediction: {e}")
            return {}

    def analyze_with_ensemble(
        self, face_roi: Optional[np.ndarray] = None, face_landmarks: Optional[Any] = None
    ) -> dict[str, Any]:
        """
        Analyze emotion using ensemble of geometric + CNN predictions.
        
        Args:
            face_roi: Face region (grayscale, 48x48)
            face_landmarks: MediaPipe landmarks
            
        Returns:
            Ensemble emotion predictions with confidence
        """
        ensemble_emotions = {label: 0.0 for label in self.EMOTION_LABELS}
        used_methods = []

        # Get CNN prediction
        if face_roi is not None and self.model is not None:
            try:
                cnn_emotions = self.predict_emotion_cnn(face_roi)
                for label in self.EMOTION_LABELS:
                    ensemble_emotions[label] += self.MODEL_WEIGHT * cnn_emotions.get(label, 0.0)
                used_methods.append("CNN")
            except Exception as e:
                print(f"CNN prediction failed: {e}")

        # Get geometric prediction
        if face_landmarks is not None:
            try:
                geo_emotions = self.predict_emotion_geometric(face_landmarks)
                for label in self.EMOTION_LABELS:
                    ensemble_emotions[label] += self.HEURISTIC_WEIGHT * geo_emotions.get(label, 0.0)
                used_methods.append("Geometric")
            except Exception as e:
                print(f"Geometric prediction failed: {e}")

        # Normalize
        total_weight = sum(self.HEURISTIC_WEIGHT if "Geometric" in used_methods else 0,
                          self.MODEL_WEIGHT if "CNN" in used_methods else 0)

        if total_weight > 0:
            for label in ensemble_emotions:
                ensemble_emotions[label] /= total_weight

        # Get dominant emotion
        dominant = max(ensemble_emotions.items(), key=lambda x: x[1])

        return {
            "emotions": ensemble_emotions,
            "dominant": dominant[0],
            "confidence": dominant[1],
            "methods": used_methods,
            "is_ensemble": len(used_methods) > 1,
        }


# Optional: Enhanced gesture analyzer with model
class EnhancedGestureAnalyzer:
    """Gesture recognition using MediaPipe Hands + custom classifier."""

    def __init__(self):
        """Initialize gesture analyzer."""
        try:
            from analysis.model_manager import get_model_manager

            manager = get_model_manager()
            self.hands_model = manager.get_model("gesture")
            print("✅ Enhanced gesture analyzer ready (MediaPipe Hands)")

        except Exception as e:
            print(f"⚠️ Could not initialize gesture analyzer: {e}")
            self.hands_model = None

    def classify_hand_gesture(self, hand_landmarks: np.ndarray) -> str:
        """
        Classify hand gesture based on landmarks.
        
        Args:
            hand_landmarks: 21 hand landmarks (normalized)
            
        Returns:
            Gesture type: 'open', 'closed', 'pointing', 'thumbs_up', etc.
        """
        try:
            if hand_landmarks is None or len(hand_landmarks) < 21:
                return "unknown"

            # Calculate hand spread (distance between fingers)
            thumb_tip = hand_landmarks[4][:2]
            index_tip = hand_landmarks[8][:2]
            pinky_tip = hand_landmarks[20][:2]

            # Calculate distances
            thumb_to_index = np.linalg.norm(index_tip - thumb_tip)
            thumb_to_pinky = np.linalg.norm(pinky_tip - thumb_tip)
            index_to_pinky = np.linalg.norm(pinky_tip - index_tip)

            spread = (thumb_to_index + thumb_to_pinky + index_to_pinky) / 3.0

            # Simple classification
            if spread > 0.15:
                return "open_hand"
            elif spread < 0.05:
                return "closed_fist"
            elif thumb_to_index > thumb_to_pinky:
                return "pointing"
            else:
                return "neutral_hand"

        except Exception as e:
            print(f"Error classifying gesture: {e}")
            return "unknown"


# Optional: Enhanced gaze analyzer
class EnhancedGazeAnalyzer:
    """Gaze direction estimation with refined accuracy."""

    GAZE_ZONES = ["center", "left", "right", "up", "down", "away"]

    def __init__(self):
        """Initialize gaze analyzer."""
        try:
            from analysis.model_manager import get_model_manager

            manager = get_model_manager()
            self.face_mesh = manager.get_model("gaze")
            print("✅ Enhanced gaze analyzer ready (MediaPipe Face Mesh)")

        except Exception as e:
            print(f"⚠️ Could not initialize gaze analyzer: {e}")
            self.face_mesh = None

    def estimate_gaze_direction(self, iris_landmarks: np.ndarray) -> dict[str, Any]:
        """
        Estimate gaze direction from iris position.
        
        Args:
            iris_landmarks: Iris landmarks (5 points)
            
        Returns:
            Gaze direction analysis
        """
        try:
            if iris_landmarks is None or len(iris_landmarks) < 5:
                return {"direction": "unknown", "confidence": 0.0}

            # Get iris center
            iris_center = np.mean(iris_landmarks, axis=0)

            # Get left/right eye corners
            # These would come from face mesh landmarks
            # Simplified: assume iris at 0.5 is center
            x_pos = iris_center[0]
            y_pos = iris_center[1]

            # Determine direction
            if 0.4 < x_pos < 0.6 and 0.4 < y_pos < 0.6:
                direction = "center"
                confidence = 1.0
            elif x_pos < 0.4:
                direction = "left"
                confidence = 0.8
            elif x_pos > 0.6:
                direction = "right"
                confidence = 0.8
            elif y_pos < 0.4:
                direction = "up"
                confidence = 0.7
            else:
                direction = "down"
                confidence = 0.7

            return {"direction": direction, "confidence": confidence, "iris_pos": (x_pos, y_pos)}

        except Exception as e:
            print(f"Error estimating gaze: {e}")
            return {"direction": "unknown", "confidence": 0.0}
