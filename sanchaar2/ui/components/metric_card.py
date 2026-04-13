from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "--", subtitle: str = "", accent: str = "#6C63FF", parent=None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self.setObjectName("MetricCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self._accent = accent

        self.title_label = QLabel(title)
        self.title_label.setProperty("class", "heading")
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setStyleSheet(f"font-size: 28px; font-weight: 700; color: {accent};")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setProperty("class", "muted")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addWidget(self.subtitle_label)
        layout.addStretch(1)

    def set_value(self, value: str, subtitle: str | None = None) -> None:
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)
