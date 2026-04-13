from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ai.coaching import generate_interview_question
from analysis.score_engine import compute_confidence_score
from analysis.speech_analyzer import analyze_speech
from analysis.voice_tone_analyzer import analyze_voice_tone
from config import SESSION_DIR
from core.recorder import SessionRecorder


class InterviewPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_user: dict[str, Any] | None = None
        self.questions: list[str] = []
        self.question_index = 0
        self.current_context = "Job Interview"
        self.answer_recorder: SessionRecorder | None = None
        self.answer_dir: Path | None = None
        self.answer_timer = QTimer(self)
        self.answer_timer.setSingleShot(True)
        self.answer_timer.timeout.connect(self.finish_answer)
        self.answer_duration = 15
        self.question_results: list[dict[str, Any]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        self.heading = QLabel("Interview mode")
        self.heading.setObjectName("PageHeading")
        outer.addWidget(self.heading)

        controls = QHBoxLayout()
        self.context_box = QComboBox()
        self.context_box.addItems(["Job Interview", "College Admission", "Public Speaking", "Debate", "Casual Conversation"])
        self.generate_button = QPushButton("Generate Questions")
        self.generate_button.clicked.connect(self.generate_questions)
        self.back_button = QPushButton("Back to Home")
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.clicked.connect(lambda: self._navigate("home"))
        controls.addWidget(self.context_box)
        controls.addWidget(self.generate_button)
        controls.addStretch(1)
        controls.addWidget(self.back_button)
        outer.addLayout(controls)

        self.question_card = QFrame()
        self.question_card.setProperty("class", "card")
        question_layout = QVBoxLayout(self.question_card)
        self.question_label = QLabel("Generate a set of questions to begin.")
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.tip_label = QLabel("You can answer each question in about 15 seconds.")
        self.tip_label.setProperty("class", "muted")
        self.status_label = QLabel("")
        self.status_label.setProperty("class", "muted")
        question_layout.addWidget(self.question_label)
        question_layout.addWidget(self.tip_label)
        question_layout.addWidget(self.status_label)
        outer.addWidget(self.question_card)

        answer_row = QHBoxLayout()
        self.start_answer_button = QPushButton("Start Answer")
        self.start_answer_button.clicked.connect(self.start_answer)
        self.stop_answer_button = QPushButton("Stop Answer")
        self.stop_answer_button.setObjectName("SecondaryButton")
        self.stop_answer_button.clicked.connect(self.finish_answer)
        self.next_button = QPushButton("Next Question")
        self.next_button.setObjectName("SecondaryButton")
        self.next_button.clicked.connect(self.next_question)
        answer_row.addWidget(self.start_answer_button)
        answer_row.addWidget(self.stop_answer_button)
        answer_row.addWidget(self.next_button)
        outer.addLayout(answer_row)

        self.results_card = QFrame()
        self.results_card.setProperty("class", "card")
        results_layout = QVBoxLayout(self.results_card)
        self.results_label = QLabel("Per-question results will appear here.")
        self.results_label.setWordWrap(True)
        results_layout.addWidget(self.results_label)
        self.results_list = QListWidget()
        results_layout.addWidget(self.results_list)
        outer.addWidget(self.results_card, 1)

        self.footer = QLabel("Final interview report will summarize your responses and scores.")
        self.footer.setProperty("class", "muted")
        outer.addWidget(self.footer)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def generate_questions(self) -> None:
        self.current_context = self.context_box.currentText()
        age_group = self.current_user.get("age_group", "college") if self.current_user else "college"
        self.questions = [generate_interview_question(self.current_context, index + 1, age_group) for index in range(5)]
        self.question_index = 0
        self.question_results = []
        self.results_list.clear()
        self.show_current_question()

    def show_current_question(self) -> None:
        if not self.questions:
            self.question_label.setText("Generate a set of questions to begin.")
            return
        self.question_label.setText(self.questions[self.question_index])
        self.status_label.setText(f"Question {self.question_index + 1} of {len(self.questions)}")

    def start_answer(self) -> None:
        if not self.questions:
            self.generate_questions()
        if self.answer_recorder is not None:
            self.answer_recorder.cleanup()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.answer_dir = SESSION_DIR / f"interview_{timestamp}"
        self.answer_dir.mkdir(parents=True, exist_ok=True)
        self.answer_recorder = SessionRecorder()
        try:
            self.answer_recorder.start(self.answer_dir)
            self.status_label.setText("Recording answer...")
            self.answer_timer.start(self.answer_duration * 1000)
        except Exception as exc:
            self.status_label.setText(str(exc))

    def finish_answer(self) -> None:
        if self.answer_recorder is None:
            return
        self.answer_timer.stop()
        try:
            video_path, audio_path = self.answer_recorder.stop()
        except Exception as exc:
            self.status_label.setText(str(exc))
            return
        speech = analyze_speech(audio_path)
        voice = analyze_voice_tone(audio_path)
        metrics = {
            "eye_center_pct": 50.0,
            "emotion_happy": 0.4,
            "emotion_neutral": 0.4,
            "posture_score": 0.6,
            "gesture_positive_pct": 45.0,
            "wpm": speech.get("wpm", 0.0),
            "filler_count": speech.get("total_fillers", 0),
            "pause_count": speech.get("pause_count", 0),
            "voice_score": voice.get("voice_score", 0.0),
        }
        score_info = compute_confidence_score(metrics)
        result = {
            "question": self.questions[self.question_index] if self.questions else "",
            "transcript": speech.get("transcript", ""),
            "score": score_info["score"],
            "grade": score_info["grade"],
            "feedback": f"Good job answering question {self.question_index + 1}. Focus on fewer fillers and a steadier pace next time.",
            "video_path": str(video_path),
            "audio_path": str(audio_path),
        }
        self.question_results.append(result)
        self.results_list.addItem(QListWidgetItem(f"Q{self.question_index + 1}: {score_info['score']:.0f}/100 - {score_info['grade']}"))
        self.results_label.setText(f"Latest answer scored {score_info['score']:.0f}/100.")
        self.status_label.setText("Analysis complete. Review the tip, then continue.")
        self.answer_recorder.cleanup()
        self.answer_recorder = None

    def next_question(self) -> None:
        if self.question_index < len(self.questions) - 1:
            self.question_index += 1
            self.show_current_question()
            return
        self.question_label.setText("Interview complete. Review your overall performance below.")
        total = sum(item["score"] for item in self.question_results) / len(self.question_results) if self.question_results else 0.0
        self.results_label.setText(f"Overall interview score: {total:.0f}/100")
        self.status_label.setText("You completed the mock interview.")
