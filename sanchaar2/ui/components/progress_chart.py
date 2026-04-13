from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

try:
    import pyqtgraph as pg
except Exception:  # pragma: no cover
    pg = None


class ProgressChart(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(220)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        if pg is not None:
            self.plot = pg.PlotWidget(background="transparent")
            self.plot.showGrid(x=True, y=True, alpha=0.25)
            self.plot.setMenuEnabled(False)
            self.plot.setMouseEnabled(x=False, y=False)
            self.plot.setAntialiasing(True)
            self.plot.setLabel("left", "Score")
            self.plot.setLabel("bottom", "Session")
            self.curve = self.plot.plot(pen=pg.mkPen(color="#00D4AA", width=3), symbol="o", symbolBrush="#6C63FF")
            layout.addWidget(self.plot)
        else:
            self.plot = None
            self.placeholder = QLabel("Progress chart will appear here.")
            self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self.placeholder)

    def set_data(self, labels: list[str], scores: list[float]) -> None:
        if self.plot is not None:
            xs = list(range(len(scores)))
            self.curve.setData(xs, scores)
            self.plot.getAxis("bottom").setTicks([list(zip(xs, labels))])
        elif hasattr(self, "placeholder"):
            self.placeholder.setText("\n".join(f"{label}: {score:.0f}" for label, score in zip(labels, scores)))
