"""
ui/dashboard.py
---------------
Home / Dashboard panel shown at startup.
Displays session summary stats and quick-start instructions.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from datetime import datetime

from .theme import THEME, StatCard, SectionTitle, NeonButton, glow_shadow


class DashboardPanel(QWidget):
    """
    Overview panel – live clock, session stat cards, quick-action tips.
    Receives live counter updates via update_stats().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._start_clock()

    # ------------------------------------------------------------------ #
    #  Build UI                                                             #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(24)

        # ── Header row ──────────────────────────────────────────────── #
        header = QHBoxLayout()

        title_col = QVBoxLayout()
        title_col.setSpacing(4)

        brand = QLabel("AI OBJECT ANALYTICS")
        brand.setStyleSheet(
            f"font-size: 26px; font-weight: bold; color: {THEME['accent_blue']};"
            "letter-spacing: 4px;"
        )

        sub = QLabel("Real-Time Detection & Tracking System  ·  YOLOv8 + Supervision")
        sub.setStyleSheet(
            f"font-size: 12px; color: {THEME['text_secondary']}; letter-spacing: 1px;"
        )

        title_col.addWidget(brand)
        title_col.addWidget(sub)
        header.addLayout(title_col)
        header.addStretch()

        # Live clock
        self.clock_label = QLabel()
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.clock_label.setStyleSheet(
            f"font-size: 28px; font-weight: bold; color: {THEME['accent_blue']}88;"
            "letter-spacing: 2px; font-family: 'Courier New';"
        )
        header.addWidget(self.clock_label)
        root.addLayout(header)

        # ── Stat cards row ───────────────────────────────────────────── #
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        self.card_in     = StatCard("Objects IN",    "0", THEME["accent_green"])
        self.card_out    = StatCard("Objects OUT",   "0", THEME["accent_red"])
        self.card_total  = StatCard("Total Events",  "0", THEME["accent_blue"])
        self.card_active = StatCard("Net Present",   "0", THEME["accent_purple"])

        for card in (self.card_in, self.card_out, self.card_total, self.card_active):
            cards_row.addWidget(card)
        root.addLayout(cards_row)

        # ── Instructions card ────────────────────────────────────────── #
        root.addWidget(SectionTitle("Quick Start", THEME["accent_purple"]))

        steps_frame = QFrame()
        steps_frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-radius: 12px;
            }}
        """)
        steps_layout = QGridLayout(steps_frame)
        steps_layout.setContentsMargins(24, 20, 24, 20)
        steps_layout.setSpacing(14)

        steps = [
            ("01", "Click  Live Camera  in the sidebar to open the webcam view."),
            ("02", "Press  ▶ START CAMERA  – the YOLOv8 model loads automatically."),
            ("03", "Move a bottle, scissors, or phone across the blue counting line."),
            ("04", "Watch IN / OUT counters update in real-time."),
            ("05", "Visit  Analytics  to see category charts and live graphs."),
            ("06", "Go to  Reports  to view the movement log or export CSV."),
            ("07", "Press  💾 Save Session  to persist data to project_report.txt."),
        ]

        for i, (num, text) in enumerate(steps):
            num_label = QLabel(num)
            num_label.setFixedWidth(32)
            num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num_label.setStyleSheet(
                f"font-size: 11px; font-weight: bold; color: {THEME['accent_blue']};"
                f"background: {THEME['accent_blue']}22; border-radius: 4px; padding: 2px;"
            )
            text_label = QLabel(text)
            text_label.setStyleSheet(
                f"font-size: 13px; color: {THEME['text_primary']};"
            )
            steps_layout.addWidget(num_label,  i, 0)
            steps_layout.addWidget(text_label, i, 1)

        root.addWidget(steps_frame)

        # ── System info row ──────────────────────────────────────────── #
        info_row = QHBoxLayout()
        info_row.setSpacing(10)

        for label, val in [
            ("MODEL",   "YOLOv8n"),
            ("BACKEND", "OpenCV + Supervision"),
            ("CLASSES", "Bottle · Scissors · Cell Phone"),
            ("TRIGGER", "Horizontal Line Zone"),
        ]:
            chip = QLabel(f"  {label}: {val}  ")
            chip.setStyleSheet(
                f"background: {THEME['bg_card']}; border: 1px solid {THEME['border']};"
                f"border-radius: 6px; padding: 4px 8px; font-size: 11px;"
                f"color: {THEME['text_secondary']}; letter-spacing: 1px;"
            )
            info_row.addWidget(chip)
        info_row.addStretch()
        root.addLayout(info_row)
        root.addStretch()

    # ------------------------------------------------------------------ #
    #  Clock                                                                #
    # ------------------------------------------------------------------ #
    def _start_clock(self):
        self._tick()
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        self.clock_label.setText(datetime.now().strftime("%H:%M:%S"))

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #
    def update_stats(self, in_count: int, out_count: int):
        self.card_in.set_value(str(in_count))
        self.card_out.set_value(str(out_count))
        self.card_total.set_value(str(in_count + out_count))
        net = max(0, in_count - out_count)
        self.card_active.set_value(str(net))
