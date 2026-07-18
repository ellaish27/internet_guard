"""Small frameless bottom-right countdown overlay, shown while internet
access is unlocked so the child can see how much time is left."""
from __future__ import annotations
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget
from common.theme import apply_theme


class OverlayWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setFixedSize(190, 70)
        apply_theme(self)
        self.setObjectName("overlay")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        title = QLabel("Internet Active")
        title.setObjectName("overlayTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.time_label = QLabel("00:00")
        self.time_label.setObjectName("overlayTime")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

    def show(self) -> None:
        self._move_to_corner()
        super().show()

    def update_time(self, seconds_remaining: int) -> None:
        h = seconds_remaining // 3600
        m = (seconds_remaining % 3600) // 60
        s = seconds_remaining % 60
        self.time_label.setText(f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}")

    def _move_to_corner(self) -> None:
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 10, screen.bottom() - self.height() - 10)
