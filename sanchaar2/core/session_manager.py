from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from analysis.analysis_strategy import build_analysis_profile
from analysis.score_engine import compute_confidence_score
from analysis.session_video_analyzer import analyze_video_session
from analysis.speech_analyzer import analyze_speech
from analysis.voice_tone_analyzer import analyze_voice_tone
from analysis.visualization_engine import VisualizationEngine
from analysis.voice_spectral_analyzer import VoiceSpectralAnalyzer
from analysis.report_generator import ReportGenerator
from analysis.tips_generator import TipsGenerator
from ai.coaching import generate_coaching_tips, generate_face_impression, generate_session_assessment
from config import SESSION_DIR
from core.database import get_last_session_for_user, get_sessions_for_user, get_calibration, save_calibration, upsert_user, save_session

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


@dataclass(slots=True)
class SessionResult:
    session_dir: Path
    video_path: Path
    audio_path: Path
    metrics: dict[str, Any] = field(default_factory=dict)
    analysis: dict[str, Any] = field(default_factory=dict)
    report_path: Path | None = None
    highlight_reel_path: Path | None = None
    session_id: int | None = None


class SessionManager:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.current_user: dict[str, Any] | None = None
        self.current_session_dir: Path | None = None

    def set_user(self, user: dict[str, Any] | None) -> None:
        self.current_user = user

    def create_session_dir(self) -> Path:
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_dir = SESSION_DIR / timestamp
        session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session_dir = session_dir
        return session_dir

    def analyze_recording(self, video_path: Path, audio_path: Path, frame_scores: list[tuple[float, float]] | None = None) -> dict[str, Any]:
        video_metrics = analyze_video_session(str(video_path))
        speech = analyze_speech(audio_path)
        voice = analyze_voice_tone(audio_path)
        face_frame = self._sample_face_frame(video_path)
        face_frames = self._sample_analysis_frames(video_path)

        metrics = {
            "emotion_happy": float(video_metrics.get("emotion_happy", 0.0)),
            "emotion_neutral": float(video_metrics.get("emotion_neutral", 1.0)),
            "emotion_sad": float(video_metrics.get("emotion_sad", 0.0)),
            "emotion_anxious": float(video_metrics.get("emotion_anxious", 0.0)),
            "emotion_surprised": float(video_metrics.get("emotion_surprised", 0.0)),
            "emotion_dominant": str(video_metrics.get("emotion_dominant", "neutral")),
            "eye_center_pct": float(video_metrics.get("eye_center_pct", 0.0)),
            "eye_away_pct": float(video_metrics.get("eye_away_pct", 100.0)),
            "blink_count": int(video_metrics.get("blink_count", 0)),
            "posture_score": float(video_metrics.get("posture_score", 0.5)),
            "slouch_pct": float(video_metrics.get("slouch_pct", 0.0)),
            "gesture_positive_pct": float(video_metrics.get("gesture_positive_pct", 0.0)),
            "gesture_nervous_pct": float(video_metrics.get("gesture_nervous_pct", 0.0)),
            "gesture_type": str(video_metrics.get("gesture_type", "neutral")),
            "wpm": float(speech.get("wpm") or 0.0),
            "filler_count": int(speech.get("total_fillers") or 0),
            "total_fillers": int(speech.get("total_fillers") or 0),
            "filler_words": speech.get("filler_words") or {},
            "pause_count": int(speech.get("pause_count") or len(speech.get("long_pauses") or [])),
            "long_pauses": speech.get("long_pauses") or [],
            "word_count": int(speech.get("word_count") or 0),
            "speech_detected": bool(speech.get("speech_detected") or False),
            "mic_level": float(speech.get("mic_level") or 0.0),
            "speech_issues": speech.get("speech_issues") or [],
            "speech_solutions": speech.get("speech_solutions") or [],
            "voice_energy": float(voice.get("energy_mean") or 0.0),
            "pitch_variation": float(voice.get("pitch_variation") or 0.0),
            "voice_emotion": str(voice.get("voice_emotion") or "neutral"),
            "voice_emotion_confidence": float(voice.get("emotion_confidence") or 0.0),
            "transcript": speech.get("transcript") or "",
            "voice_score": float(voice.get("voice_score") or 0.0),
            "is_monotone": bool(voice.get("is_monotone") or False),
            "is_too_quiet": bool(voice.get("is_too_quiet") or False),
            "is_too_loud": bool(voice.get("is_too_loud") or False),
            "duration_seconds": float(video_metrics.get("duration_seconds") or speech.get("duration") or 0.0),
        }

        heuristic_analysis = compute_confidence_score(metrics)
        # Seed fallback paths with a valid baseline before model calls.
        metrics["confidence_score"] = float(heuristic_analysis["score"])
        metrics["grade"] = str(heuristic_analysis["grade"])
        metrics["analysis_quality_score"] = float(
            heuristic_analysis.get("quality_score")
            or heuristic_analysis["breakdown"].get("quality_score")
            or 0.0
        )
        calibration = self.get_calibration_snapshot()
        analysis_profile = build_analysis_profile(video_metrics, speech, voice, calibration, self.current_user, frame_scores if frame_scores else video_metrics.get("frame_scores", []))
        metrics["analysis_profile"] = analysis_profile
        model_analysis = generate_session_assessment(
            metrics,
            self.current_user.get("name", "User") if self.current_user else "User",
            self.current_user.get("age_group") or "student" if self.current_user else "student",
            face_frames,
            metrics["transcript"],
            analysis_profile,
        )
        metrics["heuristic_analysis"] = heuristic_analysis
        metrics["model_analysis"] = model_analysis
        metrics["confidence_score"] = float(model_analysis.get("final_score") or heuristic_analysis["score"])
        metrics["grade"] = str(model_analysis.get("grade") or heuristic_analysis["grade"])
        metrics["llm_feedback"] = []
        metrics["video_path"] = str(video_path)
        metrics["highlight_reel_path"] = ""
        metrics["face_impression"] = generate_face_impression(metrics, self.current_user.get("name", "User") if self.current_user else "User", self.current_user.get("age_group") or "student" if self.current_user else "student", face_frame)
        tips = generate_coaching_tips(
            metrics
            | {
                "dominant_emotion": metrics["emotion_dominant"],
                "gesture_type": metrics.get("gesture_type", "neutral"),
                "top_filler": self.top_filler(metrics.get("filler_words") or {}),
                "total_fillers": metrics.get("total_fillers", 0),
            },
            self.current_user.get("name", "User") if self.current_user else "User",
            self.current_user.get("age_group") or "student" if self.current_user else "student",
        )
        metrics["llm_feedback"] = tips
        metrics["frame_scores"] = frame_scores if frame_scores else video_metrics.get("frame_scores", [])
        metrics["speech"] = speech
        metrics["voice"] = voice
        metrics["analysis_breakdown"] = heuristic_analysis["breakdown"]
        metrics["confidence_threshold"] = float(calibration.get("confidence_threshold", 55.0))
        metrics["analysis_quality_score"] = float(model_analysis.get("quality_score") or analysis_profile.get("signal_quality") or heuristic_analysis.get("quality_score") or heuristic_analysis["breakdown"].get("quality_score") or 0.0)
        model_confidence = model_analysis.get("confidence_label")
        if isinstance(model_confidence, dict):
            metrics["confidence_label"] = model_confidence
        else:
            metrics["confidence_label"] = self.classify_result(metrics["confidence_score"], metrics["analysis_quality_score"], float(analysis_profile.get("recommended_threshold") or metrics["confidence_threshold"]))
        metrics["uncertain"] = metrics["confidence_label"]["label"] == "uncertain"
        return metrics

    def _sample_face_frame(self, video_path: Path):
        if cv2 is None:
            return None
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return None
        try:
            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total_frames <= 0:
                return None
            capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames // 3))
            ok, frame = capture.read()
            if not ok or frame is None:
                capture.set(cv2.CAP_PROP_POS_FRAMES, max(0, total_frames // 2))
                ok, frame = capture.read()
            if not ok or frame is None:
                return None
            if np is not None and frame.size > 0:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return frame
        finally:
            capture.release()

    def _sample_analysis_frames(self, video_path: Path) -> list[np.ndarray]:
        if cv2 is None:
            return []
        capture = cv2.VideoCapture(str(video_path))
        if not capture.isOpened():
            return []
        try:
            total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            if total_frames <= 0:
                return []
            sample_points = [max(0, total_frames // 6), max(0, total_frames // 2), max(0, (total_frames * 5) // 6)]
            frames: list[np.ndarray] = []
            seen_positions: set[int] = set()
            for position in sample_points:
                if position in seen_positions:
                    continue
                seen_positions.add(position)
                capture.set(cv2.CAP_PROP_POS_FRAMES, position)
                ok, frame = capture.read()
                if not ok or frame is None:
                    continue
                if np is not None and frame.size > 0:
                    frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                else:
                    frames.append(frame)
            return frames
        finally:
            capture.release()

    def get_calibration_snapshot(self) -> dict[str, Any]:
        if not self.current_user:
            return {"confidence_threshold": 55.0}
        calibration = get_calibration(self.db_path, self.current_user["id"])
        if calibration:
            return calibration
        return {"confidence_threshold": 55.0}

    def classify_result(self, score: float, quality_score: float, threshold: float) -> dict[str, Any]:
        if score < threshold or quality_score < 45.0:
            return {"label": "uncertain", "message": "Low confidence: this result should be treated as uncertain."}
        if score >= 80 and quality_score >= 70:
            return {"label": "confident", "message": "High confidence: the detection is strong and stable."}
        return {"label": "moderate", "message": "Moderate confidence: useful but still a bit noisy."}

    def save_user_calibration(self, user_id: str, calibration_data: dict[str, Any]) -> None:
        if self.current_user and self.current_user.get("id") == user_id:
            upsert_user(self.db_path, self.current_user)
        save_calibration(self.db_path, user_id, calibration_data)

    def save_complete_session(self, user_id: str, data: dict[str, Any]) -> int:
        payload = dict(data)
        payload["user_id"] = user_id
        payload.setdefault("llm_feedback", [])
        payload.setdefault("video_path", "")
        payload.setdefault("highlight_reel_path", "")
        if self.current_user and self.current_user.get("id") == user_id:
            upsert_user(self.db_path, self.current_user)
        return save_session(self.db_path, payload)

    @staticmethod
    def top_filler(filler_words: dict[str, int] | None) -> str:
        if not filler_words:
            return "none"
        return max(filler_words.items(), key=lambda item: item[1])[0]

    def get_last_session(self, user_id: str) -> dict[str, Any] | None:
        return get_last_session_for_user(self.db_path, user_id)

    def get_session_history(self, user_id: str) -> list[dict[str, Any]]:
        return get_sessions_for_user(self.db_path, user_id)

    def build_result_payload(self, user: dict[str, Any], video_path: Path, audio_path: Path, frame_scores: list[tuple[float, float]] | None = None) -> SessionResult:
        analysis = self.analyze_recording(video_path, audio_path, frame_scores)
        session_dir = video_path.parent
        result = SessionResult(session_dir=session_dir, video_path=video_path, audio_path=audio_path, metrics=analysis, analysis=analysis)
        
        # Generate visualizations, reports, and tips
        try:
            self._generate_session_artifacts(result, analysis)
        except Exception as e:
            print(f"Warning: Error generating session artifacts: {e}")
        
        return result
    
    def _generate_session_artifacts(self, result: SessionResult, metrics: dict[str, Any]) -> None:
        """Generate visualizations, reports, and tips for the session."""
        session_dir = result.session_dir
        
        # Create visualizations directory
        viz_dir = session_dir / "visualizations"
        viz_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Generate Emotion Distribution Chart
        try:
            emotions = {
                'happy': metrics.get('emotion_happy', 0),
                'neutral': metrics.get('emotion_neutral', 0),
                'sad': metrics.get('emotion_sad', 0),
                'anxious': metrics.get('emotion_anxious', 0),
                'surprised': metrics.get('emotion_surprised', 0),
            }
            emotion_chart = VisualizationEngine.create_emotion_distribution_chart(
                emotions,
                output_path=viz_dir / "emotion_distribution.png"
            )
            if emotion_chart:
                metrics['visualization_emotion'] = str(emotion_chart)
        except Exception as e:
            print(f"Error generating emotion chart: {e}")
        
        # 2. Generate Eye Gaze Chart
        try:
            gaze_data = {
                'Center': metrics.get('eye_center_pct', 0),
                'Right': metrics.get('eye_away_pct', 0) / 2,  # Approximate
                'Left': metrics.get('eye_away_pct', 0) / 2,
                'Away': 0,
            }
            # Filter negative values
            gaze_data = {k: max(0, v) for k, v in gaze_data.items()}
            # Normalize to 100%
            total = sum(gaze_data.values())
            if total > 0:
                gaze_data = {k: (v/total)*100 for k, v in gaze_data.items()}
            
            gaze_chart = VisualizationEngine.create_eye_gaze_chart(
                gaze_data,
                output_path=viz_dir / "eye_gaze.png"
            )
            if gaze_chart:
                metrics['visualization_gaze'] = str(gaze_chart)
        except Exception as e:
            print(f"Error generating gaze chart: {e}")
        
        # 3. Generate Speech Metrics Chart
        try:
            speech_chart = VisualizationEngine.create_speech_metrics_chart(
                wpm=metrics.get('wpm', 0),
                fillers=metrics.get('filler_count', 0),
                pauses=metrics.get('pause_count', 0),
                output_path=viz_dir / "speech_metrics.png"
            )
            if speech_chart:
                metrics['visualization_speech'] = str(speech_chart)
        except Exception as e:
            print(f"Error generating speech metrics chart: {e}")
        
        # 4. Generate Confidence Trend Chart (from frame scores)
        try:
            frame_scores = metrics.get('frame_scores', [])
            if frame_scores and len(frame_scores) > 1:
                scores = [s[1] for s in frame_scores]
                trend_chart = VisualizationEngine.create_confidence_trend_chart(
                    scores,
                    output_path=viz_dir / "confidence_trend.png"
                )
                if trend_chart:
                    metrics['visualization_trend'] = str(trend_chart)
        except Exception as e:
            print(f"Error generating trend chart: {e}")
        
        # 5. Generate Performance Radar Chart
        try:
            performance_metrics = {
                'Eye Contact': min(100, metrics.get('eye_center_pct', 0)),
                'Posture': metrics.get('posture_score', 0),
                'Voice': metrics.get('voice_score', 0),
                'Speech Speed': min(100, max(0, 100 - abs(metrics.get('wpm', 150) - 150) / 1.5)),
                'Emotion Balance': 100 - min(20, metrics.get('emotion_anxious', 0)) * 5,
            }
            radar_chart = VisualizationEngine.create_performance_radar_chart(
                performance_metrics,
                output_path=viz_dir / "performance_radar.png"
            )
            if radar_chart:
                metrics['visualization_radar'] = str(radar_chart)
        except Exception as e:
            print(f"Error generating radar chart: {e}")
        
        # 6. Generate Voice Spectrogram
        try:
            if Path(result.audio_path).exists():
                spec_chart = VisualizationEngine.create_voice_spectrogram(
                    result.audio_path,
                    output_path=viz_dir / "spectrogram.png"
                )
                if spec_chart:
                    metrics['visualization_spectrogram'] = str(spec_chart)
                    
                # Also try chromagram
                chroma_chart = VoiceSpectralAnalyzer.visualize_chromagram(
                    result.audio_path,
                    output_path=viz_dir / "chromagram.png"
                )
                if chroma_chart:
                    metrics['visualization_chromagram'] = str(chroma_chart)
        except Exception as e:
            print(f"Error generating voice visualizations: {e}")
        
        # 7. Generate Excel Report
        try:
            report_path = session_dir / "analysis_report.xlsx"
            generated_report = ReportGenerator.generate_session_report(
                metrics,
                self.current_user,
                output_path=report_path
            )
            if generated_report:
                result.report_path = generated_report
                metrics['report_path'] = str(generated_report)
        except Exception as e:
            print(f"Error generating Excel report: {e}")
        
        # 8. Generate Contextual Tips
        try:
            tips_text = TipsGenerator.get_all_tips(metrics)
            tips_path = session_dir / "contextual_tips.txt"
            with open(tips_path, 'w', encoding='utf-8') as f:
                f.write(tips_text)
            metrics['tips_text'] = tips_text
            metrics['tips_path'] = str(tips_path)
        except Exception as e:
            print(f"Error generating tips: {e}")
