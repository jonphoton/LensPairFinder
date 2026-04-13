"""Dataclasses for search parameters and results."""

from __future__ import annotations

from dataclasses import dataclass, field

from lenspairfinder.utils.constants import (
    APERTURE_SAFETY_FACTOR,
    DEFAULT_M_TOLERANCE,
    DEFAULT_MAX_RESULTS,
)


@dataclass
class Lens:
    """A single commercial lens from the database."""
    id: int
    vendor: str
    part_number: str
    description: str
    lens_type: str
    focal_length_mm: float
    diameter_mm: float
    na: float | None
    coating_type: str | None
    wavelength_min_nm: float | None
    wavelength_max_nm: float | None
    center_wavelength_nm: float | None
    price_usd: float | None
    url: str | None
    back_focal_length_mm: float | None
    substrate_material: str | None


@dataclass
class SearchParams:
    """Input parameters for a lens pair search."""
    w1_um: float          # beam waist 1 in micrometers
    w2_um: float          # beam waist 2 in micrometers
    wavelength_nm: float  # operating wavelength in nanometers
    m_tolerance: float = DEFAULT_M_TOLERANCE
    aperture_safety: float = APERTURE_SAFETY_FACTOR
    max_results: int = DEFAULT_MAX_RESULTS


@dataclass
class LensPair:
    """A candidate lens pair result from the search."""
    lens1: Lens
    lens2: Lens
    actual_magnification: float
    magnification_error: float  # fractional |M_actual - M_target| / M_target
    total_length_mm: float
    total_cost_usd: float | None
    score: float
    na_side1: float
    na_side2: float
    beam_dia_at_lens1_mm: float
    beam_dia_at_lens2_mm: float
    lens1_type_suitable: bool
    lens2_type_suitable: bool
