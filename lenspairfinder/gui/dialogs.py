"""Dialogs for file import and about."""

from PyQt6.QtWidgets import QFileDialog, QMessageBox, QWidget


def choose_csv_file(parent: QWidget) -> str | None:
    path, _ = QFileDialog.getOpenFileName(
        parent, "Import CSV Lens Catalog", "",
        "CSV Files (*.csv);;All Files (*)"
    )
    return path or None


def choose_json_file(parent: QWidget) -> str | None:
    path, _ = QFileDialog.getOpenFileName(
        parent, "Import JSON Lens Catalog", "",
        "JSON Files (*.json);;All Files (*)"
    )
    return path or None


def show_import_result(parent: QWidget, stats: dict):
    msg = (
        f"Inserted: {stats['inserted']}\n"
        f"Updated: {stats['updated']}\n"
        f"Skipped: {stats['skipped']}"
    )
    if stats["errors"]:
        msg += f"\n\nErrors ({len(stats['errors'])}):\n"
        msg += "\n".join(stats["errors"][:10])
        if len(stats["errors"]) > 10:
            msg += f"\n... and {len(stats['errors']) - 10} more"

    QMessageBox.information(parent, "Import Complete", msg)


def show_about(parent: QWidget):
    QMessageBox.about(
        parent,
        "About LensPairFinder",
        "<b>LensPairFinder v0.1.0</b><br><br>"
        "Find commercial lens pairs for beam-expanding/reducing "
        "Keplerian telescopes.<br><br>"
        "Enter beam waists and wavelength to search for matching "
        "lens pairs from the local catalog database."
    )
