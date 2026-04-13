"""Detail panel showing full info for a selected lens pair."""

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget,
)

from lenspairfinder.core.models import LensPair
from lenspairfinder.utils.formatting import (
    format_beam_diameter, format_focal_length, format_na, format_price,
)


class DetailPanel(QWidget):
    """Bottom panel with detail on the selected lens pair."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_pair: LensPair | None = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.group = QGroupBox("Selected Pair")
        inner = QVBoxLayout()

        self.info_label = QLabel("Select a result row to see details.")
        self.info_label.setWordWrap(True)
        inner.addWidget(self.info_label)

        btn_layout = QHBoxLayout()
        self.url1_btn = QPushButton("Open Lens 1 Page")
        self.url1_btn.clicked.connect(self._open_url1)
        self.url1_btn.setEnabled(False)
        btn_layout.addWidget(self.url1_btn)

        self.url2_btn = QPushButton("Open Lens 2 Page")
        self.url2_btn.clicked.connect(self._open_url2)
        self.url2_btn.setEnabled(False)
        btn_layout.addWidget(self.url2_btn)

        btn_layout.addStretch()
        inner.addLayout(btn_layout)

        self.group.setLayout(inner)
        layout.addWidget(self.group)

    def update_pair(self, pair: LensPair | None):
        self._current_pair = pair

        if pair is None:
            self.info_label.setText("Select a result row to see details.")
            self.url1_btn.setEnabled(False)
            self.url2_btn.setEnabled(False)
            return

        L1 = pair.lens1
        L2 = pair.lens2

        lines = [
            f"<b>Lens 1:</b> {L1.vendor} {L1.part_number} &mdash; "
            f"{L1.description}",
            f"&nbsp;&nbsp;f = {format_focal_length(L1.focal_length_mm)}, "
            f"dia = {L1.diameter_mm:.1f} mm, "
            f"type = {L1.lens_type.replace('_', ' ')}, "
            f"coating = {L1.coating_type or 'N/A'}, "
            f"price = {format_price(L1.price_usd)}",
            "",
            f"<b>Lens 2:</b> {L2.vendor} {L2.part_number} &mdash; "
            f"{L2.description}",
            f"&nbsp;&nbsp;f = {format_focal_length(L2.focal_length_mm)}, "
            f"dia = {L2.diameter_mm:.1f} mm, "
            f"type = {L2.lens_type.replace('_', ' ')}, "
            f"coating = {L2.coating_type or 'N/A'}, "
            f"price = {format_price(L2.price_usd)}",
            "",
            f"<b>System:</b> "
            f"M = {pair.actual_magnification:.3f} "
            f"(error {pair.magnification_error * 100:.1f}%), "
            f"total length = {pair.total_length_mm:.0f} mm, "
            f"total cost = {format_price(pair.total_cost_usd)}",
            f"&nbsp;&nbsp;NA side 1 = {format_na(pair.na_side1)}, "
            f"beam dia at L1 = {format_beam_diameter(pair.beam_dia_at_lens1_mm)}"
            f"{'' if pair.lens1_type_suitable else ' (lens type may limit performance)'}",
            f"&nbsp;&nbsp;NA side 2 = {format_na(pair.na_side2)}, "
            f"beam dia at L2 = {format_beam_diameter(pair.beam_dia_at_lens2_mm)}"
            f"{'' if pair.lens2_type_suitable else ' (lens type may limit performance)'}",
        ]
        self.info_label.setText("<br>".join(lines))

        self.url1_btn.setEnabled(bool(L1.url))
        self.url2_btn.setEnabled(bool(L2.url))

    def _open_url1(self):
        if self._current_pair and self._current_pair.lens1.url:
            QDesktopServices.openUrl(QUrl(self._current_pair.lens1.url))

    def _open_url2(self):
        if self._current_pair and self._current_pair.lens2.url:
            QDesktopServices.openUrl(QUrl(self._current_pair.lens2.url))
