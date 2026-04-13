from __future__ import annotations

from collections import defaultdict
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from config import DB_PATH, ROLE_TEACHER
from core.database import execute_query, get_all_users, get_sessions_for_user

try:
    from openpyxl import Workbook
except Exception:  # pragma: no cover
    Workbook = None


class TeacherPage(QWidget):
    navigate_requested = Signal(str)

    def __init__(self, main_window=None):
        super().__init__(main_window)
        self.main_window = main_window
        self.current_user: dict[str, Any] | None = None
        self.students: list[dict[str, Any]] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        self.heading = QLabel("Teacher dashboard")
        self.heading.setObjectName("PageHeading")
        outer.addWidget(self.heading)

        summary_row = QHBoxLayout()
        self.class_average = QFrame()
        self.class_average.setProperty("class", "card")
        avg_layout = QVBoxLayout(self.class_average)
        self.average_label = QLabel("Class average")
        self.average_value = QLabel("--")
        self.average_value.setStyleSheet("font-size: 30px; font-weight: 800;")
        avg_layout.addWidget(self.average_label)
        avg_layout.addWidget(self.average_value)

        self.alert_card = QFrame()
        self.alert_card.setProperty("class", "card")
        alert_layout = QVBoxLayout(self.alert_card)
        self.alert_label = QLabel("Practice alerts")
        self.alert_value = QLabel("--")
        self.alert_value.setWordWrap(True)
        alert_layout.addWidget(self.alert_label)
        alert_layout.addWidget(self.alert_value)

        summary_row.addWidget(self.class_average)
        summary_row.addWidget(self.alert_card)
        outer.addLayout(summary_row)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Student Name", "Sessions", "Avg Score", "Last Active", "Trend"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.cellDoubleClicked.connect(self.open_student)
        outer.addWidget(self.table, 1)

        bottom = QHBoxLayout()
        self.export_button = QPushButton("Export Excel report")
        self.refresh_button = QPushButton("Refresh")
        self.back_button = QPushButton("Back to Home")
        self.export_button.clicked.connect(self.export_excel)
        self.refresh_button.clicked.connect(self.refresh_data)
        self.back_button.setObjectName("SecondaryButton")
        self.back_button.clicked.connect(lambda: self._navigate("home"))
        bottom.addWidget(self.export_button)
        bottom.addWidget(self.refresh_button)
        bottom.addWidget(self.back_button)
        bottom.addStretch(1)
        outer.addLayout(bottom)

    def set_user_context(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        self.refresh_data()

    def _navigate(self, page: str) -> None:
        if self.main_window is not None:
            self.main_window.navigate(page)
        else:
            self.navigate_requested.emit(page)

    def refresh_data(self) -> None:
        if not self.current_user or self.current_user.get("role") != ROLE_TEACHER:
            self.heading.setText("Teacher dashboard")
            self.table.setRowCount(0)
            self.average_value.setText("--")
            self.alert_value.setText("Log in as a teacher to view class data.")
            return

        students = [user for user in get_all_users(DB_PATH) if user.get("role") != ROLE_TEACHER]
        self.students = students
        all_scores = []
        alert_names = []
        self.table.setRowCount(0)
        for row_index, student in enumerate(students):
            sessions = get_sessions_for_user(DB_PATH, student["id"])
            scores = [float(session.get("confidence_score") or 0.0) for session in sessions]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            all_scores.extend(scores)
            last_active = sessions[-1]["timestamp"] if sessions else "Never"
            trend = self._trend(scores)
            self.table.insertRow(row_index)
            values = [student.get("name", ""), str(len(sessions)), f"{avg_score:.0f}", str(last_active)[:10], trend]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_index, col, item)
            if len(sessions) and self._days_since_last(sessions[-1].get("timestamp")) > 7:
                alert_names.append(student.get("name", "Unknown"))

        self.average_value.setText(f"{(sum(all_scores)/len(all_scores)):.0f}" if all_scores else "--")
        self.alert_value.setText(
            "These students haven't practiced in 7+ days: " + ", ".join(alert_names) if alert_names else "Everyone has practiced recently."
        )

    def _days_since_last(self, timestamp: Any) -> int:
        from datetime import datetime

        if not timestamp:
            return 999
        try:
            last = datetime.fromisoformat(str(timestamp).replace(" ", "T")).date()
            return (datetime.now().date() - last).days
        except Exception:
            return 999

    def _trend(self, scores: list[float]) -> str:
        if len(scores) < 2:
            return "-"
        return "▲" if scores[-1] > scores[0] + 3 else ("▼" if scores[-1] < scores[0] - 3 else "■")

    def open_student(self, row: int, column: int) -> None:
        if not self.main_window or row < 0 or row >= len(self.students):
            return
        student = self.students[row]
        self.main_window.set_user(student)
        self.main_window.navigate("history")

    def export_excel(self) -> None:
        if Workbook is None:
            QMessageBox.warning(self, "Unavailable", "openpyxl is not installed.")
            return
        if not self.students:
            QMessageBox.information(self, "No data", "No students available to export.")
            return
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Students"
        sheet.append(["Student Name", "Sessions", "Avg Score", "Last Active", "Trend"])
        for row in range(self.table.rowCount()):
            sheet.append([self.table.item(row, col).text() for col in range(self.table.columnCount())])
        from datetime import datetime
        output = f"teacher_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        workbook.save(output)
        QMessageBox.information(self, "Exported", f"Excel report saved to {output}")
