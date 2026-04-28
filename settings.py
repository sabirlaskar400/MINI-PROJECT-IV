"""
ui/settings.py
--------------
Settings panel:
  - Dark / Light mode toggle
  - Camera index selector
  - Detection confidence threshold
  - About info
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox,
    QFrame, QCheckBox,
)
from PyQt6.QtCore import Qt, pyqtSignal

from .theme import THEME, NeonButton, SectionTitle, Divider


class SettingsPanel(QWidget):
    theme_changed  = pyqtSignal(bool)   # True = dark
    camera_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dark = True
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)
        root.setAlignment(Qt.AlignmentFlag.AlignTop)

        root.addWidget(SectionTitle("Settings", THEME["accent_blue"]))

        # ── Appearance ────────────────────────────────────────────────── #
        root.addWidget(self._section_header("Appearance"))

        row = QHBoxLayout()
        lbl = QLabel("Theme Mode")
        lbl.setStyleSheet(f"font-size: 13px; color: {THEME['text_primary']};")
        row.addWidget(lbl)
        row.addStretch()

        self.btn_dark  = NeonButton("🌙  Dark Mode",  THEME["accent_blue"])
        self.btn_light = NeonButton("☀  Light Mode", THEME["accent_amber"])
        self.btn_dark.clicked.connect(lambda: self._set_theme(True))
        self.btn_light.clicked.connect(lambda: self._set_theme(False))
        row.addWidget(self.btn_dark)
        row.addWidget(self.btn_light)
        root.addLayout(row)

        root.addWidget(Divider())

        # ── Camera ────────────────────────────────────────────────────── #
        root.addWidget(self._section_header("Camera"))

        cam_row = QHBoxLayout()
        cam_row.addWidget(QLabel("Camera Index"))
        cam_row.addStretch()
        self.cam_combo = QComboBox()
        self.cam_combo.addItems(["0 – Default", "1 – Secondary", "2 – Tertiary"])
        self.cam_combo.setFixedWidth(200)
        self.cam_combo.currentIndexChanged.connect(
            lambda i: self.camera_changed.emit(i)
        )
        cam_row.addWidget(self.cam_combo)
        root.addLayout(cam_row)
        root.addWidget(Divider())

        # ── Detection ─────────────────────────────────────────────────── #
        root.addWidget(self._section_header("Detection"))

        conf_row = QHBoxLayout()
        conf_lbl = QLabel("Confidence Threshold")
        conf_lbl.setStyleSheet(f"font-size: 13px; color: {THEME['text_primary']};")
        conf_row.addWidget(conf_lbl)
        conf_row.addStretch()

        self.conf_val = QLabel("0.50")
        self.conf_val.setStyleSheet(
            f"font-size: 13px; color: {THEME['accent_blue']}; font-weight: bold;"
        )
        self.conf_slider = QSlider(Qt.Orientation.Horizontal)
        self.conf_slider.setRange(10, 95)
        self.conf_slider.setValue(50)
        self.conf_slider.setFixedWidth(200)
        self.conf_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {THEME['border']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {THEME['accent_blue']};
                width: 16px;
                height: 16px;
                border-radius: 8px;
                margin: -5px 0;
            }}
            QSlider::sub-page:horizontal {{
                background: {THEME['accent_blue']};
                border-radius: 3px;
            }}
        """)
        self.conf_slider.valueChanged.connect(
            lambda v: self.conf_val.setText(f"{v/100:.2f}")
        )
        conf_row.addWidget(self.conf_slider)
        conf_row.addWidget(self.conf_val)
        root.addLayout(conf_row)
        root.addWidget(Divider())

        # ── About ─────────────────────────────────────────────────────── #
        root.addWidget(self._section_header("About"))

        about = QFrame()
        about.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-radius: 12px;
            }}
        """)
        about_layout = QVBoxLayout(about)
        about_layout.setContentsMargins(20, 16, 20, 16)
        about_layout.setSpacing(6)

        for line, style in [
            ("AI Object Analytics System",
             f"font-size:15px;font-weight:bold;color:{THEME['accent_blue']};"),
            ("BCA Semester Project  ·  Computer Vision",
             f"font-size:12px;color:{THEME['text_secondary']};"),
            ("",
             ""),
            ("Powered by  YOLOv8 · OpenCV · Supervision · PyQt6",
             f"font-size:12px;color:{THEME['text_muted']};"),
            ("Build: 2026 · Python 3.10+",
             f"font-size:11px;color:{THEME['text_muted']};"),
        ]:
            lbl = QLabel(line)
            lbl.setStyleSheet(style)
            about_layout.addWidget(lbl)

        root.addWidget(about)
        root.addStretch()

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(
            f"font-size: 11px; color: {THEME['text_secondary']}; letter-spacing: 3px; margin-top:8px;"
        )
        return lbl

    def _set_theme(self, dark: bool):
        self._dark = dark
        self.theme_changed.emit(dark)
