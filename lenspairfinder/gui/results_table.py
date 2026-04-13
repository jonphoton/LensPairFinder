"""Results table showing matched lens pairs."""

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtWidgets import QHeaderView, QTableView

from lenspairfinder.core.models import LensPair
from lenspairfinder.utils.formatting import format_price


COLUMNS = [
    ("#", 40),
    ("Lens 1", 180),
    ("Lens 2", 180),
    ("Type 1", 90),
    ("Type 2", 90),
    ("Actual M", 70),
    ("M Error", 65),
    ("Length (mm)", 85),
    ("Cost", 75),
    ("Score", 60),
]


class LensPairTableModel(QAbstractTableModel):
    """Table model backed by a list of LensPair results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results: list[LensPair] = []

    def set_results(self, results: list[LensPair]):
        self.beginResetModel()
        self._results = results
        self.endResetModel()

    def get_pair(self, row: int) -> LensPair | None:
        if 0 <= row < len(self._results):
            return self._results[row]
        return None

    def rowCount(self, parent=QModelIndex()):
        return len(self._results)

    def columnCount(self, parent=QModelIndex()):
        return len(COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return COLUMNS[section][0]
        return None

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        pair = self._results[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            match col:
                case 0:
                    return str(index.row() + 1)
                case 1:
                    return f"{pair.lens1.vendor} {pair.lens1.part_number}"
                case 2:
                    return f"{pair.lens2.vendor} {pair.lens2.part_number}"
                case 3:
                    return pair.lens1.lens_type.replace("_", " ")
                case 4:
                    return pair.lens2.lens_type.replace("_", " ")
                case 5:
                    return f"{pair.actual_magnification:.3f}"
                case 6:
                    return f"{pair.magnification_error * 100:.1f}%"
                case 7:
                    return f"{pair.total_length_mm:.0f}"
                case 8:
                    return format_price(pair.total_cost_usd)
                case 9:
                    return f"{pair.score:.3f}"
            return None

        if role == Qt.ItemDataRole.ToolTipRole:
            if col == 1:
                return pair.lens1.description
            if col == 2:
                return pair.lens2.description
            return None

        if role == Qt.ItemDataRole.ForegroundRole:
            from PyQt6.QtGui import QColor
            if col == 3 and not pair.lens1_type_suitable:
                return QColor(200, 100, 0)
            if col == 4 and not pair.lens2_type_suitable:
                return QColor(200, 100, 0)
            return None

        return None


class ResultsTableView(QTableView):
    """Pre-configured table view for lens pair results."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model_instance = LensPairTableModel(self)
        self.setModel(self.model_instance)

        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(False)
        self.verticalHeader().setVisible(False)

        header = self.horizontalHeader()
        for i, (_, width) in enumerate(COLUMNS):
            header.resizeSection(i, width)
        header.setStretchLastSection(True)

    def set_results(self, results: list[LensPair]):
        self.model_instance.set_results(results)

    def get_selected_pair(self) -> LensPair | None:
        indexes = self.selectionModel().selectedRows()
        if indexes:
            return self.model_instance.get_pair(indexes[0].row())
        return None
