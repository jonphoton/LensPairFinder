"""SQLAlchemy ORM models for the lens catalog database."""

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Index, Integer, String, Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class LensRow(Base):
    __tablename__ = "lenses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor = Column(String, nullable=False, index=True)
    part_number = Column(String, nullable=False)
    description = Column(Text, default="")
    lens_type = Column(String, nullable=False)  # aspheric, achromat_doublet, plano-convex, etc.
    focal_length_mm = Column(Float, nullable=False)
    diameter_mm = Column(Float, nullable=False)
    na = Column(Float, nullable=True)
    coating_type = Column(String, nullable=True)  # AR_BBAR, AR_V, uncoated, nanotexture
    wavelength_min_nm = Column(Float, nullable=True)
    wavelength_max_nm = Column(Float, nullable=True)
    center_wavelength_nm = Column(Float, nullable=True)
    price_usd = Column(Float, nullable=True)
    url = Column(Text, nullable=True)
    back_focal_length_mm = Column(Float, nullable=True)
    substrate_material = Column(String, nullable=True)
    is_positive = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("vendor", "part_number", name="uq_vendor_part"),
        Index("ix_focal_diameter", "focal_length_mm", "diameter_mm"),
        Index("ix_wavelength_range", "wavelength_min_nm", "wavelength_max_nm"),
    )

    def __repr__(self) -> str:
        return f"<Lens {self.vendor} {self.part_number} f={self.focal_length_mm}mm>"


class ScrapeMetadata(Base):
    __tablename__ = "scrape_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    vendor = Column(String, nullable=False, unique=True)
    last_scraped_at = Column(DateTime, nullable=True)
    lens_count = Column(Integer, default=0)
    source_description = Column(String, default="")

    def __repr__(self) -> str:
        return f"<ScrapeMetadata {self.vendor}: {self.lens_count} lenses>"
