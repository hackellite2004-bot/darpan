from __future__ import annotations

import importlib.util
from pathlib import Path

from PySide6.QtCore import QTimer, Signal, Qt
from PySide6.QtGui import QLinearGradient, QColor, QPainter, QBrush
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from config import DEPENDENCY_PACKAGE_MAP, REQUIRED_DEPENDENCIES, COLOR_ACCENT, COLOR_PRIMARY, COLOR_TEXT


class SplashPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self._checked = False
        self._dependencies_ok = False
        self._progress_value = 0

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.canvas = QFrame()
        self.canvas.setObjectName("SplashCanvas")
        canvas_layout = QVBoxLayout(self.canvas)
        canvas_layout.setContentsMargins(40, 40, 40, 40)
        canvas_layout.setSpacing(24)
        canvas_layout.addStretch(1)

        self.title = QLabel("Darpan")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title.setStyleSheet(
            "font-size: 54px; font-weight: 800; color: white;"
        )
        self.title.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.tagline = QLabel("Know how you speak. Grow how you connect.")
        self.tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.tagline.setStyleSheet(f"font-size: 18px; color: {COLOR_TEXT};")

        self.status = QLabel("Checking dependencies...")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet(f"color: {COLOR_TEXT}; font-size: 14px;")
        self.status.setWordWrap(True)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        self.progress.setFixedHeight(16)

        self.retry_button = QPushButton("Retry")
        self.retry_button.setVisible(False)
        self.retry_button.clicked.connect(self.check_dependencies)

        self.details = QLabel("")
        self.details.setWordWrap(True)
        self.details.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.details.setStyleSheet(f"color: {COLOR_TEXT};")

        center_card = QFrame()
        center_card.setProperty("class", "card")
        center_layout = QVBoxLayout(center_card)
        center_layout.setContentsMargins(28, 28, 28, 28)
        center_layout.setSpacing(16)
        center_layout.addWidget(self.title)
        center_layout.addWidget(self.tagline)
        center_layout.addWidget(self.status)
        center_layout.addWidget(self.progress)
        center_layout.addWidget(self.details)
        center_layout.addWidget(self.retry_button, alignment=Qt.AlignmentFlag.AlignCenter)
        center_layout.addStretch(1)

        canvas_layout.addWidget(center_card, 0, Qt.AlignmentFlag.AlignCenter)
        canvas_layout.addStretch(1)
        outer.addWidget(self.canvas)

        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._tick_progress)
        self._nav_timer = QTimer(self)
        self._nav_timer.setSingleShot(True)
        self._nav_timer.timeout.connect(lambda: self.navigate_requested.emit("login"))

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        if not self._checked:
            self._checked = True
            self.check_dependencies()
        self._pulse_timer.start(40)

    def hideEvent(self, event):  # noqa: N802
        super().hideEvent(event)
        self._pulse_timer.stop()
        self._nav_timer.stop()

    def _tick_progress(self) -> None:
        if self._dependencies_ok:
            value = min(100, self.progress.value() + 3)
            self.progress.setValue(value)
        else:
            value = (self.progress.value() + 1) % 100
            self.progress.setValue(value)

    def _module_available(self, module_name: str) -> bool:
        return importlib.util.find_spec(module_name) is not None

    def check_dependencies(self) -> None:
        missing = [name for name in REQUIRED_DEPENDENCIES if not self._module_available(name)]
        if missing:
            self._dependencies_ok = False
            pip_names = [DEPENDENCY_PACKAGE_MAP.get(name, name) for name in missing]
            self.status.setText("Missing required packages found.")
            self.details.setText("Install these dependencies:\n" + "\n".join(pip_names))
            self.retry_button.setVisible(True)
            self.progress.setValue(0)
            return

        self._dependencies_ok = True
        self.status.setText("All required packages are available.")
        self.details.setText("Starting Darpan...")
        self.retry_button.setVisible(False)
        self.progress.setValue(35)
        self._nav_timer.start(2000)

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gradient = QLinearGradient(0, 0, self.width(), self.height())
        gradient.setColorAt(0.0, QColor("#0F0F1A"))
        gradient.setColorAt(0.5, QColor("#17172A"))
        gradient.setColorAt(1.0, QColor("#11111D"))
        painter.fillRect(self.rect(), QBrush(gradient))
        painter.end()
