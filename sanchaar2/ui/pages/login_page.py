from __future__ import annotations

import uuid
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QStackedLayout,
    QVBoxLayout,
    QWidget,
)

from config import AGE_GROUPS, COLOR_ACCENT, COLOR_PRIMARY, ROLE_STUDENT, ROLE_TEACHER, DB_PATH
from core.database import execute_query, get_last_session_for_user, get_user_by_id, upsert_user


class RoleCard(QFrame):
    clicked = Signal(str)

    def __init__(self, role: str, title: str, subtitle: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.setProperty("class", "card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(8)
        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 22px; font-weight: 700;")
        self.subtitle = QLabel(subtitle)
        self.subtitle.setWordWrap(True)
        self.subtitle.setProperty("class", "muted")
        layout.addStretch(1)
        layout.addWidget(self.title)
        layout.addWidget(self.subtitle)
        layout.addStretch(1)

    def mousePressEvent(self, event):  # noqa: N802
        self.clicked.emit(self.role)
        super().mousePressEvent(event)


class LoginPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.selected_role = ROLE_STUDENT
        self.current_user: dict[str, Any] | None = None
        self.last_session: dict[str, Any] | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(18)

        self.welcome = QLabel("Welcome back")
        self.welcome.setObjectName("PageHeading")
        self.summary = QLabel("Choose your role to continue.")
        self.summary.setProperty("class", "muted")

        self.hero_card = QFrame()
        self.hero_card.setProperty("class", "surface")
        hero_layout = QVBoxLayout(self.hero_card)
        hero_layout.addWidget(self.welcome)
        hero_layout.addWidget(self.summary)

        outer.addWidget(self.hero_card)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)
        self.student_card = RoleCard(ROLE_STUDENT, "Student", "Practice speaking skills, track growth, and get AI feedback.")
        self.teacher_card = RoleCard(ROLE_TEACHER, "Teacher", "Review class progress, trends, and export reports.")
        self.student_card.clicked.connect(self.select_role)
        self.teacher_card.clicked.connect(self.select_role)
        cards_row.addWidget(self.student_card)
        cards_row.addWidget(self.teacher_card)
        outer.addLayout(cards_row)

        self.form_stack = QStackedLayout()
        self.student_form = self._build_student_form()
        self.teacher_form = self._build_teacher_form()
        self.form_stack.addWidget(self.student_form)
        self.form_stack.addWidget(self.teacher_form)
        outer.addLayout(self.form_stack)

        button_row = QHBoxLayout()
        button_row.addStretch(1)
        self.continue_button = QPushButton("Continue")
        self.continue_button.clicked.connect(self.save_and_continue)
        button_row.addWidget(self.continue_button)
        outer.addLayout(button_row)

        self.select_role(ROLE_STUDENT)

    def _build_student_form(self) -> QWidget:
        frame = QFrame()
        frame.setProperty("class", "card")
        layout = QGridLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(12)

        layout.addWidget(QLabel("Student name"), 0, 0)
        self.student_name = QLineEdit()
        self.student_name.setPlaceholderText("Enter student name")
        layout.addWidget(self.student_name, 1, 0, 1, 2)

        layout.addWidget(QLabel("Age group"), 2, 0)
        self.age_group = QComboBox()
        for key, label in AGE_GROUPS.items():
            self.age_group.addItem(label, key)
        layout.addWidget(self.age_group, 3, 0, 1, 2)
        return frame

    def _build_teacher_form(self) -> QWidget:
        frame = QFrame()
        frame.setProperty("class", "card")
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(QLabel("Teacher name"))
        self.teacher_name = QLineEdit()
        self.teacher_name.setPlaceholderText("Enter teacher name")
        layout.addWidget(self.teacher_name)
        return frame

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        if not user:
            self.welcome.setText("Welcome to Darpan")
            self.summary.setText("Choose a role and continue.")
            return
        self.last_session = get_last_session_for_user(DB_PATH, user["id"])
        score_text = "no sessions yet"
        if self.last_session and self.last_session.get("confidence_score") is not None:
            score_text = f"last score {float(self.last_session['confidence_score']):.0f}/100"
        self.welcome.setText(f"Welcome back {user.get('name', 'there')}")
        self.summary.setText(score_text)
        if user.get("role") == ROLE_TEACHER:
            self.select_role(ROLE_TEACHER)
            self.teacher_name.setText(user.get("name", ""))
        else:
            self.select_role(ROLE_STUDENT)
            self.student_name.setText(user.get("name", ""))
            age_group = user.get("age_group")
            if age_group:
                index = self.age_group.findData(age_group)
                if index >= 0:
                    self.age_group.setCurrentIndex(index)

    def select_role(self, role: str) -> None:
        self.selected_role = role
        self.form_stack.setCurrentIndex(0 if role == ROLE_STUDENT else 1)
        self.student_card.setStyleSheet("border: 2px solid #6C63FF;" if role == ROLE_STUDENT else "")
        self.teacher_card.setStyleSheet("border: 2px solid #6C63FF;" if role == ROLE_TEACHER else "")

    def save_and_continue(self) -> None:
        if self.selected_role == ROLE_STUDENT:
            name = self.student_name.text().strip()
            if not name:
                self.summary.setText("Please enter the student name.")
                return
            age_group = self.age_group.currentData()
            existing = execute_query(DB_PATH, "SELECT * FROM users WHERE lower(name)=lower(?) AND role=? LIMIT 1", (name, ROLE_STUDENT))
            user_id = existing[0]["id"] if existing else str(uuid.uuid4())
            user = upsert_user(DB_PATH, {"id": user_id, "name": name, "role": ROLE_STUDENT, "age_group": age_group, "teacher_id": None})
        else:
            name = self.teacher_name.text().strip()
            if not name:
                self.summary.setText("Please enter the teacher name.")
                return
            existing = execute_query(DB_PATH, "SELECT * FROM users WHERE lower(name)=lower(?) AND role=? LIMIT 1", (name, ROLE_TEACHER))
            user_id = existing[0]["id"] if existing else str(uuid.uuid4())
            user = upsert_user(DB_PATH, {"id": user_id, "name": name, "role": ROLE_TEACHER, "age_group": None, "teacher_id": None})

        if self.main_window is not None:
            self.main_window.set_user(user)
            self.main_window.navigate("home")
        else:
            self.navigate_requested.emit("home")
