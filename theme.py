"""
ui/theme.py
-----------
Single source of truth for colors, fonts, and reusable styled widgets.
Import THEME and the widget helpers from every other UI module.
"""

from PyQt6.QtWidgets import (
    QLabel, QFrame, QPushButton, QWidget, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect,
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QColor, QFont, QPalette

# ─────────────────────────────────────────────────────────────────────────────
#  Color Palette
# ─────────────────────────────────────────────────────────────────────────────
THEME = {
    # Backgrounds
    "bg_dark":     "#0A0E1A",
    "bg_panel":    "#0F1528",
    "bg_card":     "#141C35",
    "bg_hover":    "#1A2445",
    "sidebar_bg":  "#080C18",

    # Accents
    "accent_blue": "#00C8FF",
    "accent_purple": "#7B2FFF",
    "accent_green": "#00FF9C",
    "accent_red":   "#FF3D71",
    "accent_amber": "#FFB800",

    # Text
    "text_primary":   "#E8F0FF",
    "text_secondary": "#7A8BB0",
    "text_muted":     "#3A4A70",

    # Borders
    "border":        "#1E2D50",
    "border_active": "#00C8FF",
}

DARK_STYLESHEET = f"""
QWidget {{
    background-color: {THEME['bg_dark']};
    color: {THEME['text_primary']};
    font-family: 'Consolas', 'Courier New', monospace;
}}
QScrollBar:vertical {{
    background: {THEME['bg_panel']};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {THEME['accent_blue']};
    border-radius: 4px;
    min-height: 20px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar:horizontal {{
    background: {THEME['bg_panel']};
    height: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:horizontal {{
    background: {THEME['accent_blue']};
    border-radius: 4px;
}}
QTableWidget {{
    background-color: {THEME['bg_card']};
    alternate-background-color: {THEME['bg_panel']};
    gridline-color: {THEME['border']};
    border: 1px solid {THEME['border']};
    border-radius: 8px;
    selection-background-color: {THEME['bg_hover']};
}}
QTableWidget::item {{
    padding: 6px 12px;
    color: {THEME['text_primary']};
}}
QHeaderView::section {{
    background-color: {THEME['bg_panel']};
    color: {THEME['accent_blue']};
    font-weight: bold;
    font-size: 11px;
    letter-spacing: 1px;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid {THEME['border_active']};
    text-transform: uppercase;
}}
QLineEdit {{
    background-color: {THEME['bg_card']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 8px 12px;
    color: {THEME['text_primary']};
    font-size: 13px;
}}
QLineEdit:focus {{
    border-color: {THEME['accent_blue']};
}}
QComboBox {{
    background-color: {THEME['bg_card']};
    border: 1px solid {THEME['border']};
    border-radius: 6px;
    padding: 6px 12px;
    color: {THEME['text_primary']};
}}
QComboBox::drop-down {{
    border: none;
}}
"""

LIGHT_STYLESHEET = f"""
QWidget {{
    background-color: #F0F4FF;
    color: #1A1F35;
    font-family: 'Consolas', 'Courier New', monospace;
}}
QScrollBar:vertical {{
    background: #D8E0F0;
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: #2563EB;
    border-radius: 4px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QTableWidget {{
    background-color: #FFFFFF;
    alternate-background-color: #F0F4FF;
    gridline-color: #C8D4F0;
    border: 1px solid #C8D4F0;
    border-radius: 8px;
    selection-background-color: #DBEAFE;
}}
QTableWidget::item {{
    padding: 6px 12px;
    color: #1A1F35;
}}
QHeaderView::section {{
    background-color: #E0E8FF;
    color: #2563EB;
    font-weight: bold;
    font-size: 11px;
    padding: 8px 12px;
    border: none;
    border-bottom: 2px solid #2563EB;
}}
QLineEdit {{
    background-color: #FFFFFF;
    border: 1px solid #C8D4F0;
    border-radius: 6px;
    padding: 8px 12px;
    color: #1A1F35;
}}
QLineEdit:focus {{
    border-color: #2563EB;
}}
"""


# ─────────────────────────────────────────────────────────────────────────────
#  Reusable Widgets
# ─────────────────────────────────────────────────────────────────────────────

def glow_shadow(color: str = "#00C8FF", blur: int = 20) -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, 0)
    shadow.setColor(QColor(color))
    return shadow


class NeonButton(QPushButton):
    """Rounded button with neon glow on hover."""

    def __init__(self, text: str, color: str = "#00C8FF", parent=None):
        super().__init__(text, parent)
        self._color = color
        self._update_style(hover=False)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def _update_style(self, hover: bool):
        alpha = "44" if hover else "22"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self._color}{alpha};
                color: {self._color};
                border: 1px solid {self._color};
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: bold;
                letter-spacing: 1px;
            }}
        """)
        if hover:
            self.setGraphicsEffect(glow_shadow(self._color, 18))
        else:
            self.setGraphicsEffect(None)

    def enterEvent(self, event):
        self._update_style(hover=True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._update_style(hover=False)
        super().leaveEvent(event)


class StatCard(QFrame):
    """Glowing stat card: big number + label."""

    def __init__(self, label: str, value: str = "0",
                 accent: str = "#00C8FF", parent=None):
        super().__init__(parent)
        self._accent = accent
        self.setFixedHeight(110)
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0F1528, stop:1 #141C35);
                border: 1px solid {accent}44;
                border-radius: 12px;
            }}
        """)
        self.setGraphicsEffect(glow_shadow(accent, 14))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 12, 18, 12)
        layout.setSpacing(4)

        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.value_label.setStyleSheet(
            f"font-size: 38px; font-weight: bold; color: {accent}; letter-spacing: 2px;"
        )

        self.text_label = QLabel(label.upper())
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.text_label.setStyleSheet(
            f"font-size: 10px; color: {accent}88; letter-spacing: 3px; font-weight: bold;"
        )

        layout.addWidget(self.value_label)
        layout.addWidget(self.text_label)

    def set_value(self, val: str):
        self.value_label.setText(val)


class SectionTitle(QLabel):
    """Bold section heading with a coloured underline accent."""

    def __init__(self, text: str, accent: str = "#00C8FF", parent=None):
        super().__init__(text.upper(), parent)
        self.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {accent};
            letter-spacing: 3px;
            padding-bottom: 6px;
            border-bottom: 2px solid {accent}44;
        """)


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.HLine)
        self.setStyleSheet(f"color: {THEME['border']}; margin: 4px 0;")
