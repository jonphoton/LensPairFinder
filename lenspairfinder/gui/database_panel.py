"""Database management panel — shows vendor stats and import controls."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from sqlalchemy.orm import Session


class DatabasePanel(QWidget):
    """Tab showing database status and import controls."""

    import_csv_requested = pyqtSignal()
    import_json_requested = pyqtSignal()
    reload_seed_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QHBoxLayout(self)

        # --- Vendor table ---
        left = QVBoxLayout()
        vendor_group = QGroupBox("Lens Catalog Summary")
        vendor_layout = QVBoxLayout()

        self.vendor_table = QTableWidget()
        self.vendor_table.setColumnCount(4)
        self.vendor_table.setHorizontalHeaderLabels(
            ["Vendor", "Lens Count", "Last Updated", "Source"]
        )
        header = self.vendor_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.vendor_table.verticalHeader().setVisible(False)
        self.vendor_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        vendor_layout.addWidget(self.vendor_table)

        self.total_label = QLabel("Total lenses: 0")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        vendor_layout.addWidget(self.total_label)

        vendor_group.setLayout(vendor_layout)
        left.addWidget(vendor_group)
        layout.addLayout(left, stretch=3)

        # --- Actions ---
        right = QVBoxLayout()
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()

        self.import_csv_btn = QPushButton("Import CSV...")
        self.import_csv_btn.clicked.connect(self.import_csv_requested.emit)
        actions_layout.addWidget(self.import_csv_btn)

        self.import_json_btn = QPushButton("Import JSON...")
        self.import_json_btn.clicked.connect(self.import_json_requested.emit)
        actions_layout.addWidget(self.import_json_btn)

        self.seed_btn = QPushButton("Reload Seed Data")
        self.seed_btn.clicked.connect(self.reload_seed_requested.emit)
        actions_layout.addWidget(self.seed_btn)

        actions_layout.addStretch()

        note = QLabel(
            "Import CSV/JSON files matching the schema in\n"
            "seed_data/schema.md. See SCRAPING_GUIDE.md\n"
            "for instructions on building catalog files."
        )
        note.setWordWrap(True)
        note.setStyleSheet("color: gray; font-size: 11px;")
        actions_layout.addWidget(note)

        actions_group.setLayout(actions_layout)
        right.addWidget(actions_group)
        layout.addLayout(right, stretch=1)

    def refresh(self, session: Session):
        """Refresh the vendor table from the database."""
        from lenspairfinder.db.queries import get_vendor_summary, get_lens_count

        summaries = get_vendor_summary(session)
        total = get_lens_count(session)

        self.vendor_table.setRowCount(len(summaries))
        for i, s in enumerate(summaries):
            self.vendor_table.setItem(i, 0, QTableWidgetItem(s["vendor"]))
            self.vendor_table.setItem(i, 1, QTableWidgetItem(str(s["count"])))
            scraped = s["last_scraped"]
            date_str = scraped.strftime("%Y-%m-%d %H:%M") if scraped else "N/A"
            self.vendor_table.setItem(i, 2, QTableWidgetItem(date_str))
            self.vendor_table.setItem(i, 3, QTableWidgetItem(s["source"]))

        self.total_label.setText(f"Total lenses: {total}")
