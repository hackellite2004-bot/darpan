from __future__ import annotations

from PySide6.QtCore import Property, QEasingCurve, QPropertyAnimation, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config import COLOR_ACCENT, COLOR_BORDER, COLOR_PRIMARY, COLOR_TEXT


class ConfidenceRing(QWidget):
    valueChanged = Signal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0.0
        self._target = 0.0
        self.setMinimumSize(240, 240)
        self._animation = QPropertyAnimation(self, b"ringValue", self)
        self._animation.setDuration(1200)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

    def sizeHint(self):
        return self.minimumSize()

    def getValue(self) -> float:
        return self._value

    def setValue(self, value: float) -> None:
        self._value = max(0.0, min(100.0, float(value)))
        self.valueChanged.emit(self._value)
        self.update()

    ringValue = Property(float, getValue, setValue, notify=valueChanged)

    def animate_to(self, value: float) -> None:
        self._target = max(0.0, min(100.0, float(value)))
        self._animation.stop()
        self._animation.setStartValue(self._value)
        self._animation.setEndValue(self._target)
        self._animation.start()

    def paintEvent(self, event):  # noqa: N802
        side = min(self.width(), self.height()) - 8
        radius = side / 2.0
        center_x = self.width() / 2.0
        center_y = self.height() / 2.0
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("transparent"))
        painter.drawRect(self.rect())

        ring_rect = self.rect().adjusted(12, 12, -12, -12)
        base_pen = QPen(QColor(COLOR_BORDER), 16)
        base_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(base_pen)
        painter.drawArc(ring_rect, 0, 360 * 16)

        progress_pen = QPen(QColor(COLOR_ACCENT), 16)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        span_angle = int(-360 * 16 * (self._value / 100.0))
        painter.drawArc(ring_rect, 90 * 16, span_angle)

        painter.setPen(QColor(COLOR_TEXT))
        font = painter.font()
        font.setPointSize(22)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, f"{self._value:.0f}")

        font.setPointSize(10)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor(COLOR_PRIMARY))
        label_rect = self.rect().adjusted(0, 60, 0, 0)
        painter.drawText(label_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Confidence")
