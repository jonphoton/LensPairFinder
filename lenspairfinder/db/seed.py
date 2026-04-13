"""Auto-load seed data on first run."""

from pathlib import Path

from sqlalchemy.orm import Session

from lenspairfinder.db.importer import import_csv
from lenspairfinder.db.queries import get_lens_count

SEED_DIR = Path(__file__).resolve().parent.parent.parent / "seed_data"


def seed_if_empty(session: Session) -> dict:
    """Load all seed CSVs if the database is empty.

    Returns summary dict with total inserted/updated or None if DB was not empty.
    """
    if get_lens_count(session) > 0:
        return None

    totals = {"inserted": 0, "updated": 0, "skipped": 0, "errors": [], "files": []}

    if not SEED_DIR.exists():
        totals["errors"].append(f"Seed directory not found: {SEED_DIR}")
        return totals

    for csv_file in sorted(SEED_DIR.glob("*.csv")):
        stats = import_csv(session, csv_file)
        totals["inserted"] += stats["inserted"]
        totals["updated"] += stats["updated"]
        totals["skipped"] += stats["skipped"]
        totals["errors"].extend(stats["errors"])
        totals["files"].append(csv_file.name)

    return totals
