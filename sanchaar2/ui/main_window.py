from __future__ import annotations

from functools import partial
from typing import Any

from PySide6.QtCore import QEasingCurve, Property, QPropertyAnimation, QSize, Qt
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QStyle,
)

from config import DB_PATH, ROLE_TEACHER
from core.database import get_last_session_for_user, get_latest_user
from core.session_manager import SessionManager
from ui.components.confidence_ring import ConfidenceRing
from ui.pages.history_page import HistoryPage
from ui.pages.home_page import HomePage
from ui.pages.interview_page import InterviewPage
from ui.pages.login_page import LoginPage
from ui.pages.record_page import RecordPage
from ui.pages.results_page import ResultsPage
from ui.pages.splash_page import SplashPage
from ui.pages.teacher_page import TeacherPage


class SidebarButton(QToolButton):
    def __init__(self, title: str, icon, parent=None):
        super().__init__(parent)
        self.full_title = title
        self.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.setIcon(icon)
        self.setText(title)
        self.setCheckable(True)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(42)

    def set_compact(self, compact: bool) -> None:
        self.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonIconOnly if compact else Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )
        self.setText("" if compact else self.full_title)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_path = DB_PATH
        self.session_manager = SessionManager(self.db_path)
        self.current_user: dict[str, Any] | None = get_latest_user(self.db_path)
        self.current_session_result: dict[str, Any] | None = None
        self.dark_mode = False
        self._compact_sidebar = False

        central = QWidget(self)
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(16, 16, 16, 16)
        root_layout.setSpacing(16)

        self.sidebar = QFrame()
        self.sidebar.setProperty("class", "surface")
        self.sidebar.setMinimumWidth(88)
        self.sidebar.setMaximumWidth(260)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(14, 16, 14, 16)
        sidebar_layout.setSpacing(10)

        self.brand_label = QLabel("Darpan")
        self.brand_label.setStyleSheet("font-size: 18px; font-weight: 700;")
        sidebar_layout.addWidget(self.brand_label)

        self.nav_buttons: dict[str, SidebarButton] = {}
        nav_specs = [
            ("home", "Home", self.style().standardIcon(QStyle.StandardPixmap.SP_DesktopIcon)),
            ("record", "Record", self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay)),
            ("history", "History", self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogContentsView)),
            ("interview", "Interview", self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxInformation)),
            ("teacher", "Teacher", self.style().standardIcon(QStyle.StandardPixmap.SP_DirHomeIcon)),
        ]
        for key, title, icon in nav_specs:
            button = SidebarButton(title, icon)
            button.clicked.connect(partial(self.navigate, key))
            self.nav_buttons[key] = button
            sidebar_layout.addWidget(button)

        sidebar_layout.addStretch(1)

        self.stack = QStackedWidget()
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.pages = {
            "splash": SplashPage(self),
            "login": LoginPage(self),
            "home": HomePage(self),
            "record": RecordPage(self),
            "results": ResultsPage(self),
            "history": HistoryPage(self),
            "interview": InterviewPage(self),
            "teacher": TeacherPage(self),
        }
        for page in self.pages.values():
            self.stack.addWidget(page)

        self.top_bar = QFrame()
        self.top_bar.setProperty("class", "surface")
        top_layout = QHBoxLayout(self.top_bar)
        top_layout.setContentsMargins(18, 12, 18, 12)
        top_layout.setSpacing(12)
        self.page_title = QLabel("Darpan")
        self.page_title.setObjectName("PageHeading")
        self.user_label = QLabel("Guest")
        self.user_label.setProperty("class", "muted")
        self.avatar = QLabel()
        self.avatar.setFixedSize(34, 34)
        self.avatar.setStyleSheet("border-radius: 17px; background: #0B6E99; color: white; font-weight: 700;")
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.theme_toggle = QPushButton("Dark mode")
        self.theme_toggle.setObjectName("SecondaryButton")
        self.theme_toggle.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.page_title)
        top_layout.addStretch(1)
        top_layout.addWidget(self.user_label)
        top_layout.addWidget(self.avatar)
        top_layout.addWidget(self.theme_toggle)

        content = QVBoxLayout()
        content.setSpacing(16)
        content.addWidget(self.top_bar)
        content.addWidget(self.stack, 1)

        content_wrapper = QWidget()
        content_wrapper.setLayout(content)

        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(content_wrapper, 1)

        self._fade_effect = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self._fade_effect)
        self._fade_anim = QPropertyAnimation(self._fade_effect, b"opacity", self)
        self._fade_anim.setDuration(220)
        self._fade_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.navigate("splash")
        self.refresh_user_context()

    def current_page(self):
        return self.stack.currentWidget()

    def navigate(self, page_key: str) -> None:
        if page_key not in self.pages:
            return
        if self.stack.currentWidget() is self.pages[page_key]:
            return
        self._fade_anim.stop()
        self._fade_effect.setOpacity(0.0)
        self.stack.setCurrentWidget(self.pages[page_key])
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.start()
        self.page_title.setText(page_key.title())
        for key, button in self.nav_buttons.items():
            button.setChecked(key == page_key)
        self.refresh_user_context()

    def go_home(self) -> None:
        self.navigate("home")

    def set_user(self, user: dict[str, Any] | None) -> None:
        self.current_user = user
        self.session_manager.set_user(user)
        self.refresh_user_context()
        for page in self.pages.values():
            if hasattr(page, "set_user_context"):
                page.set_user_context(user)
            if hasattr(page, "refresh_data"):
                page.refresh_data()

    def set_session_result(self, result: dict[str, Any]) -> None:
        self.current_session_result = result
        results_page = self.pages["results"]
        if hasattr(results_page, "load_result"):
            results_page.load_result(result)
        history_page = self.pages["history"]
        if hasattr(history_page, "refresh_data"):
            history_page.refresh_data()
        home_page = self.pages["home"]
        if hasattr(home_page, "refresh_data"):
            home_page.refresh_data()

    def open_results_for_session(self, session_data: dict[str, Any]) -> None:
        results_page = self.pages["results"]
        if hasattr(results_page, "load_session_data"):
            results_page.load_session_data(session_data)
        self.navigate("results")

    def refresh_user_context(self) -> None:
        user = self.current_user or get_latest_user(self.db_path)
        if user:
            self.user_label.setText(user.get("name", "Guest"))
            initials = "".join(part[:1] for part in user.get("name", "U").split()[:2]).upper() or "U"
            self.avatar.setText(initials)
        else:
            self.user_label.setText("Guest")
            self.avatar.setText("U")
        if hasattr(self.pages["home"], "set_user_context"):
            self.pages["home"].set_user_context(user)
        if hasattr(self.pages["history"], "set_user_context"):
            self.pages["history"].set_user_context(user)
        if hasattr(self.pages["teacher"], "set_user_context"):
            self.pages["teacher"].set_user_context(user)
        if hasattr(self.pages["results"], "set_user_context"):
            self.pages["results"].set_user_context(user)
        if hasattr(self.pages["login"], "set_user_context"):
            self.pages["login"].set_user_context(user)

    def toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        from ui.styles import DARK_STYLESHEET, LIGHT_STYLESHEET

        self.setStyleSheet(DARK_STYLESHEET if self.dark_mode else LIGHT_STYLESHEET)
        self.theme_toggle.setText("Light mode" if self.dark_mode else "Dark mode")

    def resizeEvent(self, event):  # noqa: N802
        super().resizeEvent(event)
        compact = self.width() < 1050
        if compact != self._compact_sidebar:
            self._compact_sidebar = compact
            self.sidebar.setMaximumWidth(92 if compact else 260)
            for button in self.nav_buttons.values():
                button.set_compact(compact)

    def showEvent(self, event):  # noqa: N802
        super().showEvent(event)
        self.refresh_user_context()
