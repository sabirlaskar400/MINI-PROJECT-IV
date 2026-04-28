"""
ui/reports.py
-------------
Reports panel:
  - Table view of all tracking events
  - Live search / filter
  - Export to TXT or CSV
  - Reload from project_report.txt
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QLabel, QFileDialog,
    QMessageBox, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from .theme import THEME, NeonButton, SectionTitle
from core.data_manager import DataManager, TrackingRecord
from typing import List


class ReportsPanel(QWidget):
    def __init__(self, data_manager: DataManager, parent=None):
        super().__init__(parent)
        self.dm = data_manager
        self._all_records: List[TrackingRecord] = []
        self._build_ui()
        self._load_file()   # auto-load existing report on startup

    # ------------------------------------------------------------------ #
    #  Build UI                                                             #
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 28)
        root.setSpacing(16)

        root.addWidget(SectionTitle("Movement Report", THEME["accent_blue"]))

        # ── Toolbar ──────────────────────────────────────────────────── #
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍  Search by object, action, ID, time…")
        self.search_box.textChanged.connect(self._filter)
        self.search_box.setFixedHeight(38)
        toolbar.addWidget(self.search_box, stretch=1)

        btn_reload = NeonButton("↺  Reload File",    THEME["accent_blue"])
        btn_txt    = NeonButton("⬇  Export TXT",     THEME["accent_purple"])
        btn_csv    = NeonButton("⬇  Export CSV",     THEME["accent_green"])
        btn_clear  = NeonButton("🗑  Clear History",  THEME["accent_red"])

        btn_reload.clicked.connect(self._load_file)
        btn_txt.clicked.connect(self._export_txt)
        btn_csv.clicked.connect(self._export_csv)
        btn_clear.clicked.connect(self._clear_history)

        for btn in (btn_reload, btn_txt, btn_csv, btn_clear):
            toolbar.addWidget(btn)
        root.addLayout(toolbar)

        # ── Summary chips row ─────────────────────────────────────────── #
        self.chips_row = QHBoxLayout()
        self.chips_row.setSpacing(10)
        self._total_chip  = self._chip("TOTAL EVENTS", "0",  THEME["accent_blue"])
        self._in_chip     = self._chip("IN",            "0",  THEME["accent_green"])
        self._out_chip    = self._chip("OUT",           "0",  THEME["accent_red"])
        self._shown_chip  = self._chip("SHOWING",       "0",  THEME["accent_amber"])
        for c in (self._total_chip, self._in_chip, self._out_chip, self._shown_chip):
            self.chips_row.addWidget(c)
        self.chips_row.addStretch()
        root.addLayout(self.chips_row)

        # ── Table ─────────────────────────────────────────────────────── #
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["TIME", "OBJECT", "ID", "ACTION"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                font-size: 13px;
            }}
            QTableWidget::item:selected {{
                background: {THEME['bg_hover']};
                color: {THEME['text_primary']};
            }}
        """)
        root.addWidget(self.table)

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #
    def _chip(self, label: str, value: str, color: str) -> QFrame:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: {color}22;
                border: 1px solid {color}44;
                border-radius: 8px;
                padding: 2px 8px;
            }}
        """)
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 4, 10, 4)
        layout.setSpacing(6)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"font-size: 10px; color: {color}88; letter-spacing: 2px;")
        val = QLabel(value)
        val.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {color};")
        layout.addWidget(lbl)
        layout.addWidget(val)
        frame._val_label = val          # keep reference for updates
        return frame

    def _populate_table(self, records: List[TrackingRecord]):
        self.table.setRowCount(0)
        for rec in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            for col, text in enumerate([
                rec.timestamp, rec.obj_name, str(rec.obj_id), rec.action
            ]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # Colour-code the ACTION column
                if col == 3:
                    color = THEME["accent_green"] if text == "IN" else THEME["accent_red"]
                    item.setForeground(QColor(color))
                self.table.setItem(row, col, item)

        # Update shown chip
        self._shown_chip._val_label.setText(str(len(records)))

    # ------------------------------------------------------------------ #
    #  Slots                                                                #
    # ------------------------------------------------------------------ #
    def _load_file(self):
        """Reload from project_report.txt + merge with in-memory records."""
        file_records = self.dm.load_from_file()
        session_recs = self.dm.records
        # Merge: file first, then any session records not already in file
        seen = {(r.timestamp, r.obj_id) for r in file_records}
        merged = file_records + [r for r in session_recs
                                  if (r.timestamp, r.obj_id) not in seen]
        self._all_records = merged
        self._filter(self.search_box.text())
        self._update_chips()

    def _filter(self, query: str):
        q = query.strip().lower()
        if q:
            shown = [r for r in self._all_records if
                     q in r.timestamp.lower() or
                     q in r.obj_name.lower() or
                     q in str(r.obj_id) or
                     q in r.action.lower()]
        else:
            shown = self._all_records
        self._populate_table(shown)

    def _update_chips(self):
        total = len(self._all_records)
        in_c  = sum(1 for r in self._all_records if r.action == "IN")
        out_c = total - in_c
        self._total_chip._val_label.setText(str(total))
        self._in_chip._val_label.setText(str(in_c))
        self._out_chip._val_label.setText(str(out_c))

    def _export_txt(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export TXT Report", "report_export.txt", "Text Files (*.txt)"
        )
        if not path:
            return
        with open(path, "w") as f:
            f.write("TIME         | OBJECT       | ID   | ACTION\n")
            f.write("-" * 50 + "\n")
            for r in self._all_records:
                f.write(f"{r.timestamp:<14} {r.obj_name:<14} {r.obj_id:<6} {r.action}\n")
        QMessageBox.information(self, "Exported", f"Report saved to:\n{path}")

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV Report", "report_export.csv", "CSV Files (*.csv)"
        )
        if not path:
            return
        self.dm.export_csv(path)
        QMessageBox.information(self, "Exported", f"CSV saved to:\n{path}")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, "Clear History",
            "This will clear the in-memory session history.\n"
            "The project_report.txt file will NOT be deleted.\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.dm.clear()
            self._all_records = self.dm.load_from_file()
            self._filter("")
            self._update_chips()

    # ------------------------------------------------------------------ #
    #  Public API                                                           #
    # ------------------------------------------------------------------ #
    def add_record(self, rec: TrackingRecord):
        """Called live by the main window when a new event arrives."""
        self._all_records.append(rec)
        self._update_chips()
        self._filter(self.search_box.text())

    def refresh(self):
        self._load_file()
