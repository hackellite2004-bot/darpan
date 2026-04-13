from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout

from config import COLOR_ACCENT, COLOR_DANGER, COLOR_PRIMARY, COLOR_SUCCESS, COLOR_WARNING


class LiveOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.emotion_label = QLabel("Emotion: --")
        self.gaze_label = QLabel("Gaze: --")
        self.posture_label = QLabel("Posture: --")
        self.timer_label = QLabel("00:00")
        self.wpm_label = QLabel("WPM: --")
        self.waveform = QProgressBar()
        self.waveform.setRange(0, 100)
        self.waveform.setValue(10)
        self.waveform.setTextVisible(False)
        self.waveform.setFixedHeight(12)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)
        layout.addWidget(self.emotion_label)
        layout.addWidget(self.gaze_label)
        layout.addWidget(self.posture_label)
        layout.addWidget(self.wpm_label)
        layout.addWidget(self.timer_label)
        layout.addWidget(self.waveform)
        layout.addStretch(1)
        self.set_state("neutral", "center", "good", "00:00", 0.0, 0.0)

    def set_state(self, emotion: str, gaze: str, posture: str, timer_text: str, wpm: float, waveform_level: float) -> None:
        self.emotion_label.setText(f"Emotion: {emotion.title()}")
        self.gaze_label.setText(f"Gaze: {gaze.title()}")
        self.posture_label.setText(f"Posture: {posture.title()}")
        self.timer_label.setText(timer_text)
        self.wpm_label.setText(f"WPM: {wpm:.0f}" if wpm else "WPM: --")
        self.waveform.setValue(max(0, min(100, int(waveform_level))))

        for label, color in ((self.emotion_label, COLOR_PRIMARY), (self.gaze_label, COLOR_ACCENT), (self.posture_label, COLOR_SUCCESS)):
            label.setStyleSheet(f"font-weight: 600; color: {color};")

        if posture.lower() == "warning":
            self.posture_label.setStyleSheet(f"font-weight: 600; color: {COLOR_WARNING};")
        elif posture.lower() == "bad":
            self.posture_label.setStyleSheet(f"font-weight: 600; color: {COLOR_DANGER};")
