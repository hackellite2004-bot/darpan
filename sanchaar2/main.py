from __future__ import annotations

import os
import sys
from pathlib import Path

# Reduce noisy third-party ML logs so terminal only shows actionable errors.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "3")
os.environ.setdefault("GLOG_minloglevel", "3")
os.environ.setdefault("ABSL_MIN_LOG_LEVEL", "3")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("HF_HUB_VERBOSITY", "error")
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("DISABLE_TQDM", "1")


class _FilteredStderr:
    """Drop recurring non-actionable warnings from third-party native libs."""

    _DROP_MARKERS = (
        "inference_feedback_manager.cc:121",
        "landmark_projection_calculator.cc:81",
        "You are sending unauthenticated requests to the HF Hub",
        "Loading weights:",
    )

    def __init__(self, wrapped):
        self._wrapped = wrapped

    def write(self, text: str) -> int:
        if any(marker in text for marker in self._DROP_MARKERS):
            return len(text)
        return self._wrapped.write(text)

    def flush(self) -> None:
        self._wrapped.flush()


sys.stderr = _FilteredStderr(sys.stderr)

# Ensure the sanchaar2 directory is in the Python path for imports
_PROJECT_DIR = Path(__file__).parent
if str(_PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(_PROJECT_DIR))

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from core.database import init_database
from config import DB_PATH
from ui.main_window import MainWindow
from ui.styles import GLOBAL_STYLESHEET


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Darpan")
    app.setApplicationVersion("2.0.0")
    app.setStyleSheet(GLOBAL_STYLESHEET)
    init_database(DB_PATH)

    window = MainWindow()
    window.setWindowTitle("Darpan — Communication Intelligence Mirror")
    window.resize(1200, 800)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
