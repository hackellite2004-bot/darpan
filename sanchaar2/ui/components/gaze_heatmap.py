from __future__ import annotations

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget

from config import COLOR_ACCENT, COLOR_BORDER, COLOR_PRIMARY


class GazeHeatmap(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(260, 220)
        self._points: list[QPointF] = []

    def add_point(self, x: float, y: float) -> None:
        self._points.append(QPointF(x, y))
        if len(self._points) > 500:
            self._points = self._points[-500:]
        self.update()

    def set_points(self, points: list[tuple[float, float]]) -> None:
        self._points = [QPointF(x, y) for x, y in points]
        self.update()

    def paintEvent(self, event):  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))
        painter.setPen(QPen(QColor(COLOR_BORDER), 1))
        painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 14, 14)

        width = self.width()
        height = self.height()
        grid_color = QColor(COLOR_BORDER)
        grid_color.setAlpha(120)
        painter.setPen(QPen(grid_color, 1))
        for index in range(1, 5):
            x = int(width * index / 5)
            y = int(height * index / 5)
            painter.drawLine(x, 12, x, height - 12)
            painter.drawLine(12, y, width - 12, y)

        if not self._points:
            return

        painter.setPen(Qt.PenStyle.NoPen)
        for point in self._points:
            px = int((point.x() % 1.0) * width)
            py = int((point.y() % 1.0) * height)
            radius = 8
            painter.setBrush(QColor(COLOR_PRIMARY))
            painter.setOpacity(0.25)
            painter.drawEllipse(px - radius, py - radius, radius * 2, radius * 2)
            painter.setBrush(QColor(COLOR_ACCENT))
            painter.setOpacity(0.45)
            painter.drawEllipse(px - radius // 2, py - radius // 2, radius, radius)
