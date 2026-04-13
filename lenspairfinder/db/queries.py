"""Database query functions for the lens catalog."""

from sqlalchemy.orm import Session

from lenspairfinder.db.schema import LensRow, ScrapeMetadata


def get_wavelength_compatible_lenses(session: Session, wavelength_nm: float) -> list[LensRow]:
    """Get all positive lenses whose coating covers the given wavelength.

    Includes lenses with no wavelength data (assumed compatible / uncoated).
    Results sorted by focal_length_mm for efficient binary search downstream.
    """
    return (
        session.query(LensRow)
        .filter(LensRow.is_positive == True)  # noqa: E712
        .filter(
            # Coating covers wavelength, OR no wavelength data (uncoated/unknown)
            ((LensRow.wavelength_min_nm <= wavelength_nm) &
             (LensRow.wavelength_max_nm >= wavelength_nm))
            | (LensRow.wavelength_min_nm == None)  # noqa: E711
        )
        .order_by(LensRow.focal_length_mm)
        .all()
    )


def get_all_lenses(session: Session) -> list[LensRow]:
    """Get all lenses, sorted by vendor then part number."""
    return (
        session.query(LensRow)
        .order_by(LensRow.vendor, LensRow.part_number)
        .all()
    )


def get_lens_count(session: Session) -> int:
    """Total number of lenses in the database."""
    return session.query(LensRow).count()


def get_vendor_summary(session: Session) -> list[dict]:
    """Get per-vendor lens counts and scrape metadata."""
    from sqlalchemy import func

    vendor_counts = (
        session.query(LensRow.vendor, func.count(LensRow.id))
        .group_by(LensRow.vendor)
        .all()
    )

    result = []
    for vendor, count in vendor_counts:
        meta = session.query(ScrapeMetadata).filter_by(vendor=vendor).first()
        result.append({
            "vendor": vendor,
            "count": count,
            "last_scraped": meta.last_scraped_at if meta else None,
            "source": meta.source_description if meta else "unknown",
        })
    return result
