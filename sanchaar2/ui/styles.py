from __future__ import annotations

from config import (
    COLOR_ACCENT,
    COLOR_BG_DARK,
    COLOR_BORDER,
    COLOR_CARD,
    COLOR_DANGER,
    COLOR_MUTED,
    COLOR_PRIMARY,
    COLOR_SURFACE,
    COLOR_TEXT,
)

FONT_STACK = '"Trebuchet MS", "Segoe UI", "Verdana", sans-serif'


def build_stylesheet(dark: bool = True) -> str:
    background = COLOR_BG_DARK if dark else "#F3F7FA"
    surface = COLOR_SURFACE if dark else "#FFFFFF"
    card = COLOR_CARD if dark else "#FFFFFF"
    text = COLOR_TEXT if dark else "#1E2A33"
    muted = COLOR_MUTED if dark else "#465664"
    border = COLOR_BORDER if dark else "#D2DEE7"
    button_hover = "#0D7CAB" if dark else "#0A5F86"
    button_pressed = "#0A5F86" if dark else "#084B6A"
    progress_bg = "#244256" if dark else "#DFE9F0"
    progress_fill = COLOR_ACCENT

    return f"""
    * {{
        font-family: {FONT_STACK};
    }}

    QMainWindow {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
            stop:0 #F8F3EC, stop:0.45 #F3F8FB, stop:1 #EAF4EE);
        color: {text};
    }}

    QWidget {{
        color: {text};
    }}

    QLabel {{
        color: {text};
    }}

    QLabel#PageHeading, QLabel[class="heading"] {{
        font-size: 23px;
        font-weight: 700;
    }}

    QLabel[class="muted"] {{
        color: {muted};
    }}

    QFrame[class="card"] {{
        background: {card};
        border-radius: 16px;
        border: 1px solid {border};
    }}

    QFrame[class="surface"] {{
        background: {surface};
        border-radius: 16px;
        border: 1px solid {border};
    }}

    QPushButton {{
        border: none;
        border-radius: 10px;
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 {COLOR_PRIMARY}, stop:1 #2D8AB4);
        color: white;
        padding: 10px 18px;
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {button_hover};
    }}

    QPushButton:pressed {{
        background: {button_pressed};
    }}

    QPushButton#SecondaryButton {{
        background: transparent;
        border: 1px solid {border};
        color: {text};
    }}

    QPushButton#SecondaryButton:hover {{
        background: rgba(11, 110, 153, 0.10);
    }}

    QLabel[class="loading"] {{
        color: {text};
        font-weight: 600;
        padding: 8px 10px;
        border-radius: 8px;
        background: rgba(11, 110, 153, 0.14);
        border: 1px solid rgba(11, 110, 153, 0.35);
    }}

    QLabel[class="status_ok"] {{
        color: #1F9D73;
        font-weight: 700;
    }}

    QLabel[class="status_warn"] {{
        color: #C17F00;
        font-weight: 700;
    }}

    QPushButton#DangerButton {{
        background: {COLOR_DANGER};
        color: white;
    }}

    QLineEdit, QComboBox, QTextEdit, QPlainTextEdit, QTableWidget {{
        background: {surface};
        border: 1px solid {border};
        border-radius: 10px;
        padding: 8px 10px;
        selection-background-color: {COLOR_PRIMARY};
        selection-color: white;
    }}

    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}

    QTabWidget::pane {{
        border: 1px solid {border};
        border-radius: 16px;
        top: -1px;
    }}

    QTabBar::tab {{
        background: transparent;
        padding: 10px 16px;
        border-top-left-radius: 10px;
        border-top-right-radius: 10px;
        color: {muted};
    }}

    QTabBar::tab:selected {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
            stop:0 rgba(11,110,153,0.20), stop:1 rgba(45,138,180,0.16));
        color: {text};
        border: 1px solid {border};
    }}

    QProgressBar {{
        border: none;
        background: {progress_bg};
        border-radius: 8px;
        text-align: center;
        color: {text};
        min-height: 16px;
    }}

    QProgressBar::chunk {{
        background: {progress_fill};
        border-radius: 8px;
    }}

    QScrollArea {{
        border: none;
        background: transparent;
    }}

    QTableWidget::item:selected {{
        background: rgba(11, 110, 153, 0.22);
    }}

    QHeaderView::section {{
        background: {surface};
        color: {text};
        border: none;
        padding: 8px 10px;
        border-bottom: 1px solid {border};
    }}

    QToolButton {{
        border: none;
        background: transparent;
        padding: 8px;
        color: {text};
    }}

    QSlider::groove:horizontal {{
        height: 6px;
        background: {progress_bg};
        border-radius: 3px;
    }}

    QSlider::handle:horizontal {{
        background: {COLOR_PRIMARY};
        width: 16px;
        margin: -6px 0;
        border-radius: 8px;
    }}
    """


DARK_STYLESHEET = build_stylesheet(True)
LIGHT_STYLESHEET = build_stylesheet(False)
GLOBAL_STYLESHEET = LIGHT_STYLESHEET
