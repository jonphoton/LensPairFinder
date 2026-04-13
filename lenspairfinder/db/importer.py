"""Import lens data from CSV or JSON files into the database."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.orm import Session

from lenspairfinder.db.schema import LensRow, ScrapeMetadata


# CSV columns expected (order matters for positional CSV, but we use DictReader)
EXPECTED_COLUMNS = {
    "vendor", "part_number", "description", "lens_type",
    "focal_length_mm", "diameter_mm",
}

OPTIONAL_COLUMNS = {
    "na", "coating_type", "wavelength_min_nm", "wavelength_max_nm",
    "center_wavelength_nm", "price_usd", "url", "back_focal_length_mm",
    "substrate_material", "is_positive",
}


def _parse_float(val: str | None) -> float | None:
    if val is None or val.strip() == "":
        return None
    return float(val)


def _parse_bool(val: str | None, default: bool = True) -> bool:
    if val is None or val.strip() == "":
        return default
    return val.strip().lower() in ("true", "1", "yes")


def _row_to_lens(row: dict) -> LensRow:
    """Convert a dict (from CSV or JSON) to a LensRow."""
    return LensRow(
        vendor=row["vendor"].strip(),
        part_number=row["part_number"].strip(),
        description=row.get("description", "").strip(),
        lens_type=row["lens_type"].strip(),
        focal_length_mm=float(row["focal_length_mm"]),
        diameter_mm=float(row["diameter_mm"]),
        na=_parse_float(row.get("na")),
        coating_type=row.get("coating_type", "").strip() or None,
        wavelength_min_nm=_parse_float(row.get("wavelength_min_nm")),
        wavelength_max_nm=_parse_float(row.get("wavelength_max_nm")),
        center_wavelength_nm=_parse_float(row.get("center_wavelength_nm")),
        price_usd=_parse_float(row.get("price_usd")),
        url=row.get("url", "").strip() or None,
        back_focal_length_mm=_parse_float(row.get("back_focal_length_mm")),
        substrate_material=row.get("substrate_material", "").strip() or None,
        is_positive=_parse_bool(row.get("is_positive"), default=True),
    )


def import_csv(session: Session, csv_path: Path | str) -> dict:
    """Import lenses from a CSV file. Upserts on (vendor, part_number).

    Returns dict with keys: inserted, updated, skipped, errors.
    """
    csv_path = Path(csv_path)
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = EXPECTED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            stats["errors"].append(f"Missing required columns: {missing}")
            return stats

        for i, row in enumerate(reader, start=2):  # line 2 = first data row
            try:
                _upsert_lens(session, row, stats)
            except Exception as e:
                stats["errors"].append(f"Row {i}: {e}")

    session.commit()
    _update_scrape_metadata(session, csv_path)
    return stats


def import_json(session: Session, json_path: Path | str) -> dict:
    """Import lenses from a JSON file (array of objects). Upserts."""
    json_path = Path(json_path)
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": []}

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        stats["errors"].append("JSON file must contain a top-level array")
        return stats

    for i, row in enumerate(data):
        try:
            _upsert_lens(session, row, stats)
        except Exception as e:
            stats["errors"].append(f"Item {i}: {e}")

    session.commit()
    _update_scrape_metadata(session, json_path)
    return stats


def _upsert_lens(session: Session, row: dict, stats: dict) -> None:
    """Insert or update a single lens record."""
    vendor = row["vendor"].strip()
    part_number = row["part_number"].strip()

    existing = (
        session.query(LensRow)
        .filter_by(vendor=vendor, part_number=part_number)
        .first()
    )

    if existing:
        # Update all fields
        new = _row_to_lens(row)
        for col in ("description", "lens_type", "focal_length_mm", "diameter_mm",
                     "na", "coating_type", "wavelength_min_nm", "wavelength_max_nm",
                     "center_wavelength_nm", "price_usd", "url",
                     "back_focal_length_mm", "substrate_material", "is_positive"):
            setattr(existing, col, getattr(new, col))
        existing.updated_at = datetime.now(timezone.utc)
        stats["updated"] += 1
    else:
        session.add(_row_to_lens(row))
        stats["inserted"] += 1


def _update_scrape_metadata(session: Session, source_path: Path) -> None:
    """Update scrape metadata for all vendors in the import."""
    from sqlalchemy import func

    vendors = session.query(LensRow.vendor).distinct().all()
    for (vendor,) in vendors:
        count = session.query(func.count(LensRow.id)).filter_by(vendor=vendor).scalar()
        meta = session.query(ScrapeMetadata).filter_by(vendor=vendor).first()
        if meta:
            meta.last_scraped_at = datetime.now(timezone.utc)
            meta.lens_count = count
            meta.source_description = f"Import from {source_path.name}"
        else:
            session.add(ScrapeMetadata(
                vendor=vendor,
                last_scraped_at=datetime.now(timezone.utc),
                lens_count=count,
                source_description=f"Import from {source_path.name}",
            ))
    session.commit()
