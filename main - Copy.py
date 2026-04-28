"""
main.py
-------
Application entry point.
Builds the main window:
  - Left sidebar (navigation)
  - QStackedWidget (pages)
  - Status bar (camera / time / system status)
Wires signals between camera, analytics, reports, and data_manager.
"""

import sys
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QStatusBar,
    QMessageBox, QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QIcon, QFont

from ui.theme import THEME, DARK_STYLESHEET, LIGHT_STYLESHEET, NeonButton, glow_shadow
from ui.dashboard   import DashboardPanel
from ui.camera_view import CameraPanel
from ui.analytics   import AnalyticsPanel
from ui.reports     import ReportsPanel
from ui.settings    import SettingsPanel

from core.detector     import ObjectDetector
from core.tracker      import LineTracker
from core.data_manager import DataManager


# ─────────────────────────────────────────────────────────────────────────────
#  Sidebar button
# ─────────────────────────────────────────────────────────────────────────────

class SidebarButton(QPushButton):
    """Navigation button with icon emoji + text, active/inactive states."""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(f"  {icon}  {text}", parent)
        self._active = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(52)
        self.setCheckable(False)
        self._refresh()

    def set_active(self, active: bool):
        self._active = active
        self._refresh()

    def _refresh(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: {THEME['accent_blue']}22;
                    color: {THEME['accent_blue']};
                    border: none;
                    border-left: 3px solid {THEME['accent_blue']};
                    border-radius: 0px;
                    text-align: left;
                    padding: 0 16px;
                    font-size: 13px;
                    font-weight: bold;
                    letter-spacing: 1px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {THEME['text_secondary']};
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    text-align: left;
                    padding: 0 16px;
                    font-size: 13px;
                    letter-spacing: 1px;
                }}
                QPushButton:hover {{
                    background: {THEME['bg_hover']};
                    color: {THEME['text_primary']};
                }}
            """)


# ─────────────────────────────────────────────────────────────────────────────
#  Main Window
# ─────────────────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Object Analytics System")
        self.resize(1280, 800)
        self.setMinimumSize(1000, 650)

        # ── Core objects ───────────────────────────────────────────── #
        self.detector = ObjectDetector()
        self.tracker  = LineTracker()
        self.dm       = DataManager()

        self._dark_mode = True
        self._event_count = 0
        self._session_start = datetime.now()

        self._build_ui()
        self._apply_theme(dark=True)
        self._start_status_clock()

    # ------------------------------------------------------------------ #
    #  Build UI                                                             #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_main_area(), stretch=1)

        self._build_status_bar()

    # ── Sidebar ─────────────────────────────────────────────────────── #
    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {THEME['sidebar_bg']};
                border-right: 1px solid {THEME['border']};
            }}
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo header
        logo = QLabel("⬡  AI ANALYTICS")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setFixedHeight(70)
        logo.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {THEME['accent_blue']};
            letter-spacing: 2px;
            border-bottom: 1px solid {THEME['border']};
            padding: 0 16px;
        """)
        layout.addWidget(logo)

        # Nav items: (emoji, label, page index)
        self._nav_items = [
            ("⌂",  "Dashboard",    0),
            ("◉",  "Live Camera",  1),
            ("▦",  "Analytics",    2),
            ("≡",  "Reports",      3),
            ("⚙",  "Settings",     4),
        ]

        self._sidebar_btns = []
        for icon, label, idx in self._nav_items:
            btn = SidebarButton(icon, label)
            btn.clicked.connect(lambda _, i=idx: self._navigate(i))
            self._sidebar_btns.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom action buttons
        bottom = QFrame()
        bottom.setStyleSheet(f"border-top: 1px solid {THEME['border']};")
        bot_layout = QVBoxLayout(bottom)
        bot_layout.setContentsMargins(12, 10, 12, 10)
        bot_layout.setSpacing(8)

        btn_save  = NeonButton("💾  Save Session",  THEME["accent_green"])
        btn_exit  = NeonButton("✕  Exit",           THEME["accent_red"])
        btn_save.setFixedHeight(40)
        btn_exit.setFixedHeight(40)
        btn_save.clicked.connect(self._save_session)
        btn_exit.clicked.connect(self.close)

        bot_layout.addWidget(btn_save)
        bot_layout.addWidget(btn_exit)
        layout.addWidget(bottom)

        return sidebar

    # ── Main area ────────────────────────────────────────────────────── #
    def _build_main_area(self) -> QStackedWidget:
        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background: {THEME['bg_dark']};")

        # Page 0 – Dashboard
        self.dash = DashboardPanel()
        self.stack.addWidget(self.dash)

        # Page 1 – Camera
        self.cam_panel = CameraPanel(self.detector, self.tracker)
        self.cam_panel.new_events.connect(self._on_new_events)
        self.cam_panel.stats_update.connect(self._on_stats_update)
        self.stack.addWidget(self.cam_panel)

        # Page 2 – Analytics
        self.analytics = AnalyticsPanel()
        self.stack.addWidget(self.analytics)

        # Page 3 – Reports
        self.reports = ReportsPanel(self.dm)
        self.stack.addWidget(self.reports)

        # Page 4 – Settings
        self.settings_panel = SettingsPanel()
        self.settings_panel.theme_changed.connect(self._apply_theme)
        self.stack.addWidget(self.settings_panel)

        self._navigate(0)
        return self.stack

    # ── Status bar ───────────────────────────────────────────────────── #
    def _build_status_bar(self):
        sb = QStatusBar()
        sb.setStyleSheet(f"""
            QStatusBar {{
                background: {THEME['sidebar_bg']};
                border-top: 1px solid {THEME['border']};
                color: {THEME['text_secondary']};
                font-size: 11px;
                letter-spacing: 1px;
            }}
        """)
        self.setStatusBar(sb)

        self._status_cam  = self._status_pill("CAMERA: OFFLINE", THEME["text_muted"])
        self._status_sys  = self._status_pill("■ SYSTEM READY",  THEME["accent_green"])
        self._status_time = self._status_pill("00:00:00",         THEME["accent_blue"])
        self._status_events = self._status_pill("EVENTS: 0",      THEME["accent_purple"])

        for w in (self._status_cam, self._status_sys, self._status_events):
            sb.addWidget(w)
        sb.addPermanentWidget(self._status_time)

    def _status_pill(self, text: str, color: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {color}; font-size: 11px; letter-spacing: 1px; padding: 0 12px;"
        )
        return lbl

    # ------------------------------------------------------------------ #
    #  Navigation                                                           #
    # ------------------------------------------------------------------ #
    def _navigate(self, index: int):
        self.stack.setCurrentIndex(index)
        for i, btn in enumerate(self._sidebar_btns):
            btn.set_active(i == index)

        # Refresh reports when switching to that tab
        if index == 3:
            self.reports.refresh()

    # ------------------------------------------------------------------ #
    #  Event handlers                                                       #
    # ------------------------------------------------------------------ #
    def _on_new_events(self, events: list):
        """Called when camera worker detects line crossings."""
        for ev in events:
            rec = self.dm.add_event(ev.timestamp, ev.obj_name, ev.obj_id, ev.action)
            self.reports.add_record(rec)
            self._event_count += 1

        # Update analytics category chart
        self.analytics.update_categories(self.dm.category_counts())
        self._status_events.setText(f"EVENTS: {self._event_count}")

    def _on_stats_update(self, in_count: int, out_count: int):
        self.dash.update_stats(in_count, out_count)
        self.analytics.update_stats(in_count, out_count)

        # Update camera status pill
        self._status_cam.setText("CAMERA: LIVE")
        self._status_cam.setStyleSheet(
            f"color: {THEME['accent_green']}; font-size:11px; letter-spacing:1px; padding:0 12px;"
        )

        # Update rate (events per minute)
        elapsed = max(1, (datetime.now() - self._session_start).seconds)
        rate = round(self._event_count / elapsed * 60, 1)
        self.analytics.update_rate(f"{rate}/min")

    # ------------------------------------------------------------------ #
    #  Session controls                                                     #
    # ------------------------------------------------------------------ #
    def _save_session(self):
        self.dm.save_session(self.tracker.in_count, self.tracker.out_count)
        QMessageBox.information(
            self, "Saved",
            "Session saved to  project_report.txt\n\n"
            f"Total IN:  {self.tracker.in_count}\n"
            f"Total OUT: {self.tracker.out_count}",
        )
        self.reports.refresh()

    # ------------------------------------------------------------------ #
    #  Theme                                                                #
    # ------------------------------------------------------------------ #
    def _apply_theme(self, dark: bool):
        self._dark_mode = dark
        QApplication.instance().setStyleSheet(
            DARK_STYLESHEET if dark else LIGHT_STYLESHEET
        )

    # ------------------------------------------------------------------ #
    #  Status clock                                                         #
    # ------------------------------------------------------------------ #
    def _start_status_clock(self):
        def tick():
            self._status_time.setText(datetime.now().strftime("%H:%M:%S"))
        timer = QTimer(self)
        timer.timeout.connect(tick)
        timer.start(1000)
        tick()

    # ------------------------------------------------------------------ #
    #  Close event                                                          #
    # ------------------------------------------------------------------ #
    def closeEvent(self, event):
        self.cam_panel.stop_if_running()
        event.accept()


# ─────────────────────────────────────────────────────────────────────────────
#  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Consolas", 10))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
