from __future__ import annotations

from datetime import datetime
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from config import DB_PATH
from core.database import get_sessions_for_user
from ui.components.metric_card import MetricCard
from ui.components.progress_chart import ProgressChart


class HistoryPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_user: dict[str, Any] | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        self.heading = QLabel("Session history")
        self.heading.setObjectName("PageHeading")
        outer.addWidget(self.heading)

        self.summary_row = QHBoxLayout()
        self.improvement_card = MetricCard("Improvement", "--")
        self.streak_card = MetricCard("Streak", "--")
        self.average_card = MetricCard("Average", "--")
        for card in (self.improvement_card, self.streak_card, self.average_card):
            self.summary_row.addWidget(card)
        outer.addLayout(self.summary_row)

        chart_card = QFrame()
        chart_card.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.addWidget(QLabel("Confidence score over time"))
        self.progress_chart = ProgressChart()
        chart_layout.addWidget(self.progress_chart)
        outer.addWidget(chart_card)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Date", "Duration", "Score", "Grade", "Highlight"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellDoubleClicked.connect(self.open_row)
        outer.addWidget(self.table, 1)

        self.footer = QLabel("You can click any row to open the full analysis for that session.")
        self.footer.setProperty("class", "muted")
        outer.addWidget(self.footer)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        self.refresh_data()

    def refresh_data(self) -> None:
        if not self.current_user:
            self.heading.setText("Session history")
            self.table.setRowCount(0)
            self.progress_chart.set_data([], [])
            self.improvement_card.set_value("--")
            self.streak_card.set_value("--")
            self.average_card.set_value("--")
            return

        sessions = get_sessions_for_user(DB_PATH, self.current_user["id"])
        labels = []
        scores = []
        self.table.setRowCount(0)
        for row_index, session in enumerate(sessions):
            timestamp = str(session.get("timestamp") or "")
            try:
                display_date = datetime.fromisoformat(timestamp.replace(" ", "T")).strftime("%d %b %Y")
            except Exception:
                display_date = timestamp[:10]
            score = float(session.get("confidence_score") or 0.0)
            grade = session.get("grade") or self._grade_for(score)
            duration = float(session.get("duration_seconds") or 0.0)
            highlight = "Yes" if session.get("highlight_reel_path") else "No"
            labels.append(display_date)
            scores.append(score)
            self.table.insertRow(row_index)
            for col, value in enumerate((display_date, f"{duration/60:.1f} min", f"{score:.0f}", grade, highlight)):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, col, item)
            self.table.setRowHeight(row_index, 34)

        self.progress_chart.set_data(labels[-5:], scores[-5:])
        if scores:
            improvement = scores[-1] - scores[0]
            self.improvement_card.set_value(f"{improvement:+.0f}")
            self.average_card.set_value(f"{sum(scores)/len(scores):.0f}")
        else:
            self.improvement_card.set_value("--")
            self.average_card.set_value("--")
        self.streak_card.set_value(f"{self._calculate_streak(sessions)} sessions")

    def _calculate_streak(self, sessions: list[dict[str, Any]]) -> int:
        if not sessions:
            return 0
        count = 0
        today = datetime.now().date()
        for session in reversed(sessions):
            timestamp = str(session.get("timestamp") or "")
            try:
                session_date = datetime.fromisoformat(timestamp.replace(" ", "T")).date()
            except Exception:
                continue
            if (today - session_date).days <= 30:
                count += 1
        return count

    def _grade_for(self, score: float) -> str:
        if score >= 85:
            return "A"
        if score >= 70:
            return "B"
        if score >= 55:
            return "C"
        return "D"

    def open_row(self, row: int, column: int) -> None:
        if not self.main_window or not self.current_user:
            return
        sessions = get_sessions_for_user(DB_PATH, self.current_user["id"])
        if 0 <= row < len(sessions):
            self.main_window.open_results_for_session(sessions[row])
