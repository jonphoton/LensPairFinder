"""Input panel for beam waist, wavelength, and search parameters."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QPushButton, QVBoxLayout, QWidget,
)

from lenspairfinder.core.models import SearchParams
from lenspairfinder.core.optics import (
    magnification, numerical_aperture, um_to_m, nm_to_m,
)
from lenspairfinder.utils.constants import NA_ASPHERIC_THRESHOLD
from lenspairfinder.utils.formatting import format_na


class InputPanel(QWidget):
    """Left panel with beam parameters and search button."""

    search_requested = pyqtSignal(SearchParams)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._connect_signals()
        self._update_computed()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # --- Input parameters ---
        input_group = QGroupBox("Telescope Parameters")
        form = QFormLayout()

        self.w1_spin = QDoubleSpinBox()
        self.w1_spin.setRange(0.1, 100000.0)
        self.w1_spin.setDecimals(1)
        self.w1_spin.setValue(50.0)
        self.w1_spin.setSuffix(" \u00b5m")
        form.addRow("Beam waist w\u2081:", self.w1_spin)

        self.w2_spin = QDoubleSpinBox()
        self.w2_spin.setRange(0.1, 100000.0)
        self.w2_spin.setDecimals(1)
        self.w2_spin.setValue(500.0)
        self.w2_spin.setSuffix(" \u00b5m")
        form.addRow("Beam waist w\u2082:", self.w2_spin)

        self.wavelength_spin = QDoubleSpinBox()
        self.wavelength_spin.setRange(200.0, 20000.0)
        self.wavelength_spin.setDecimals(1)
        self.wavelength_spin.setValue(633.0)
        self.wavelength_spin.setSuffix(" nm")
        form.addRow("Wavelength \u03bb:", self.wavelength_spin)

        self.tolerance_spin = QDoubleSpinBox()
        self.tolerance_spin.setRange(0.1, 50.0)
        self.tolerance_spin.setDecimals(1)
        self.tolerance_spin.setValue(5.0)
        self.tolerance_spin.setSuffix(" %")
        form.addRow("M tolerance:", self.tolerance_spin)

        self.safety_spin = QDoubleSpinBox()
        self.safety_spin.setRange(1.0, 10.0)
        self.safety_spin.setDecimals(1)
        self.safety_spin.setValue(3.0)
        self.safety_spin.setSuffix("x")
        form.addRow("Aperture safety:", self.safety_spin)

        input_group.setLayout(form)
        layout.addWidget(input_group)

        # --- Computed values ---
        computed_group = QGroupBox("Computed Values")
        comp_layout = QFormLayout()

        self.mag_label = QLabel()
        comp_layout.addRow("Target M:", self.mag_label)

        self.na1_label = QLabel()
        comp_layout.addRow("NA (side 1):", self.na1_label)

        self.na2_label = QLabel()
        comp_layout.addRow("NA (side 2):", self.na2_label)

        self.recommendation_label = QLabel()
        self.recommendation_label.setWordWrap(True)
        self.recommendation_label.setStyleSheet("color: #cc6600; font-weight: bold;")
        comp_layout.addRow("", self.recommendation_label)

        computed_group.setLayout(comp_layout)
        layout.addWidget(computed_group)

        # --- Search button ---
        btn_layout = QHBoxLayout()
        self.search_btn = QPushButton("Search")
        self.search_btn.setMinimumHeight(36)
        self.search_btn.setStyleSheet("font-weight: bold; font-size: 14px;")
        btn_layout.addWidget(self.search_btn)
        layout.addLayout(btn_layout)

        layout.addStretch()

    def _connect_signals(self):
        self.w1_spin.valueChanged.connect(self._update_computed)
        self.w2_spin.valueChanged.connect(self._update_computed)
        self.wavelength_spin.valueChanged.connect(self._update_computed)
        self.search_btn.clicked.connect(self._on_search)

    def _update_computed(self):
        w1_m = um_to_m(self.w1_spin.value())
        w2_m = um_to_m(self.w2_spin.value())
        lam_m = nm_to_m(self.wavelength_spin.value())

        M = magnification(w1_m, w2_m)
        na1 = numerical_aperture(w1_m, lam_m)
        na2 = numerical_aperture(w2_m, lam_m)

        self.mag_label.setText(f"{M:.3f}")
        self.na1_label.setText(format_na(na1))
        self.na2_label.setText(format_na(na2))

        notes = []
        if na1 > NA_ASPHERIC_THRESHOLD:
            notes.append("Side 1: high NA \u2014 asphere or doublet recommended")
        if na2 > NA_ASPHERIC_THRESHOLD:
            notes.append("Side 2: high NA \u2014 asphere or doublet recommended")
        self.recommendation_label.setText("\n".join(notes))

    def _on_search(self):
        params = SearchParams(
            w1_um=self.w1_spin.value(),
            w2_um=self.w2_spin.value(),
            wavelength_nm=self.wavelength_spin.value(),
            m_tolerance=self.tolerance_spin.value() / 100.0,
            aperture_safety=self.safety_spin.value(),
        )
        self.search_requested.emit(params)
