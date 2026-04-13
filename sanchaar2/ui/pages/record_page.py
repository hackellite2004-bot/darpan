from __future__ import annotations

import json
import queue
import time
from pathlib import Path
from typing import Any

import numpy as np
from PySide6.QtCore import QObject, QRunnable, QThread, QThreadPool, QTimer, Qt, Signal
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config import COLOR_ACCENT, COLOR_DANGER, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING
from core.recorder import SessionRecorder
from core.session_manager import SessionManager
from analysis.emotion_analyzer import EmotionAnalyzer
from analysis.eye_gaze_analyzer import EyeGazeAnalyzer
from analysis.gesture_analyzer import GestureAnalyzer
from analysis.pose_analyzer import PoseAnalyzer
from ui.components.live_overlay import LiveOverlay

try:
    import cv2
except Exception:  # pragma: no cover
    cv2 = None

try:
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvasAgg
except Exception:  # pragma: no cover
    Figure = None
    FigureCanvasAgg = None


class LiveAnalysisWorker(QThread):
    result_ready = Signal(dict)

    def __init__(self, frame_queue: "queue.Queue[np.ndarray]", parent=None):
        super().__init__(parent)
        self.frame_queue = frame_queue
        self.running = True
        self.emotion_analyzer = EmotionAnalyzer()
        self.gaze_analyzer = EyeGazeAnalyzer()
        self.pose_analyzer = PoseAnalyzer()
        self.gesture_analyzer = GestureAnalyzer()

    def stop(self) -> None:
        self.running = False

    def run(self) -> None:
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=0.2)
            except queue.Empty:
                continue
            emotion = self.emotion_analyzer.analyze(frame)
            gaze = self.gaze_analyzer.analyze(frame)
            posture = self.pose_analyzer.analyze(frame)
            gesture = self.gesture_analyzer.analyze(frame)
            live_score = float(
                emotion.get("happy", 0.0) * 30.0
                + (100.0 if gaze.get("gaze") == "center" else 0.0)
                + float(posture.get("posture_score", 0.0)) * 100.0
                + float(gesture.get("positive_pct", 0.0))
            ) / 3.0
            self.result_ready.emit(
                {
                    "emotion": emotion,
                    "gaze": gaze,
                    "posture": posture,
                    "gesture": gesture,
                    "live_score": live_score,
                }
            )
            time.sleep(0.1)


class AnalysisSignals(QObject):
    progress = Signal(str)
    finished = Signal(dict)
    error = Signal(str)


class AnalysisWorker(QRunnable):
    def __init__(self, session_manager: SessionManager, user: dict[str, Any], video_path: Path, audio_path: Path, frame_scores: list[tuple[float, float]]):
        super().__init__()
        self.session_manager = session_manager
        self.user = user
        self.video_path = video_path
        self.audio_path = audio_path
        self.frame_scores = frame_scores
        self.signals = AnalysisSignals()

    def run(self) -> None:
        try:
            self.signals.progress.emit("Transcribing speech...")
            payload = self.session_manager.build_result_payload(self.user, self.video_path, self.audio_path, self.frame_scores)
            result = dict(payload.metrics)
            if payload.report_path:
                result["report_path"] = str(payload.report_path)
            self.signals.progress.emit("Saving session data...")
            self.signals.finished.emit(result)
        except Exception as exc:
            self.signals.error.emit(str(exc))


class RecordPage(QWidget):
    navigate_requested = Signal(str)
    analysis_finished = Signal(dict)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.session_manager = main_window.session_manager if main_window is not None else SessionManager(Path("data/sanchaar.db"))
        self.recorder = SessionRecorder()
        self.thread_pool = QThreadPool.globalInstance()
        self.frame_queue: "queue.Queue[np.ndarray]" = queue.Queue(maxsize=3)
        self.live_worker: LiveAnalysisWorker | None = None
        self.recording = False
        self.paused = False
        self.current_user: dict[str, Any] | None = None
        self.session_dir: Path | None = None
        self.video_path: Path | None = None
        self.audio_path: Path | None = None
        self.frame_scores: list[tuple[float, float]] = []
        self.calibration_data: dict[str, Any] | None = None
        self.calibration_mode = False
        self.calibration_samples: list[dict[str, float]] = []
        self.latest_live: dict[str, Any] = {
            "emotion": {"dominant": "neutral"},
            "gaze": {"gaze": "center"},
            "posture": {"posture_score": 1.0, "slouching": False},
            "gesture": {"gesture_type": "neutral", "positive_pct": 0.0, "nervous_pct": 0.0},
            "live_score": 0.0,
        }

        outer = QVBoxLayout(self)
        outer.setContentsMargins(20, 20, 20, 20)
        outer.setSpacing(16)

        self.loading_overlay = QFrame(self)
        self.loading_overlay.setVisible(False)
        self.loading_overlay.setStyleSheet("background: rgba(8, 22, 34, 0.90); border: 1px solid rgba(255,255,255,0.10); border-radius: 18px;")
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.addStretch(1)
        self.loading_label = QLabel("Analysing your session...")
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.setStyleSheet("font-size: 24px; font-weight: 700; color: white;")
        self.loading_subtitle = QLabel("")
        self.loading_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_subtitle.setStyleSheet("color: #F2F7FB; font-size: 14px;")
        self.loading_progress = QProgressBar()
        self.loading_progress.setRange(0, 100)
        self.loading_progress.setValue(12)
        self.loading_progress.setFixedHeight(14)
        self.loading_progress.setVisible(True)
        overlay_layout.addWidget(self.loading_label)
        overlay_layout.addWidget(self.loading_subtitle)
        overlay_layout.addWidget(self.loading_progress)
        overlay_layout.addStretch(1)

        content = QHBoxLayout()
        content.setSpacing(16)

        self.video_card = QFrame()
        self.video_card.setProperty("class", "card")
        video_layout = QVBoxLayout(self.video_card)
        self.video_label = QLabel("Webcam preview")
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setStyleSheet("background: #090913; border-radius: 16px;")
        video_layout.addWidget(self.video_label)
        content.addWidget(self.video_card, 3)

        self.side_card = QFrame()
        self.side_card.setProperty("class", "card")
        side_layout = QVBoxLayout(self.side_card)
        self.live_overlay = LiveOverlay()
        self.emotion_bar = QProgressBar()
        self.gaze_label = QLabel("Gaze: --")
        self.speaking_label = QLabel("Speaking: idle")
        self.wpm_label = QLabel("WPM: --")
        self.posture_label = QLabel("Posture: good")
        self.posture_label.setStyleSheet(f"font-weight: 700; color: {COLOR_SUCCESS};")
        self.emotion_bar.setRange(0, 100)
        self.emotion_bar.setValue(0)
        self.emotion_bar.setTextVisible(True)
        side_layout.addWidget(QLabel("Live metrics"))
        side_layout.addWidget(self.live_overlay)
        side_layout.addWidget(QLabel("Emotion"))
        side_layout.addWidget(self.emotion_bar)
        side_layout.addWidget(self.gaze_label)
        side_layout.addWidget(self.speaking_label)
        side_layout.addWidget(self.wpm_label)
        side_layout.addWidget(self.posture_label)
        side_layout.addStretch(1)
        content.addWidget(self.side_card, 2)

        outer.addLayout(content, 1)

        controls = QHBoxLayout()
        controls.setSpacing(12)
        self.record_button = QPushButton("Record")
        self.record_button.setStyleSheet("font-size: 18px; font-weight: 700; background: #FF6B6B; min-width: 120px; min-height: 52px; border-radius: 26px;")
        self.stop_button = QPushButton("Stop")
        self.pause_button = QPushButton("Pause")
        self.back_button = QPushButton("Back")
        self.back_button.setObjectName("SecondaryButton")
        self.timer_label = QLabel("00:00")
        self.timer_label.setStyleSheet("font-size: 20px; font-weight: 700;")
        self.record_button.clicked.connect(self.toggle_recording)
        self.stop_button.clicked.connect(self.stop_recording)
        self.pause_button.clicked.connect(self.toggle_pause)
        self.back_button.clicked.connect(lambda: self._navigate("home"))
        controls.addWidget(self.record_button)
        controls.addWidget(self.pause_button)
        controls.addWidget(self.stop_button)
        controls.addStretch(1)
        controls.addWidget(self.timer_label)
        controls.addWidget(self.back_button)
        outer.addLayout(controls)

        self.live_timer = QTimer(self)
        self.live_timer.timeout.connect(self.update_frame)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_timer)
        self.analysis_timer = QTimer(self)
        self.analysis_timer.timeout.connect(self.push_frame_to_analysis)
        self.loading_timer = QTimer(self)
        self.loading_timer.timeout.connect(self._animate_loading_progress)
        self.loading_timer.setInterval(80)

    def _show_loading_overlay(self, title: str, subtitle: str) -> None:
        self.loading_label.setText(title)
        self.loading_subtitle.setText(subtitle)
        self.loading_progress.setRange(0, 100)
        self.loading_progress.setValue(12)
        self.loading_overlay.setGeometry(self.rect())
        self.loading_overlay.raise_()
        self.loading_overlay.show()
        self.loading_timer.start()
        QApplication.processEvents()

    def _hide_loading_overlay(self) -> None:
        self.loading_timer.stop()
        self.loading_overlay.hide()

    def _animate_loading_progress(self) -> None:
        value = self.loading_progress.value()
        if value < 90:
            self.loading_progress.setValue(value + 2)
        else:
            self.loading_progress.setValue(76)

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        self.calibration_data = None
        self.calibration_mode = False
        self.calibration_samples = []
        if self.main_window is not None and user:
            calibration = self.main_window.session_manager.get_calibration_snapshot()
            if calibration and calibration.get("completed_at"):
                self.calibration_data = calibration
            else:
                self.calibration_mode = True
                self.loading_label.setText("Calibration needed")
                self.loading_subtitle.setText("We will collect a quick baseline before the first real recording.")

    def _ensure_session_manager(self) -> None:
        if self.main_window is not None:
            self.session_manager = self.main_window.session_manager

    def toggle_recording(self) -> None:
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        self._ensure_session_manager()
        self.session_dir = self.session_manager.create_session_dir()
        self.recorder.start(self.session_dir)
        self.frame_scores = []
        self.calibration_samples = []
        if self.current_user and self.main_window is not None:
            calibration = self.main_window.session_manager.get_calibration_snapshot()
            self.calibration_mode = not bool(calibration.get("completed_at"))
        self.recording = True
        self.paused = False
        self.record_button.setText("Recording")
        self.record_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.live_timer.start(33)
        self.timer.start(1000)
        self.analysis_timer.start(100)
        self.live_worker = LiveAnalysisWorker(self.frame_queue)
        self.live_worker.result_ready.connect(self.apply_live_analysis)
        self.live_worker.start()
        if self.calibration_mode:
            self._show_loading_overlay(
                "Calibration in progress",
                "Hold a normal speaking posture for a few seconds. This helps the app learn your baseline.",
            )

    def toggle_pause(self) -> None:
        if not self.recording:
            return
        if self.paused:
            self.recorder.resume()
            self.paused = False
            self.pause_button.setText("Pause")
        else:
            self.recorder.pause()
            self.paused = True
            self.pause_button.setText("Resume")

    def stop_recording(self) -> None:
        if not self.recording:
            return
        self.recording = False
        self.live_timer.stop()
        self.timer.stop()
        self.analysis_timer.stop()
        if self.live_worker is not None:
            self.live_worker.stop()
            self.live_worker.wait(1500)
        try:
            self.video_path, self.audio_path = self.recorder.stop()
        except Exception as exc:
            QMessageBox.critical(self, "Recording error", str(exc))
            self.record_button.setEnabled(True)
            self.record_button.setText("Record")
            return
        if self.calibration_mode and self.current_user and self.main_window is not None:
            self._save_calibration_from_live_data()
        self._show_loading_overlay(
            "Analyzing your session...",
            "Transcribing speech, analyzing emotions, posture, gestures, and tone...",
        )
        worker = AnalysisWorker(self.session_manager, self.current_user or {}, self.video_path, self.audio_path, self.frame_scores)
        worker.signals.progress.connect(self._on_analysis_progress)
        worker.signals.finished.connect(self._analysis_finished)
        worker.signals.error.connect(self._analysis_failed)
        self.thread_pool.start(worker)

    def _on_analysis_progress(self, text: str) -> None:
        self.loading_subtitle.setText(text)
        current = self.loading_progress.value()
        self.loading_progress.setValue(min(95, max(current + 6, 30)))
        QApplication.processEvents()

    def _analysis_failed(self, message: str) -> None:
        self._hide_loading_overlay()
        QMessageBox.warning(self, "Analysis failed", message)
        self.record_button.setEnabled(True)
        self.record_button.setText("Record")

    def _analysis_finished(self, result: dict[str, Any]) -> None:
        self.loading_progress.setValue(100)
        self._hide_loading_overlay()
        result = dict(result)
        result["video_path"] = str(self.video_path) if self.video_path else ""
        result["audio_path"] = str(self.audio_path) if self.audio_path else ""
        result["session_dir"] = str(self.session_dir) if self.session_dir else ""
        result["frame_scores"] = self.frame_scores
        if self.session_dir is not None:
            self._write_session_artifacts(result, self.session_dir)
        if self.current_user:
            session_id = self.session_manager.save_complete_session(self.current_user["id"], result)
            result["session_id"] = session_id
        self.analysis_finished.emit(result)
        if self.main_window is not None:
            self.main_window.set_session_result(result)
            self.main_window.navigate("results")
        self.record_button.setEnabled(True)
        self.record_button.setText("Record")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        if self.loading_overlay.isVisible():
            self.loading_overlay.setGeometry(self.rect())
            self.loading_overlay.raise_()

    def _save_calibration_from_live_data(self) -> None:
        if not self.current_user or self.main_window is None:
            return
        calibration_source = self.calibration_samples or [{
            "posture": float(self.latest_live.get("posture", {}).get("posture_score", 0.5)),
            "eye_center": 100.0 if self.latest_live.get("gaze", {}).get("gaze") == "center" else 0.0,
            "emotion_neutral": float(self.latest_live.get("emotion", {}).get("neutral", 1.0)),
            "gesture_positive": float(self.latest_live.get("gesture", {}).get("positive_pct", 0.0)),
            "voice_score": float(self.latest_live.get("live_score") or 0.0),
        }]
        posture_samples = [float(item.get("posture", 0.5)) for item in calibration_source]
        eye_samples = [float(item.get("eye_center", 50.0)) for item in calibration_source]
        emotion_samples = [float(item.get("emotion_neutral", 0.5)) for item in calibration_source]
        gesture_samples = [float(item.get("gesture_positive", 0.0)) for item in calibration_source]
        voice_samples = [float(item.get("voice_score", 0.0)) for item in calibration_source]
        face_impression = {
            "summary": "Baseline calibration captured.",
            "confidence": 0.68,
            "what_it_says": "This is your normal speaking baseline under relaxed conditions.",
            "real_life_example": "Use this as the starting point for classroom answers, introductions, and interviews.",
        }
        calibration = {
            "posture_baseline": float(np.mean(posture_samples)) if posture_samples else 0.5,
            "eye_baseline": float(np.mean(eye_samples)) if eye_samples else 50.0,
            "emotion_baseline": float(np.mean(emotion_samples)) if emotion_samples else 0.5,
            "gesture_baseline": float(np.mean(gesture_samples)) if gesture_samples else 0.0,
            "voice_baseline": float(np.mean(voice_samples)) if voice_samples else 0.0,
            "face_impression": face_impression,
            "confidence_threshold": 55.0,
        }
        self.main_window.session_manager.save_user_calibration(self.current_user["id"], calibration)
        self.calibration_data = calibration
        self.calibration_mode = False

    def _write_session_artifacts(self, result: dict[str, Any], session_dir: Path) -> None:
        try:
            results_path = session_dir / "results.json"
            with results_path.open("w", encoding="utf-8") as handle:
                json.dump(result, handle, indent=2, default=str)
        except Exception:
            pass

        try:
            if Figure is None or FigureCanvasAgg is None:
                return
            report_path = session_dir / "report.png"
            figure = Figure(figsize=(8, 5), dpi=140)
            canvas = FigureCanvasAgg(figure)
            axis = figure.add_subplot(111)
            labels = ["Confidence", "Eye", "Posture", "Speech", "Voice"]
            values = [
                float(result.get("confidence_score") or 0.0),
                float(result.get("eye_center_pct") or 0.0),
                float(result.get("posture_score") or 0.0) * 100.0,
                float(result.get("wpm") or 0.0),
                float(result.get("voice_score") or 0.0) * 100.0,
            ]
            axis.bar(labels, values, color=[COLOR_PRIMARY, COLOR_ACCENT, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER])
            axis.set_ylim(0, max(100.0, max(values) * 1.15 if values else 100.0))
            axis.set_title("Session summary")
            figure.tight_layout()
            canvas.print_png(str(report_path))
        except Exception:
            pass

    def update_timer(self) -> None:
        elapsed = int(self.recorder.get_elapsed_seconds())
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.timer_label.setText(f"{minutes:02d}:{seconds:02d}")

    def push_frame_to_analysis(self) -> None:
        if not self.recording:
            return
        frame = self.recorder.get_live_frame()
        if frame is None:
            return
        if self.frame_queue.full():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                pass
        try:
            self.frame_queue.put_nowait(frame.copy())
        except queue.Full:
            pass

    def apply_live_analysis(self, data: dict[str, Any]) -> None:
        self.latest_live = data
        emotion = data.get("emotion", {})
        gaze = data.get("gaze", {})
        posture = data.get("posture", {})
        gesture = data.get("gesture", {})
        score = float(data.get("live_score") or 0.0)
        self.emotion_bar.setValue(max(0, min(100, int(score))))
        self.gaze_label.setText(f"Gaze: {gaze.get('gaze', 'center').title()}")
        posture_state = "Good" if posture.get("posture_good") else "Warning"
        if posture.get("slouching"):
            posture_state = "Slouching"
        self.posture_label.setText(f"Posture: {posture_state}")
        self.speaking_label.setText(f"Gesture: {gesture.get('gesture_type', 'neutral').title()}")
        self.wpm_label.setText("Speech: captured and analyzed after stop")
        posture_level = "good" if posture.get("posture_good") else ("warning" if not posture.get("slouching") else "bad")
        self.live_overlay.set_state(
            emotion.get("dominant", "neutral"),
            gaze.get("gaze", "center"),
            posture_level,
            self.timer_label.text(),
            float(self.latest_live.get("wpm") or 0.0),
            score,
        )
        self.frame_scores.append((self.recorder.get_elapsed_seconds(), float(score)))

    def update_frame(self) -> None:
        frame = self.recorder.get_live_frame()
        if frame is None or frame.size == 0:
            return
        try:
            frame = self._draw_frame_overlays(frame)
        except Exception:
            frame = frame.copy()
        if cv2 is not None:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb.shape
            image = QImage(rgb.data, width, height, channel * width, QImage.Format.Format_RGB888)
            self.video_label.setPixmap(QPixmap.fromImage(image).scaled(self.video_label.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))

    @staticmethod
    def _hex_to_bgr(color: str) -> tuple[int, int, int]:
        if not color:
            return (255, 255, 255)
        color = color.strip()
        if color.startswith("#"):
            color = color[1:]
        if len(color) != 6:
            return (255, 255, 255)
        try:
            red = int(color[0:2], 16)
            green = int(color[2:4], 16)
            blue = int(color[4:6], 16)
            return (blue, green, red)
        except Exception:
            return (255, 255, 255)

    def _draw_frame_overlays(self, frame: np.ndarray) -> np.ndarray:
        if cv2 is None:
            return frame
        canvas = frame.copy()
        emotion = str(self.latest_live.get("emotion", {}).get("dominant", "neutral")).title()
        gaze = str(self.latest_live.get("gaze", {}).get("gaze", "center")).title()
        posture = "Good" if self.latest_live.get("posture", {}).get("posture_good", True) else "Slouch"
        timer = self.timer_label.text()
        overlay_specs = [
            ((16, 16), emotion, COLOR_PRIMARY),
            ((canvas.shape[1] - 220, 16), gaze, COLOR_ACCENT),
            ((16, canvas.shape[0] - 24), posture, COLOR_SUCCESS if posture == "Good" else COLOR_WARNING),
            ((canvas.shape[1] - 130, canvas.shape[0] - 24), timer, COLOR_DANGER),
        ]
        for (x, y), text, color in overlay_specs:
            cv2.rectangle(canvas, (x - 8, y - 28), (x + 160, y + 4), (15, 15, 26), -1)
            cv2.putText(
                canvas,
                text,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                self._hex_to_bgr(color),
                2,
                cv2.LINE_AA,
            )
        return canvas

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        self.loading_overlay.setGeometry(self.rect())
