"""
ui/analytics.py
---------------
Analytics panel:
  - Live IN/OUT line chart (scrolling 60-second window)
  - Category distribution bar chart
  - Animated counter widgets
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout,
)
from PyQt6.QtCore import Qt, QTimer
from collections import deque
from datetime import datetime
import matplotlib
matplotlib.use("QtAgg")
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from .theme import THEME, SectionTitle, StatCard


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────────────

BG  = THEME["bg_dark"]
BG2 = THEME["bg_card"]
ACC = THEME["accent_blue"]
GRN = THEME["accent_green"]
RED = THEME["accent_red"]
PUR = THEME["accent_purple"]
TXT = THEME["text_secondary"]

def _dark_fig(figsize=(6, 3)):
    fig = Figure(figsize=figsize, facecolor=BG2)
    ax  = fig.add_subplot(111, facecolor=BG)
    for spine in ax.spines.values():
        spine.set_color(THEME["border"])
    ax.tick_params(colors=TXT, labelsize=9)
    ax.xaxis.label.set_color(TXT)
    ax.yaxis.label.set_color(TXT)
    ax.grid(color=THEME["border"], linewidth=0.5, linestyle="--", alpha=0.5)
    fig.tight_layout(pad=1.5)
    return fig, ax


# ─────────────────────────────────────────────────────────────────────────────
#  Live Line Chart
# ─────────────────────────────────────────────────────────────────────────────

class LiveLineChart(FigureCanvas):
    """Scrolling line chart tracking IN and OUT counts over time."""

    WINDOW = 60   # keep last 60 data points

    def __init__(self, parent=None):
        self.fig, self.ax = _dark_fig((6, 3))
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet(f"background: {BG2}; border-radius: 10px;")

        self._times   = deque(maxlen=self.WINDOW)
        self._in_vals = deque(maxlen=self.WINDOW)
        self._out_vals= deque(maxlen=self.WINDOW)

        self._line_in,  = self.ax.plot([], [], color=GRN, linewidth=2, label="IN",  marker="o", markersize=3)
        self._line_out, = self.ax.plot([], [], color=RED,  linewidth=2, label="OUT", marker="o", markersize=3)

        legend = self.ax.legend(
            facecolor=BG2, edgecolor=THEME["border"],
            labelcolor=THEME["text_primary"], fontsize=9
        )
        self.ax.set_xlabel("Time", fontsize=9)
        self.ax.set_ylabel("Cumulative Count", fontsize=9)
        self.draw()

    def push(self, in_count: int, out_count: int):
        self._times.append(datetime.now().strftime("%H:%M:%S"))
        self._in_vals.append(in_count)
        self._out_vals.append(out_count)
        self._redraw()

    def _redraw(self):
        xs = list(range(len(self._times)))
        self._line_in.set_data(xs,  list(self._in_vals))
        self._line_out.set_data(xs, list(self._out_vals))

        if xs:
            self.ax.set_xlim(0, max(1, len(xs) - 1))
            all_vals = list(self._in_vals) + list(self._out_vals)
            self.ax.set_ylim(0, max(1, max(all_vals)) * 1.15)

            # Show only last few x-tick labels
            step = max(1, len(xs) // 5)
            ticks = xs[::step]
            labels = [self._times[i] for i in ticks]
            self.ax.set_xticks(ticks)
            self.ax.set_xticklabels(labels, rotation=25, fontsize=8)

        self.fig.tight_layout(pad=1.5)
        self.draw()


# ─────────────────────────────────────────────────────────────────────────────
#  Category Bar Chart
# ─────────────────────────────────────────────────────────────────────────────

class CategoryBarChart(FigureCanvas):
    """Horizontal bar chart showing event count per object class."""

    COLORS = ["#00C8FF", "#7B2FFF", "#00FF9C", "#FFB800", "#FF3D71"]

    def __init__(self, parent=None):
        self.fig, self.ax = _dark_fig((5, 3))
        super().__init__(self.fig)
        self.setParent(parent)
        self.setStyleSheet(f"background: {BG2}; border-radius: 10px;")
        self.ax.set_title("Events by Object Class", color=ACC, fontsize=11, pad=8)
        self.draw()

    def update_data(self, category_counts: dict):
        self.ax.clear()
        self.ax.set_facecolor(BG)
        for spine in self.ax.spines.values():
            spine.set_color(THEME["border"])
        self.ax.tick_params(colors=TXT, labelsize=9)
        self.ax.grid(color=THEME["border"], linewidth=0.5, linestyle="--", alpha=0.5, axis="x")

        if not category_counts:
            self.ax.text(0.5, 0.5, "No data yet", transform=self.ax.transAxes,
                         ha="center", va="center", color=TXT, fontsize=11)
        else:
            labels = list(category_counts.keys())
            values = list(category_counts.values())
            colors = [self.COLORS[i % len(self.COLORS)] for i in range(len(labels))]
            bars = self.ax.barh(labels, values, color=colors, height=0.55)
            for bar, val in zip(bars, values):
                self.ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                             str(val), va="center", color=THEME["text_primary"], fontsize=9)

        self.ax.set_title("Events by Object Class", color=ACC, fontsize=11, pad=8)
        self.fig.tight_layout(pad=1.5)
        self.draw()


# ─────────────────────────────────────────────────────────────────────────────
#  Analytics Panel
# ─────────────────────────────────────────────────────────────────────────────

class AnalyticsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._in_count  = 0
        self._out_count = 0
        self._build_ui()
        # Auto-refresh charts every 2 s (even with no new data)
        timer = QTimer(self)
        timer.timeout.connect(self._refresh)
        timer.start(2000)

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(20)

        root.addWidget(SectionTitle("Analytics", THEME["accent_blue"]))

        # ── Top stat cards ───────────────────────────────────────────── #
        top = QHBoxLayout()
        top.setSpacing(16)
        self.card_in   = StatCard("Total IN",     "0", THEME["accent_green"])
        self.card_out  = StatCard("Total OUT",    "0", THEME["accent_red"])
        self.card_rate = StatCard("Event Rate",   "0/min", THEME["accent_blue"])
        self.card_net  = StatCard("Net Present",  "0", THEME["accent_purple"])
        for c in (self.card_in, self.card_out, self.card_rate, self.card_net):
            top.addWidget(c)
        root.addLayout(top)

        # ── Charts row ───────────────────────────────────────────────── #
        charts = QHBoxLayout()
        charts.setSpacing(20)

        self.line_chart = LiveLineChart()
        self.bar_chart  = CategoryBarChart()

        charts.addWidget(self._chart_wrap(self.line_chart, "Live IN/OUT Timeline"), stretch=3)
        charts.addWidget(self._chart_wrap(self.bar_chart,  "Category Distribution"), stretch=2)
        root.addLayout(charts)

    def _chart_wrap(self, chart, title: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {THEME['bg_card']};
                border: 1px solid {THEME['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(0)
        layout.addWidget(chart)
        return frame

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #
    def update_stats(self, in_count: int, out_count: int):
        self._in_count  = in_count
        self._out_count = out_count
        self.card_in.set_value(str(in_count))
        self.card_out.set_value(str(out_count))
        net = max(0, in_count - out_count)
        self.card_net.set_value(str(net))
        self.line_chart.push(in_count, out_count)

    def update_categories(self, category_counts: dict):
        self.bar_chart.update_data(category_counts)

    def update_rate(self, rate: str):
        self.card_rate.set_value(rate)

    def _refresh(self):
        # push current values periodically so the line chart scrolls even at rest
        self.line_chart.push(self._in_count, self._out_count)
