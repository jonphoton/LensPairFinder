"""Main application window assembling all GUI panels."""

import time
from pathlib import Path

from PyQt6.QtWidgets import (
    QHBoxLayout, QMainWindow, QSplitter, QStatusBar,
    QTabWidget, QVBoxLayout, QWidget,
)
from PyQt6.QtCore import Qt

from lenspairfinder.core.models import SearchParams
from lenspairfinder.core.search import find_lens_pairs
from lenspairfinder.db.database import get_session
from lenspairfinder.db.importer import import_csv, import_json
from lenspairfinder.db.queries import get_lens_count
from lenspairfinder.db.seed import seed_if_empty
from lenspairfinder.gui.database_panel import DatabasePanel
from lenspairfinder.gui.detail_panel import DetailPanel
from lenspairfinder.gui.dialogs import (
    choose_csv_file, choose_json_file, show_about, show_import_result,
)
from lenspairfinder.gui.input_panel import InputPanel
from lenspairfinder.gui.results_table import ResultsTableView


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LensPairFinder")
        self.setMinimumSize(1100, 700)

        self.session = get_session()
        self._init_db()
        self._build_ui()
        self._build_menu()
        self._connect_signals()
        self._update_status()

    def _init_db(self):
        result = seed_if_empty(self.session)
        if result and result["inserted"] > 0:
            self._seed_msg = f"Loaded {result['inserted']} seed lenses from {len(result['files'])} files"
        else:
            self._seed_msg = None

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()

        # --- Search tab ---
        search_tab = QWidget()
        search_layout = QVBoxLayout(search_tab)

        top_splitter = QSplitter(Qt.Orientation.Horizontal)

        self.input_panel = InputPanel()
        self.input_panel.setMaximumWidth(320)
        self.input_panel.setMinimumWidth(260)
        top_splitter.addWidget(self.input_panel)

        self.results_table = ResultsTableView()
        top_splitter.addWidget(self.results_table)

        top_splitter.setStretchFactor(0, 0)
        top_splitter.setStretchFactor(1, 1)

        search_layout.addWidget(top_splitter, stretch=3)

        self.detail_panel = DetailPanel()
        self.detail_panel.setMaximumHeight(220)
        search_layout.addWidget(self.detail_panel, stretch=1)

        self.tabs.addTab(search_tab, "Search")

        # --- Database tab ---
        self.database_panel = DatabasePanel()
        self.tabs.addTab(self.database_panel, "Database")

        main_layout.addWidget(self.tabs)

        # --- Status bar ---
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    def _build_menu(self):
        menu = self.menuBar()
        file_menu = menu.addMenu("File")
        file_menu.addAction("Import CSV...", self._import_csv)
        file_menu.addAction("Import JSON...", self._import_json)
        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close)

        help_menu = menu.addMenu("Help")
        help_menu.addAction("About", lambda: show_about(self))

    def _connect_signals(self):
        self.input_panel.search_requested.connect(self._run_search)
        self.results_table.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        self.database_panel.import_csv_requested.connect(self._import_csv)
        self.database_panel.import_json_requested.connect(self._import_json)
        self.database_panel.reload_seed_requested.connect(self._reload_seed)
        self.tabs.currentChanged.connect(self._on_tab_changed)

    def _run_search(self, params: SearchParams):
        t0 = time.perf_counter()
        results = find_lens_pairs(params, self.session)
        elapsed = time.perf_counter() - t0

        self.results_table.set_results(results)
        self.detail_panel.update_pair(None)

        self.status_bar.showMessage(
            f"{len(results)} pairs found in {elapsed:.3f}s | "
            f"{get_lens_count(self.session)} lenses in database"
        )

    def _on_selection_changed(self):
        pair = self.results_table.get_selected_pair()
        self.detail_panel.update_pair(pair)

    def _import_csv(self):
        path = choose_csv_file(self)
        if path:
            stats = import_csv(self.session, Path(path))
            show_import_result(self, stats)
            self._update_status()

    def _import_json(self):
        path = choose_json_file(self)
        if path:
            stats = import_json(self.session, Path(path))
            show_import_result(self, stats)
            self._update_status()

    def _reload_seed(self):
        # Clear and reload
        from lenspairfinder.db.schema import LensRow, ScrapeMetadata
        self.session.query(LensRow).delete()
        self.session.query(ScrapeMetadata).delete()
        self.session.commit()
        result = seed_if_empty(self.session)
        if result:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self, "Seed Data",
                f"Loaded {result['inserted']} lenses from {len(result['files'])} files."
            )
        self._update_status()

    def _on_tab_changed(self, index: int):
        if index == 1:  # Database tab
            self.database_panel.refresh(self.session)

    def _update_status(self):
        count = get_lens_count(self.session)
        msg = f"{count} lenses in database"
        if self._seed_msg:
            msg = f"{self._seed_msg} | {msg}"
            self._seed_msg = None
        self.status_bar.showMessage(msg)
