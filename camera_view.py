"""
ui/camera_view.py
-----------------
Live camera panel with:
  - Real webcam mode (CameraWorker)
  - Demo mode (DemoWorker) – runs without any camera using a synthetic feed
  - Loading overlay while model downloads
  - Graceful error handling
"""

import cv2
import numpy as np
import random
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap

from .theme import THEME, NeonButton, StatCard, SectionTitle, glow_shadow
from core.detector import ObjectDetector
from core.tracker import LineTracker, CrossingEvent
from typing import List


# ─────────────────────────────────────────────────────────────────────────────
#  Real Camera Worker
# ─────────────────────────────────────────────────────────────────────────────

class CameraWorker(QThread):
    """Reads frames from a real webcam, runs YOLOv8 tracking."""
    frame_ready  = pyqtSignal(np.ndarray)
    events_ready = pyqtSignal(list)
    stats_ready  = pyqtSignal(int, int)
    error        = pyqtSignal(str)

    def __init__(self, detector: ObjectDetector, tracker: LineTracker, cam_index: int = 0):
        super().__init__()
        self.detector  = detector
        self.tracker   = tracker
        self.cam_index = cam_index
        self._running  = False

    def run(self):
        cap = cv2.VideoCapture(self.cam_index)
        if not cap.isOpened():
            cap.release()
            cap = cv2.VideoCapture(self.cam_index + 1)

        if not cap.isOpened():
            self.error.emit(
                "No webcam detected.\n\n"
                "Tip: Press  DEMO MODE  to run the dashboard without a camera."
            )
            return

        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.tracker.resize(w, h)

        self._running = True
        while self._running:
            ret, frame = cap.read()
            if not ret:
                self.error.emit("Lost camera feed.")
                break

            detections = self.detector.detect(frame)
            events, annotated = self.tracker.process(frame, detections, self.detector)

            self.frame_ready.emit(annotated)
            if events:
                self.events_ready.emit(events)
            self.stats_ready.emit(self.tracker.in_count, self.tracker.out_count)

        cap.release()

    def stop(self):
        self._running = False
        self.wait()


# ─────────────────────────────────────────────────────────────────────────────
#  Demo Worker  (no camera or YOLO required)
# ─────────────────────────────────────────────────────────────────────────────

class DemoWorker(QThread):
    """
    Generates a synthetic animated frame and fake crossing events.
    Three coloured blobs move around and cross the counting line.
    """
    frame_ready  = pyqtSignal(np.ndarray)
    events_ready = pyqtSignal(list)
    stats_ready  = pyqtSignal(int, int)

    _OBJECTS = [
        ("bottle",     (60,  200,  60)),
        ("cell phone", (60,  180, 240)),
        ("scissors",   (180,  60, 240)),
    ]

    def __init__(self):
        super().__init__()
        self._running   = False
        self._in_count  = 0
        self._out_count = 0
        self._blobs = []
        for i, (name, color) in enumerate(self._OBJECTS):
            self._blobs.append({
                "id": i + 1,
                "name": name,
                "color": color,
                "x": random.randint(80, 560),
                "y": random.randint(50, 200),
                "vx": random.choice([-3, 3]),
                "vy": random.choice([2, 3]),
                "below": False,   # was blob below line last frame?
            })

    def run(self):
        W, H   = 640, 480
        line_y = H // 2
        self._running = True

        while self._running:
            # Dark background
            frame = np.zeros((H, W, 3), dtype=np.uint8)
            frame[:] = (20, 28, 50)

            # Grid
            for x in range(0, W, 80):
                cv2.line(frame, (x, 0), (x, H), (30, 42, 75), 1)
            for y in range(0, H, 60):
                cv2.line(frame, (0, y), (W, y), (30, 42, 75), 1)

            # Counting line
            cv2.line(frame, (0, line_y), (W, line_y), (0, 200, 255), 2)
            cv2.putText(frame, "COUNTING LINE",
                        (W // 2 - 72, line_y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 200, 255), 1)

            # Dashboard bar
            cv2.rectangle(frame, (0, 0), (W, 36), (10, 16, 32), -1)
            cv2.putText(frame,
                        f"DEMO MODE  |  IN: {self._in_count}  OUT: {self._out_count}",
                        (12, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.52,
                        (0, 200, 255), 1)

            events: List[CrossingEvent] = []
            now = datetime.now().strftime("%H:%M:%S")

            for blob in self._blobs:
                # Move
                blob["x"] = int(blob["x"] + blob["vx"])
                blob["y"] = int(blob["y"] + blob["vy"])

                # Bounce off walls
                if blob["x"] < 30 or blob["x"] > W - 30:
                    blob["vx"] *= -1
                if blob["y"] < 44 or blob["y"] > H - 30:
                    blob["vy"] *= -1

                bx, by = blob["x"], blob["y"]
                now_below = by >= line_y

                # Detect crossing
                if now_below and not blob["below"]:
                    blob["below"] = True
                    self._in_count += 1
                    events.append(CrossingEvent(now, blob["name"], blob["id"], "IN"))
                elif not now_below and blob["below"]:
                    blob["below"] = False
                    self._out_count += 1
                    events.append(CrossingEvent(now, blob["name"], blob["id"], "OUT"))

                # Draw box + label
                cv2.rectangle(frame,
                              (bx - 32, by - 44), (bx + 32, by + 14),
                              blob["color"], 2)
                cv2.putText(frame,
                            f"{blob['name']} #{blob['id']}",
                            (bx - 30, by - 48),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.36,
                            blob["color"], 1)

            self.frame_ready.emit(frame)
            if events:
                self.events_ready.emit(events)
            self.stats_ready.emit(self._in_count, self._out_count)
            self.msleep(33)   # ~30 fps

    def stop(self):
        self._running = False
        self.wait()


# ─────────────────────────────────────────────────────────────────────────────
#  Loading Overlay
# ─────────────────────────────────────────────────────────────────────────────

class LoadingOverlay(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_dark']}DD;
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(16)

        self._spinner = QLabel("⚙")
        self._spinner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._spinner.setStyleSheet(f"font-size: 48px; color: {THEME['accent_blue']};")

        self._msg_label = QLabel("Loading YOLOv8 Model…")
        self._msg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._msg_label.setStyleSheet(
            f"font-size: 14px; color: {THEME['text_secondary']}; letter-spacing: 2px;"
        )

        bar = QProgressBar()
        bar.setRange(0, 0)
        bar.setFixedWidth(260)
        bar.setFixedHeight(6)
        bar.setTextVisible(False)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {THEME['border']};
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background: {THEME['accent_blue']};
                border-radius: 3px;
            }}
        """)

        self._spin_frames = ["⚙", "◈", "◉", "◎"]
        self._idx = 0
        timer = QTimer(self)
        timer.timeout.connect(self._spin)
        timer.start(200)

        layout.addWidget(self._spinner)
        layout.addWidget(self._msg_label)
        layout.addWidget(bar, alignment=Qt.AlignmentFlag.AlignCenter)

    def set_message(self, text: str):
        self._msg_label.setText(text)

    def _spin(self):
        self._idx = (self._idx + 1) % len(self._spin_frames)
        self._spinner.setText(self._spin_frames[self._idx])


# ─────────────────────────────────────────────────────────────────────────────
#  Camera Panel
# ─────────────────────────────────────────────────────────────────────────────

class CameraPanel(QWidget):
    new_events   = pyqtSignal(list)
    stats_update = pyqtSignal(int, int)

    def __init__(self, detector: ObjectDetector, tracker: LineTracker, parent=None):
        super().__init__(parent)
        self.detector = detector
        self.tracker  = tracker
        self._worker  = None
        self._build_ui()

    # ------------------------------------------------------------------ #
    #  Build UI                                                             #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        root.addWidget(SectionTitle("Live Camera Feed", THEME["accent_blue"]))

        # ── Controls row ─────────────────────────────────────────────── #
        ctrl = QHBoxLayout()
        ctrl.setSpacing(10)

        self.btn_start = NeonButton("▶  START CAMERA", THEME["accent_green"])
        self.btn_demo  = NeonButton("⬡  DEMO MODE",    THEME["accent_blue"])
        self.btn_stop  = NeonButton("■  STOP",         THEME["accent_red"])
        self.btn_stop.setEnabled(False)

        self.btn_start.clicked.connect(self._start_real)
        self.btn_demo.clicked.connect(self._start_demo)
        self.btn_stop.clicked.connect(self._stop)

        ctrl.addWidget(self.btn_start)
        ctrl.addWidget(self.btn_demo)
        ctrl.addWidget(self.btn_stop)
        ctrl.addStretch()

        self.status_dot = QLabel("●  IDLE")
        self.status_dot.setStyleSheet(
            f"font-size: 12px; color: {THEME['text_secondary']}; letter-spacing: 2px;"
        )
        ctrl.addWidget(self.status_dot)
        root.addLayout(ctrl)

        # ── Info banner ───────────────────────────────────────────────── #
        self.info_banner = QLabel(
            "  ⬡  No webcam?  Click  DEMO MODE  to run the full dashboard with a simulated feed.  "
        )
        self.info_banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info_banner.setStyleSheet(f"""
            background: {THEME['accent_blue']}14;
            border: 1px solid {THEME['accent_blue']}44;
            border-radius: 8px;
            color: {THEME['accent_blue']};
            font-size: 12px;
            letter-spacing: 1px;
            padding: 8px;
        """)
        root.addWidget(self.info_banner)

        # ── Main content ─────────────────────────────────────────────── #
        content = QHBoxLayout()
        content.setSpacing(20)

        # Video frame
        self._vframe = QFrame()
        self._vframe.setStyleSheet(f"""
            QFrame {{
                background: #000;
                border: 2px solid {THEME['border']};
                border-radius: 12px;
            }}
        """)
        self._vframe.setGraphicsEffect(glow_shadow(THEME["accent_blue"], 20))
        vlay = QVBoxLayout(self._vframe)
        vlay.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel(
            "Camera offline\n\nPress  ▶ START CAMERA  or  ⬡ DEMO MODE"
        )
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet(
            f"color: {THEME['text_muted']}; font-size: 13px; letter-spacing: 1px;"
        )
        self.video_label.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self.video_label.setMinimumSize(480, 340)
        vlay.addWidget(self.video_label)
        content.addWidget(self._vframe, stretch=3)

        # Side panel
        side = QVBoxLayout()
        side.setSpacing(14)
        side.addWidget(SectionTitle("Session Stats", THEME["accent_purple"]))
        self.card_in  = StatCard("Objects IN",  "0", THEME["accent_green"])
        self.card_out = StatCard("Objects OUT", "0", THEME["accent_red"])
        side.addWidget(self.card_in)
        side.addWidget(self.card_out)

        side.addWidget(SectionTitle("Last Event", THEME["accent_amber"]))
        self.last_event = QLabel("—")
        self.last_event.setWordWrap(True)
        self.last_event.setStyleSheet(
            f"font-size: 12px; color: {THEME['text_secondary']}; "
            f"background: {THEME['bg_card']}; border: 1px solid {THEME['border']}; "
            f"border-radius: 8px; padding: 12px;"
        )
        side.addWidget(self.last_event)
        side.addStretch()
        content.addLayout(side, stretch=1)
        root.addLayout(content, stretch=1)

        # Loading overlay
        self._overlay = LoadingOverlay(self._vframe)
        self._overlay.hide()
        self._overlay.resize(self._vframe.size())

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, '_overlay') and self._overlay.parent():
            self._overlay.resize(self._overlay.parent().size())

    # ------------------------------------------------------------------ #
    #  Camera Lifecycle                                                     #
    # ------------------------------------------------------------------ #
    def _start_real(self):
        self._set_btns(False, False, False)
        self._set_status("LOADING MODEL…", THEME["accent_amber"])
        self._overlay.set_message("Downloading / Loading YOLOv8 Model…")
        self._overlay.show()

        loader = _ModelLoader(self.detector)
        loader.finished.connect(self._on_model_ready)
        loader.failed.connect(self._on_model_failed)
        loader.start()
        self._loader = loader   # keep alive

    def _start_demo(self):
        """Start synthetic demo – no model or camera needed."""
        self._stop_worker()
        worker = DemoWorker()
        worker.frame_ready.connect(self._update_frame)
        worker.events_ready.connect(self._handle_events)
        worker.stats_ready.connect(self._update_stats)
        worker.start()
        self._worker = worker
        self.info_banner.hide()
        self._set_btns(False, False, True)
        self._set_status("● DEMO LIVE", THEME["accent_blue"])

    def _on_model_ready(self):
        self._overlay.hide()
        worker = CameraWorker(self.detector, self.tracker)
        worker.frame_ready.connect(self._update_frame)
        worker.events_ready.connect(self._handle_events)
        worker.stats_ready.connect(self._update_stats)
        worker.error.connect(self._on_cam_error)
        worker.start()
        self._worker = worker
        self.info_banner.hide()
        self._set_btns(False, False, True)
        self._set_status("● LIVE", THEME["accent_green"])

    def _on_model_failed(self, msg: str):
        self._overlay.hide()
        self._set_btns(True, True, False)
        self._set_status("MODEL ERROR", THEME["accent_red"])
        self.video_label.setText(f"⚠  {msg}")

    def _on_cam_error(self, msg: str):
        self._stop_worker()
        self._set_btns(True, True, False)
        self._set_status("NO CAMERA", THEME["accent_red"])
        self.video_label.setText(
            "⚠  Camera not detected.\n\nPress  ⬡ DEMO MODE  to run without a webcam."
        )
        self.info_banner.show()

    def _stop(self):
        self._stop_worker()
        self.video_label.setText(
            "Camera offline\n\nPress  ▶ START CAMERA  or  ⬡ DEMO MODE"
        )
        self._set_btns(True, True, False)
        self._set_status("STOPPED", THEME["text_secondary"])

    def _stop_worker(self):
        if self._worker:
            self._worker.stop()
            self._worker = None

    # ------------------------------------------------------------------ #
    #  Slots                                                                #
    # ------------------------------------------------------------------ #
    @pyqtSlot(np.ndarray)
    def _update_frame(self, frame: np.ndarray):
        rgb  = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img  = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix  = QPixmap.fromImage(img).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(pix)

    @pyqtSlot(list)
    def _handle_events(self, events: list):
        self.new_events.emit(events)
        last  = events[-1]
        color = THEME["accent_green"] if last.action == "IN" else THEME["accent_red"]
        self.last_event.setText(
            f"<span style='color:{color}'>{last.action}</span>  "
            f"{last.obj_name}  #<b>{last.obj_id}</b><br>"
            f"<span style='color:{THEME['text_secondary']}'>{last.timestamp}</span>"
        )

    @pyqtSlot(int, int)
    def _update_stats(self, in_count: int, out_count: int):
        self.card_in.set_value(str(in_count))
        self.card_out.set_value(str(out_count))
        self.stats_update.emit(in_count, out_count)

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #
    def _set_btns(self, start: bool, demo: bool, stop: bool):
        self.btn_start.setEnabled(start)
        self.btn_demo.setEnabled(demo)
        self.btn_stop.setEnabled(stop)

    def _set_status(self, text: str, color: str):
        self.status_dot.setText(f"●  {text}")
        self.status_dot.setStyleSheet(
            f"font-size: 12px; color: {color}; letter-spacing: 2px;"
        )

    def stop_if_running(self):
        self._stop_worker()


# ─────────────────────────────────────────────────────────────────────────────
#  Model Loader Thread
# ─────────────────────────────────────────────────────────────────────────────

class _ModelLoader(QThread):
    finished = pyqtSignal()
    failed   = pyqtSignal(str)

    def __init__(self, detector: ObjectDetector):
        super().__init__()
        self.detector = detector

    def run(self):
        if self.detector.is_loaded or self.detector.load():
            self.finished.emit()
        else:
            self.failed.emit(
                "YOLOv8 model failed to load.\n"
                "Check your internet connection for the first-time download.\n\n"
                "You can still use  DEMO MODE  without the model."
            )
