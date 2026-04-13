from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import QUrl

from config import COLOR_ACCENT, COLOR_DANGER, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING
from core.database import get_session_by_id
from ui.components.confidence_ring import ConfidenceRing
from ui.components.gaze_heatmap import GazeHeatmap
from ui.components.metric_card import MetricCard
from analysis.score_engine import classify_confidence

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
except Exception:  # pragma: no cover
    FigureCanvas = None
    Figure = None

try:
    from moviepy import VideoFileClip, concatenate_videoclips
except Exception:  # pragma: no cover
    VideoFileClip = None
    concatenate_videoclips = None


class ResultsPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_user: dict[str, Any] | None = None
        self.current_result: dict[str, Any] | None = None
        self.current_session: dict[str, Any] | None = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(24, 24, 24, 24)
        self.content_layout.setSpacing(16)
        scroll.setWidget(self.content)

        outer = QVBoxLayout(self)
        outer.addWidget(scroll)

        self.summary_card = QFrame()
        self.summary_card.setProperty("class", "card")
        summary_layout = QVBoxLayout(self.summary_card)
        summary_layout.setSpacing(12)

        self.heading = QLabel("Analysis results")
        self.heading.setObjectName("PageHeading")
        self.render_status = QLabel("Ready to display analysis.")
        self.render_status.setProperty("class", "loading")
        self.score_ring = ConfidenceRing()
        self.grade_badge = QLabel("Grade: -")
        self.grade_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.grade_badge.setStyleSheet("font-size: 20px; font-weight: 800; color: white; padding: 10px 16px; border-radius: 14px; background: #6C63FF;")

        score_row = QHBoxLayout()
        score_row.addWidget(self.score_ring)
        side_score = QVBoxLayout()
        self.overall_score = QLabel("0")
        self.overall_score.setStyleSheet("font-size: 52px; font-weight: 800;")
        self.overall_subtitle = QLabel("Confidence score")
        self.overall_subtitle.setProperty("class", "muted")
        side_score.addWidget(self.grade_badge)
        side_score.addWidget(self.overall_score)
        side_score.addWidget(self.overall_subtitle)
        side_score.addStretch(1)
        score_row.addLayout(side_score, 1)

        summary_layout.addWidget(self.heading)
        summary_layout.addWidget(self.render_status)
        summary_layout.addLayout(score_row)

        self.mini_cards_row = QHBoxLayout()
        self.mini_cards: list[MetricCard] = [
            MetricCard("Emotions", "--"),
            MetricCard("Eye Contact", "--"),
            MetricCard("Posture", "--"),
            MetricCard("Speech", "--"),
            MetricCard("Gestures", "--"),
        ]
        for card in self.mini_cards:
            self.mini_cards_row.addWidget(card)
        summary_layout.addLayout(self.mini_cards_row)
        self.content_layout.addWidget(self.summary_card)

        self.coach_card = QFrame()
        self.coach_card.setProperty("class", "card")
        coach_layout = QVBoxLayout(self.coach_card)
        coach_layout.addWidget(QLabel("Your AI Coach Says"))
        self.coach_list = QTextEdit()
        self.coach_list.setReadOnly(True)
        self.coach_list.setMinimumHeight(120)
        coach_layout.addWidget(self.coach_list)
        self.coach_message = QLabel("Add your API key in settings to enable AI coaching feedback.")
        self.coach_message.setProperty("class", "muted")
        coach_layout.addWidget(self.coach_message)
        self.content_layout.addWidget(self.coach_card)

        self.face_card = QFrame()
        self.face_card.setProperty("class", "card")
        face_layout = QVBoxLayout(self.face_card)
        face_layout.addWidget(QLabel("Face impression"))
        self.face_summary = QLabel("No face impression yet.")
        self.face_summary.setWordWrap(True)
        self.face_confidence = QLabel("")
        self.face_confidence.setProperty("class", "muted")
        self.face_example = QLabel("")
        self.face_example.setWordWrap(True)
        self.face_example.setProperty("class", "muted")
        face_layout.addWidget(self.face_summary)
        face_layout.addWidget(self.face_confidence)
        face_layout.addWidget(self.face_example)
        self.content_layout.addWidget(self.face_card)

        self.model_card = QFrame()
        self.model_card.setProperty("class", "card")
        model_layout = QVBoxLayout(self.model_card)
        model_layout.addWidget(QLabel("Model-backed assessment"))
        self.model_summary = QLabel("Gemini assessment will appear here.")
        self.model_summary.setWordWrap(True)
        self.model_strengths = QLabel("")
        self.model_strengths.setWordWrap(True)
        self.model_improvements = QLabel("")
        self.model_improvements.setWordWrap(True)
        self.model_tip = QLabel("")
        self.model_tip.setWordWrap(True)
        for widget in (self.model_summary, self.model_strengths, self.model_improvements, self.model_tip):
            widget.setProperty("class", "muted")
            model_layout.addWidget(widget)
        self.content_layout.addWidget(self.model_card)

        self.strategy_card = QFrame()
        self.strategy_card.setProperty("class", "card")
        strategy_layout = QVBoxLayout(self.strategy_card)
        strategy_layout.addWidget(QLabel("Analysis strategy"))
        self.strategy_summary = QLabel("Strategy details will appear here.")
        self.strategy_summary.setWordWrap(True)
        self.strategy_metrics = QLabel("")
        self.strategy_metrics.setWordWrap(True)
        self.strategy_trend = QLabel("")
        self.strategy_trend.setWordWrap(True)
        for widget in (self.strategy_summary, self.strategy_metrics, self.strategy_trend):
            widget.setProperty("class", "muted")
            strategy_layout.addWidget(widget)
        self.content_layout.addWidget(self.strategy_card)

        self.tabs = QTabWidget()
        self.content_layout.addWidget(self.tabs)
        self._build_tabs()

        self.highlight_card = QFrame()
        self.highlight_card.setProperty("class", "card")
        highlight_layout = QHBoxLayout(self.highlight_card)
        self.best_button = QPushButton("Your best moment")
        self.worst_button = QPushButton("Moment to improve")
        self.export_button = QPushButton("Export highlight reel")
        self.best_button.clicked.connect(lambda: self.play_clip(best=True))
        self.worst_button.clicked.connect(lambda: self.play_clip(best=False))
        self.export_button.clicked.connect(self.export_highlight_reel)
        highlight_layout.addWidget(self.best_button)
        highlight_layout.addWidget(self.worst_button)
        highlight_layout.addWidget(self.export_button)
        self.content_layout.addWidget(self.highlight_card)

        actions = QHBoxLayout()
        self.save_button = QPushButton("Save Session")
        self.share_button = QPushButton("Share Report")
        self.try_button = QPushButton("Try Again")
        self.home_button = QPushButton("Back to Home")
        self.share_button.setObjectName("SecondaryButton")
        self.try_button.setObjectName("SecondaryButton")
        self.home_button.setObjectName("SecondaryButton")
        self.save_button.clicked.connect(self.save_session)
        self.share_button.clicked.connect(self.share_report)
        self.try_button.clicked.connect(lambda: self._navigate("record"))
        self.home_button.clicked.connect(lambda: self._navigate("home"))
        actions.addWidget(self.save_button)
        actions.addWidget(self.share_button)
        actions.addWidget(self.try_button)
        actions.addWidget(self.home_button)
        actions.addStretch(1)
        self.content_layout.addLayout(actions)

    def _build_tabs(self) -> None:
        self.emotion_tab = QWidget()
        emotion_layout = QVBoxLayout(self.emotion_tab)
        self.emotion_canvas = self._create_canvas()
        emotion_layout.addWidget(self.emotion_canvas)
        self.emotion_insight = QLabel("Emotion insight will appear here.")
        self.emotion_insight.setWordWrap(True)
        emotion_layout.addWidget(self.emotion_insight)
        self.tabs.addTab(self.emotion_tab, "Emotions")

        self.gaze_tab = QWidget()
        gaze_layout = QVBoxLayout(self.gaze_tab)
        self.gaze_heatmap = GazeHeatmap()
        gaze_layout.addWidget(self.gaze_heatmap)
        self.gaze_stats = QLabel("Center 0%, Away 0%, Blinks 0")
        self.gaze_tip = QLabel("")
        self.gaze_tip.setWordWrap(True)
        gaze_layout.addWidget(self.gaze_stats)
        gaze_layout.addWidget(self.gaze_tip)
        self.tabs.addTab(self.gaze_tab, "Eye Gaze")

        self.speech_tab = QWidget()
        speech_layout = QVBoxLayout(self.speech_tab)
        self.transcript_box = QTextEdit()
        self.transcript_box.setReadOnly(True)
        speech_layout.addWidget(self.transcript_box)
        self.speech_stats = QLabel("WPM --")
        self.filler_breakdown = QLabel("")
        self.pause_box = QLabel("")
        self.speech_issues_box = QLabel("")
        self.speech_solutions_box = QLabel("")
        for widget in (self.speech_stats, self.filler_breakdown, self.pause_box, self.speech_issues_box, self.speech_solutions_box):
            widget.setWordWrap(True)
            speech_layout.addWidget(widget)
        self.tabs.addTab(self.speech_tab, "Speech")

        self.voice_tab = QWidget()
        voice_layout = QVBoxLayout(self.voice_tab)
        self.voice_canvas = self._create_canvas()
        voice_layout.addWidget(self.voice_canvas)
        self.voice_stats = QLabel("Pitch variation and energy levels appear here.")
        self.voice_warning = QLabel("")
        self.voice_warning.setWordWrap(True)
        voice_layout.addWidget(self.voice_stats)
        voice_layout.addWidget(self.voice_warning)
        self.tabs.addTab(self.voice_tab, "Voice Tone")

        self.posture_tab = QWidget()
        posture_layout = QVBoxLayout(self.posture_tab)
        self.posture_summary = QLabel("Posture and gesture insights.")
        self.posture_summary.setWordWrap(True)
        self.posture_breakdown = QLabel("")
        self.posture_breakdown.setWordWrap(True)
        posture_layout.addWidget(self.posture_summary)
        posture_layout.addWidget(self.posture_breakdown)
        self.tabs.addTab(self.posture_tab, "Posture & Gestures")

        # New: Charts & Analytics Tab
        self.charts_tab = QWidget()
        charts_layout = QVBoxLayout(self.charts_tab)
        self.charts_scroll = QScrollArea()
        self.charts_scroll.setWidgetResizable(True)
        self.charts_container = QWidget()
        self.charts_inner = QVBoxLayout(self.charts_container)
        self.charts_scroll.setWidget(self.charts_container)
        charts_layout.addWidget(self.charts_scroll)
        
        # Chart display labels
        self.chart_emotion = QLabel("Loading emotion distribution chart...")
        self.chart_gaze = QLabel("Loading gaze analysis chart...")
        self.chart_speech = QLabel("Loading speech metrics chart...")
        self.chart_trend = QLabel("Loading confidence trend...")
        self.chart_radar = QLabel("Loading performance radar...")
        self.chart_spectrogram = QLabel("Loading voice spectrogram...")
        
        for chart_label in [self.chart_emotion, self.chart_gaze, self.chart_speech, self.chart_trend, self.chart_radar, self.chart_spectrogram]:
            chart_label.setWordWrap(True)
            self.charts_inner.addWidget(chart_label)
        
        self.charts_inner.addStretch()
        self.tabs.addTab(self.charts_tab, "Charts")

        # New: Contextual Tips Tab
        self.tips_tab = QWidget()
        tips_layout = QVBoxLayout(self.tips_tab)
        self.tips_scroll = QScrollArea()
        self.tips_scroll.setWidgetResizable(True)
        self.tips_text = QTextEdit()
        self.tips_text.setReadOnly(True)
        self.tips_scroll.setWidget(self.tips_text)
        tips_layout.addWidget(QLabel("Personalized Tips & Recommendations"))
        tips_layout.addWidget(self.tips_scroll)
        
        # Export buttons
        tips_button_layout = QHBoxLayout()
        self.export_tips_button = QPushButton("Export Tips (.txt)")
        self.export_report_button = QPushButton("Export Full Report (.xlsx)")
        self.export_tips_button.clicked.connect(self.export_tips)
        self.export_report_button.clicked.connect(self.export_report)
        tips_button_layout.addWidget(self.export_tips_button)
        tips_button_layout.addWidget(self.export_report_button)
        tips_button_layout.addStretch()
        tips_layout.addLayout(tips_button_layout)
        
        self.tabs.addTab(self.tips_tab, "Tips & Advice")

    def _create_canvas(self):
        if FigureCanvas is None or Figure is None:
            label = QLabel("Chart rendering unavailable.")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return label
        figure = Figure(figsize=(4.5, 2.8), constrained_layout=True)
        canvas = FigureCanvas(figure)
        canvas.figure = figure  # type: ignore[attr-defined]
        return canvas

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user

    def load_session_data(self, session_data: dict[str, Any]) -> None:
        self.current_session = session_data
        self.load_result(session_data)

    def load_result(self, result: dict[str, Any]) -> None:
        self.current_result = result
        self.render_status.setText("Rendering analysis cards, charts, and coaching details...")
        model = result.get("model_analysis") or {}
        score = float(model.get("final_score") or result.get("confidence_score") or result.get("score") or 0.0)
        grade = model.get("grade") or result.get("grade") or self._grade_for(score)
        quality_score = float(result.get("analysis_quality_score") or result.get("analysis_breakdown", {}).get("quality_score") or 0.0)
        threshold = float(result.get("confidence_threshold") or 55.0)
        model_conf = model.get("confidence_label")
        if isinstance(model_conf, dict):
            confidence_state = model_conf
        elif isinstance(model_conf, str) and model_conf.strip():
            label = model_conf.strip().lower()
            message_map = {
                "uncertain": "Low confidence: this result should be treated as uncertain.",
                "moderate": "Moderate confidence: useful but still a bit noisy.",
                "confident": "High confidence: the detection is strong and stable.",
            }
            confidence_state = {"label": label, "message": message_map.get(label, "Confidence signal received from model output.")}
        else:
            confidence_state = result.get("confidence_label") or classify_confidence(score, quality_score, threshold)
        self.overall_score.setText(f"{score:.0f}")
        self.score_ring.animate_to(score)
        self.grade_badge.setText(f"Grade: {grade}")
        palette = {"A": COLOR_SUCCESS, "B": COLOR_ACCENT, "C": COLOR_WARNING, "D": COLOR_DANGER}
        self.grade_badge.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: white; padding: 10px 16px; border-radius: 14px; background: {palette.get(grade, COLOR_PRIMARY)};"
        )

        self._populate_summary_cards(result)
        self._populate_coach(result)
        self._populate_face_impression(result, confidence_state, quality_score)
        self._populate_model_assessment(result, model)
        self._populate_strategy(result)
        self._populate_tabs(result)
        self.render_status.setText("Analysis ready for review and public presentation.")

    def _grade_for(self, score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        return "D"

    def _populate_summary_cards(self, result: dict[str, Any]) -> None:
        model = result.get("model_analysis") or {}
        emotion = model.get("dominant_emotion") or result.get("dominant_emotion") or result.get("emotion_dominant") or "neutral"
        eye = float(result.get("eye_center_pct") or 0.0)
        posture = float(result.get("posture_score") or 0.0) * 100.0
        speech = float(result.get("wpm") or 0.0)
        gestures = float(result.get("gesture_positive_pct") or 0.0)
        self.mini_cards[0].set_value(str(emotion).title())
        self.mini_cards[1].set_value(f"{eye:.0f}%")
        self.mini_cards[2].set_value(f"{posture:.0f}%")
        self.mini_cards[3].set_value(f"{speech:.0f}")
        self.mini_cards[4].set_value(f"{gestures:.0f}%")
        confidence_label = result.get("confidence_label", {})
        if isinstance(confidence_label, dict) and confidence_label.get("label") == "uncertain":
            self.heading.setText("Analysis results - uncertain detection")
        else:
            self.heading.setText("Analysis results")

    def _populate_coach(self, result: dict[str, Any]) -> None:
        tips = result.get("llm_feedback") or []
        if isinstance(tips, str):
            try:
                tips = json.loads(tips)
            except Exception:
                tips = [tips]
        if tips:
            self.coach_message.setText("")
            self.coach_list.setText("\n\n".join(f"• {tip}" for tip in tips))
        else:
            self.coach_list.setText("")
            self.coach_message.setText("Add your API key in settings to enable AI coaching feedback.")

    def _populate_face_impression(self, result: dict[str, Any], confidence_state: dict[str, Any], quality_score: float) -> None:
        face = result.get("face_impression") or {}
        summary = face.get("summary") or "No face impression available."
        what_it_says = face.get("what_it_says") or ""
        example = face.get("real_life_example") or ""
        self.face_summary.setText(summary)
        self.face_confidence.setText(f"Confidence: {float(face.get('confidence') or 0.0):.2f} | Quality: {quality_score:.0f}/100 | {confidence_state.get('message', '')}")
        self.face_example.setText(f"Real-life example: {what_it_says} {example}".strip())

    def _populate_model_assessment(self, result: dict[str, Any], model: dict[str, Any]) -> None:
        if not model:
            self.model_summary.setText("No Gemini model assessment was available for this session.")
            self.model_strengths.setText("")
            self.model_improvements.setText("")
            self.model_tip.setText("")
            return
        summary = model.get("overall_summary") or ""
        strengths = model.get("strengths") or []
        improvements = model.get("improvements") or []
        tip = model.get("public_ready_tip") or ""
        evidence = model.get("evidence_used") or []
        uncertainty = model.get("uncertainty_reason") or ""
        self.model_summary.setText(summary)
        self.model_strengths.setText("Strengths: " + " | ".join(str(item) for item in strengths[:3]))
        self.model_improvements.setText("Improvement areas: " + " | ".join(str(item) for item in improvements[:3]))
        parts = []
        if tip:
            parts.append(f"Tip: {tip}")
        if evidence:
            parts.append("Evidence: " + " | ".join(str(item) for item in evidence[:4]))
        if uncertainty:
            parts.append(f"Uncertainty: {uncertainty}")
        self.model_tip.setText("\n\n".join(parts))

    def _populate_strategy(self, result: dict[str, Any]) -> None:
        profile = result.get("analysis_profile") or {}
        if not profile:
            self.strategy_summary.setText("No analysis strategy profile was available.")
            self.strategy_metrics.setText("")
            self.strategy_trend.setText("")
            return

        summary = profile.get("summary") or ""
        mode = profile.get("analysis_mode") or "unknown"
        reliability = float(profile.get("signal_quality") or 0.0)
        stability = float(profile.get("frame_stability") or 0.0)
        speech_fit = float(profile.get("speech_fit") or 0.0)
        vision_fit = float(profile.get("vision_fit") or 0.0)
        vocal_fit = float(profile.get("vocal_fit") or 0.0)
        self.strategy_summary.setText(summary)
        self.strategy_metrics.setText(
            f"Mode: {mode} | Reliability: {reliability:.0f}/100 | Stability: {stability:.0f}/100 | Speech fit: {speech_fit:.0f} | Vision fit: {vision_fit:.0f} | Voice fit: {vocal_fit:.0f}"
        )
        trend = profile.get("trend") or {}
        self.strategy_trend.setText(
            f"Trend across session: start {trend.get('start', '--')} | middle {trend.get('middle', '--')} | end {trend.get('end', '--')}"
        )

    def _populate_tabs(self, result: dict[str, Any]) -> None:
        self._update_emotion_tab(result)
        self._update_gaze_tab(result)
        self._update_speech_tab(result)
        self._update_voice_tab(result)
        self._update_posture_tab(result)
        self._update_charts_tab(result)
        self._update_tips_tab(result)

    def _update_emotion_tab(self, result: dict[str, Any]) -> None:
        if FigureCanvas is None or Figure is None:
            self.emotion_canvas.setText("Emotion charts unavailable.")
        else:
            figure = self.emotion_canvas.figure  # type: ignore[attr-defined]
            figure.clear()
            axis = figure.add_subplot(111)
            values = [float(result.get(key) or 0.0) for key in ("emotion_happy", "emotion_neutral", "emotion_sad", "emotion_anxious", "emotion_surprised")]
            labels = ["Happy", "Neutral", "Sad", "Anxious", "Surprised"]
            plot_values = values if any(values) else [1, 0, 0, 0, 0]
            wedges, _, _ = axis.pie(
                plot_values,
                labels=None,
                autopct="%1.0f%%",
                colors=["#00D4AA", "#6C63FF", "#FF6B6B", "#F7B731", "#7B73FF"],
                textprops={"fontsize": 8},
            )
            axis.legend(wedges, labels, loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=8)
            axis.set_title("Emotion distribution")
            self.emotion_canvas.draw()
        model = result.get("model_analysis") or {}
        dominant = model.get("dominant_emotion") or result.get("dominant_emotion") or result.get("emotion_dominant") or "neutral"
        self.emotion_insight.setText(f"Dominant emotion: {str(dominant).title()}. Keep reinforcing the moments where your expression stayed open and calm.")

    def _update_gaze_tab(self, result: dict[str, Any]) -> None:
        heat_points = result.get("gaze_points") or []
        if heat_points:
            self.gaze_heatmap.set_points([(float(x), float(y)) for x, y in heat_points])
        else:
            self.gaze_heatmap.set_points([(0.5, 0.5), (0.45, 0.4), (0.55, 0.45)])
        center = float(result.get("eye_center_pct") or 0.0)
        away = float(result.get("eye_away_pct") or max(0.0, 100.0 - center))
        blinks = int(result.get("blink_count") or 0)
        self.gaze_stats.setText(f"Center {center:.0f}%, Away {away:.0f}%, Blinks {blinks}")
        tip = "Keep looking back to the camera between points so your audience feels included."
        if center >= 70:
            tip = "Your eye contact is strong. Keep using short glances away only when you need to think."
        self.gaze_tip.setText(tip)

    def _update_speech_tab(self, result: dict[str, Any]) -> None:
        transcript = (result.get("transcript") or "").strip()
        self.transcript_box.setPlainText(transcript)
        wpm = float(result.get("wpm") or 0.0)
        word_count = int(result.get("word_count") or 0)
        mic_level = float(result.get("mic_level") or 0.0)
        fillers = result.get("filler_words") or {}
        pauses = result.get("long_pauses") or []
        speech_issues = result.get("speech_issues") or []
        speech_solutions = result.get("speech_solutions") or []
        if not transcript:
            self.speech_stats.setText(f"No speech detected. Mic level {mic_level:.4f}. Check microphone input and recording permissions.")
        else:
            self.speech_stats.setText(f"WPM {wpm:.0f} | Words {word_count} | Mic level {mic_level:.4f} | Ideal range 110-150")
        if isinstance(fillers, dict) and fillers:
            breakdown = ", ".join(f"{word}: {count}" for word, count in fillers.items())
        else:
            breakdown = "No major filler words detected."
        self.filler_breakdown.setText(breakdown)
        if pauses:
            pause_text = "Long pauses: " + ", ".join(f"{item['at']:.1f}s ({item['duration']:.1f}s)" for item in pauses)
        else:
            pause_text = "No long pauses detected."
        self.pause_box.setText(pause_text)

        if speech_issues:
            self.speech_issues_box.setText("Issues: " + " | ".join(str(item) for item in speech_issues))
        elif not transcript:
            self.speech_issues_box.setText("Issues: Speech content could not be extracted from this recording.")
        else:
            self.speech_issues_box.setText("Issues: No major speech issues detected.")

        if speech_solutions:
            self.speech_solutions_box.setText("Solutions: " + " | ".join(str(item) for item in speech_solutions))
        elif not transcript:
            self.speech_solutions_box.setText("Solutions: Increase mic input level, move closer to mic, and ensure Windows microphone access is enabled for this app.")
        else:
            self.speech_solutions_box.setText("Solutions: Keep your pace between 110-150 WPM and continue reducing filler words.")

    def _update_voice_tab(self, result: dict[str, Any]) -> None:
        if FigureCanvas is None or Figure is None:
            self.voice_canvas.setText("Voice charts unavailable.")
        else:
            figure = self.voice_canvas.figure  # type: ignore[attr-defined]
            figure.clear()
            axis = figure.add_subplot(111)
            pitch_variation = float(result.get("pitch_variation") or 0.0)
            energy_mean = float(result.get("voice_energy") or result.get("energy_mean") or 0.0)
            axis.bar(["Pitch", "Energy"], [pitch_variation, energy_mean * 100.0], color=["#6C63FF", "#00D4AA"])
            axis.set_title("Tone analysis")
            self.voice_canvas.draw()
        pitch_variation = float(result.get("pitch_variation") or 0.0)
        energy_mean = float(result.get("voice_energy") or result.get("energy_mean") or 0.0)
        voice_emotion = str(result.get("voice_emotion") or "neutral").title()
        voice_emotion_conf = float(result.get("voice_emotion_confidence") or 0.0)
        self.voice_stats.setText(
            f"Pitch variation {pitch_variation:.1f} Hz | Energy {energy_mean:.3f} | Voice emotion {voice_emotion} ({voice_emotion_conf:.2f})"
        )
        if result.get("is_monotone"):
            self.voice_warning.setText("Issue: Monotone delivery. Solution: emphasize key words and vary your pitch at sentence endings.")
        elif result.get("is_too_quiet"):
            self.voice_warning.setText("Issue: Voice is too quiet. Solution: increase microphone gain and keep mouth 15-20 cm from mic.")
        elif result.get("is_too_loud"):
            self.voice_warning.setText("Issue: Voice is too loud. Solution: step slightly away from mic and reduce input volume by 10-15%.")
        elif energy_mean < 0.01 and voice_emotion_conf < 0.1:
            self.voice_warning.setText("Issue: Voice signal is weak for emotion detection. Solution: record in a quieter room and speak with steady volume.")
        else:
            self.voice_warning.setText("No major voice issues detected. Maintain this tone consistency.")

    def _update_posture_tab(self, result: dict[str, Any]) -> None:
        posture = float(result.get("posture_score") or 0.0) * 100.0
        slouch = float(result.get("slouch_pct") or 0.0)
        gesture_positive = float(result.get("gesture_positive_pct") or 0.0)
        gesture_nervous = float(result.get("gesture_nervous_pct") or 0.0)
        self.posture_summary.setText(f"Posture score {posture:.0f}% | Slouch {slouch:.0f}%")
        self.posture_breakdown.setText(f"Positive gestures {gesture_positive:.0f}% | Nervous gestures {gesture_nervous:.0f}%")

    def _update_charts_tab(self, result: dict[str, Any]) -> None:
        """Display generated visualization charts in the Charts tab."""
        # Clear previous charts
        while self.charts_inner.count() > 0:
            widget = self.charts_inner.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # Add title
        title = QLabel("Performance Analytics & Visualizations")
        title.setStyleSheet("font-weight: bold; font-size: 12pt; margin-bottom: 10px;")
        self.charts_inner.addWidget(title)
        
        # Try to display chart images
        chart_files = {
            "Emotion Distribution": result.get("visualization_emotion"),
            "Eye Gaze Analysis": result.get("visualization_gaze"),
            "Speech Metrics": result.get("visualization_speech"),
            "Confidence Trend": result.get("visualization_trend"),
            "Performance Radar": result.get("visualization_radar"),
            "Voice Spectrogram": result.get("visualization_spectrogram"),
            "Voice Chromagram": result.get("visualization_chromagram"),
        }
        
        chart_count = 0
        for chart_name, chart_path in chart_files.items():
            chart_frame = QFrame()
            chart_frame.setProperty("class", "card")
            chart_layout = QVBoxLayout(chart_frame)

            chart_title = QLabel(chart_name)
            chart_title.setStyleSheet("font-weight: bold; margin-top: 6px;")
            chart_layout.addWidget(chart_title)

            if chart_path and Path(chart_path).exists():
                try:
                    from PySide6.QtGui import QPixmap

                    pixmap = QPixmap(chart_path)
                    if not pixmap.isNull():
                        image_label = QLabel()
                        image_label.setPixmap(pixmap.scaledToWidth(620, Qt.SmoothTransformation))
                        image_label.setAlignment(Qt.AlignCenter)
                        status = QLabel("Generated")
                        status.setProperty("class", "status_ok")
                        chart_layout.addWidget(status)
                        chart_layout.addWidget(image_label)
                        chart_count += 1
                    else:
                        status = QLabel("Image exists but failed to render.")
                        status.setProperty("class", "status_warn")
                        chart_layout.addWidget(status)
                except Exception:
                    status = QLabel("Rendering error while loading this chart.")
                    status.setProperty("class", "status_warn")
                    chart_layout.addWidget(status)
            else:
                status = QLabel("Pending: this chart was not generated for this session yet.")
                status.setProperty("class", "loading")
                chart_layout.addWidget(status)

            self.charts_inner.addWidget(chart_frame)
        
        if chart_count == 0:
            no_charts = QLabel("No visualizations were generated for this session. Record a new session to populate analytics.")
            no_charts.setWordWrap(True)
            self.charts_inner.addWidget(no_charts)
        
        self.charts_inner.addStretch()

    def _update_tips_tab(self, result: dict[str, Any]) -> None:
        """Display contextual tips and recommendations."""
        tips_text = result.get("tips_text", "")
        if not tips_text:
            tips_path = result.get("tips_path")
            if tips_path and Path(tips_path).exists():
                try:
                    tips_text = Path(tips_path).read_text(encoding="utf-8")
                except Exception:
                    tips_text = ""
        
        if tips_text:
            # Format tips with markdown-like styling
            self.tips_text.setPlainText(tips_text)
        else:
            self.tips_text.setPlainText(
                "Tips not available for this session.\n\n"
                "Run a new recording to generate personalized coaching, charts, and exportable report content."
            )

    def export_tips(self) -> None:
        """Export contextual tips to a text file."""
        if not self.current_result:
            QMessageBox.warning(self, "Export Tips", "No session data available.")
            return
        
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Tips", "", "Text Files (*.txt);;All Files (*)"
            )
            if not file_path:
                return
            
            tips_text = self.current_result.get("tips_text", "No tips available.")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(tips_text)
            
            QMessageBox.information(self, "Success", f"Tips exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export tips:\n{str(e)}")

    def export_report(self) -> None:
        """Export the full Excel report."""
        if not self.current_result:
            QMessageBox.warning(self, "Export Report", "No session data available.")
            return
        
        report_path = self.current_result.get("report_path")
        if not report_path or not Path(report_path).exists():
            QMessageBox.warning(self, "Export Report", "No Excel report was generated for this session.")
            return
        
        try:
            save_path, _ = QFileDialog.getSaveFileName(
                self, "Save Report", "analysis_report.xlsx", "Excel Files (*.xlsx);;All Files (*)"
            )
            if not save_path:
                return
            
            import shutil
            shutil.copy(report_path, save_path)
            QMessageBox.information(self, "Success", f"Report exported to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report:\n{str(e)}")

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def play_clip(self, best: bool = True) -> None:
        if not self.current_result:
            return
        video_path = self.current_result.get("video_path")
        if not video_path:
            return
        path = Path(video_path)
        if not path.exists():
            return
        highlight_path = path.with_name("highlight_reel.mp4")
        frame_scores = self.current_result.get("frame_scores") or []
        if frame_scores:
            try:
                self.create_highlight_reel(path, frame_scores, highlight_path, best=best)
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(highlight_path)))
                return
            except Exception:
                pass
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path)))

    def export_highlight_reel(self) -> None:
        if not self.current_result:
            return
        video_path = self.current_result.get("video_path")
        if not video_path:
            return
        source = Path(video_path)
        if not source.exists():
            return
        target, _ = QFileDialog.getSaveFileName(self, "Export highlight reel", str(source.with_name("highlight_reel.mp4")), "MP4 Video (*.mp4)")
        if not target:
            return
        try:
            self.create_highlight_reel(source, self.current_result.get("frame_scores") or [], Path(target), best=True)
            QMessageBox.information(self, "Export complete", f"Highlight reel saved to {target}")
        except Exception as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def create_highlight_reel(self, video_path: Path, frame_scores: list[tuple[float, float]], output_path: Path, best: bool = True) -> None:
        if VideoFileClip is None or concatenate_videoclips is None:
            raise RuntimeError("moviepy is unavailable.")
        sorted_scores = sorted(frame_scores, key=lambda item: item[1], reverse=best)
        chosen = [timestamp for timestamp, _ in sorted_scores[:3]]
        clip = VideoFileClip(str(video_path))
        subclips = []
        for timestamp in chosen:
            start = max(0.0, timestamp - 1.0)
            end = min(clip.duration, timestamp + 2.0)
            subclips.append(clip.subclip(start, end))
        if not subclips:
            raise RuntimeError("No highlight segments available.")
        final = concatenate_videoclips(subclips)
        final.write_videofile(str(output_path), codec="libx264")

    def save_session(self) -> None:
        if not self.current_result:
            return
        if self.current_session and self.current_session.get("session_id"):
            QMessageBox.information(self, "Saved", "This session is already stored.")
            return
        QMessageBox.information(self, "Saved", "Session details are stored automatically after analysis.")

    def share_report(self) -> None:
        if not self.current_result:
            return
        video_path = self.current_result.get("video_path")
        if video_path:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(video_path).parent)))

    def load_session_from_db(self, session_id: int) -> None:
        if self.main_window is None:
            return
        session = get_session_by_id(self.main_window.db_path, session_id)
        if session:
            self.load_result(session)
