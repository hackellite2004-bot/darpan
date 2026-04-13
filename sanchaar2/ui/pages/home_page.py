from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from config import DB_PATH, COLOR_ACCENT, COLOR_PRIMARY
from core.database import get_last_session_for_user, get_sessions_for_user
from ui.components.confidence_ring import ConfidenceRing
from ui.components.metric_card import MetricCard
from ui.components.progress_chart import ProgressChart


class HomePage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_user: dict[str, Any] | None = None
        self.last_session: dict[str, Any] | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        self.greeting = QLabel("Good morning")
        self.greeting.setObjectName("PageHeading")
        self.subheading = QLabel("Your latest communication insights are below.")
        self.subheading.setProperty("class", "muted")
        outer.addWidget(self.greeting)
        outer.addWidget(self.subheading)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(12)
        self.metric_cards = [
            MetricCard("Confidence Score", "--"),
            MetricCard("Eye Contact", "--"),
            MetricCard("Speech Rate", "--"),
            MetricCard("Posture", "--"),
        ]
        for card in self.metric_cards:
            metrics_row.addWidget(card)
        outer.addLayout(metrics_row)

        center_row = QHBoxLayout()
        center_row.setSpacing(16)
        self.confidence_ring = ConfidenceRing()
        center_row.addWidget(self.confidence_ring, 0)

        right_card = QFrame()
        right_card.setProperty("class", "card")
        right_layout = QVBoxLayout(right_card)
        self.progress_chart = ProgressChart()
        right_layout.addWidget(QLabel("Your progress"))
        right_layout.addWidget(self.progress_chart)
        center_row.addWidget(right_card, 1)
        outer.addLayout(center_row, 1)

        self.onboarding_card = QFrame()
        self.onboarding_card.setProperty("class", "card")
        onboarding_layout = QVBoxLayout(self.onboarding_card)
        self.onboarding_label = QLabel("Start your first recording to see personalized feedback.")
        self.onboarding_label.setWordWrap(True)
        self.onboarding_label.setProperty("class", "muted")
        onboarding_layout.addWidget(self.onboarding_label)
        outer.addWidget(self.onboarding_card)

        cta_row = QHBoxLayout()
        self.record_button = QPushButton("Start New Session")
        self.interview_button = QPushButton("Practice Interview")
        self.record_button.clicked.connect(lambda: self._navigate("record"))
        self.interview_button.clicked.connect(lambda: self._navigate("interview"))
        cta_row.addWidget(self.record_button)
        cta_row.addWidget(self.interview_button)
        cta_row.addStretch(1)
        outer.addLayout(cta_row)

        self.refresh_data()

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        if user:
            self.greeting.setText(f"Good morning, {user.get('name', 'there')}")
        else:
            self.greeting.setText("Good morning")
        self.refresh_data()

    def refresh_data(self) -> None:
        if not self.current_user:
            self.onboarding_card.setVisible(True)
            self.onboarding_label.setText("Sign in to see your latest session stats and progress chart.")
            for card in self.metric_cards:
                card.set_value("--")
            self.confidence_ring.animate_to(0)
            self.progress_chart.set_data([], [])
            return

        sessions = get_sessions_for_user(DB_PATH, self.current_user["id"], limit=5)
        last_session = get_last_session_for_user(DB_PATH, self.current_user["id"])
        self.last_session = last_session
        if not sessions:
            self.onboarding_card.setVisible(True)
            self.onboarding_label.setText("No sessions yet. Start a recording to unlock your dashboard.")
            self.progress_chart.set_data([], [])
            self.confidence_ring.animate_to(0)
            for card in self.metric_cards:
                card.set_value("--")
            return

        self.onboarding_card.setVisible(False)
        latest = sessions[-1]
        score = float(latest.get("confidence_score") or 0.0)
        eye = float(latest.get("eye_center_pct") or 0.0)
        wpm = float(latest.get("wpm") or 0.0)
        posture = float(latest.get("posture_score") or 0.0) * 100.0
        self.metric_cards[0].set_value(f"{score:.0f}")
        self.metric_cards[1].set_value(f"{eye:.0f}%")
        self.metric_cards[2].set_value(f"{wpm:.0f}")
        self.metric_cards[3].set_value(f"{posture:.0f}%")
        self.confidence_ring.animate_to(score)

        labels = [str(index + 1) for index in range(len(sessions))]
        scores = [float(session.get("confidence_score") or 0.0) for session in sessions]
        self.progress_chart.set_data(labels, scores)

        if last_session:
            self.subheading.setText(
                f"Latest session: {float(last_session.get('confidence_score') or 0.0):.0f}/100, grade {last_session.get('grade', 'D')}"
            )
