"""Lens pair search algorithm.

Given beam waists w1, w2 and wavelength, find commercial lens pairs
that form a Keplerian telescope with magnification M = w2/w1.
"""

import bisect
import math

from sqlalchemy.orm import Session

from lenspairfinder.core.models import Lens, LensPair, SearchParams
from lenspairfinder.core.optics import (
    beam_radius_at_lens,
    is_lens_type_suitable,
    magnification,
    min_clear_aperture_m,
    mm_to_m,
    m_to_mm,
    nm_to_m,
    numerical_aperture,
    system_length_mm,
    um_to_m,
)
from lenspairfinder.db.queries import get_wavelength_compatible_lenses
from lenspairfinder.db.schema import LensRow


def _row_to_lens(row: LensRow) -> Lens:
    """Convert a SQLAlchemy LensRow to a Lens dataclass."""
    return Lens(
        id=row.id,
        vendor=row.vendor,
        part_number=row.part_number,
        description=row.description or "",
        lens_type=row.lens_type,
        focal_length_mm=row.focal_length_mm,
        diameter_mm=row.diameter_mm,
        na=row.na,
        coating_type=row.coating_type,
        wavelength_min_nm=row.wavelength_min_nm,
        wavelength_max_nm=row.wavelength_max_nm,
        center_wavelength_nm=row.center_wavelength_nm,
        price_usd=row.price_usd,
        url=row.url,
        back_focal_length_mm=row.back_focal_length_mm,
        substrate_material=row.substrate_material,
    )


def find_lens_pairs(params: SearchParams, session: Session) -> list[LensPair]:
    """Search for lens pairs matching the given beam telescope parameters.

    Returns a list of LensPair results sorted by score (best first).
    """
    # Derived quantities
    w1_m = um_to_m(params.w1_um)
    w2_m = um_to_m(params.w2_um)
    wavelength_m = nm_to_m(params.wavelength_nm)
    M = magnification(w1_m, w2_m)
    na1 = numerical_aperture(w1_m, wavelength_m)
    na2 = numerical_aperture(w2_m, wavelength_m)

    # Get wavelength-compatible lenses (already sorted by focal_length_mm)
    rows = get_wavelength_compatible_lenses(session, params.wavelength_nm)
    if not rows:
        return []

    # Build sorted focal length array for binary search
    focal_lengths = [r.focal_length_mm for r in rows]

    results: list[LensPair] = []

    for i, row1 in enumerate(rows):
        f1_mm = row1.focal_length_mm

        # Required f2 range
        f2_target = f1_mm * M
        f2_min = f2_target * (1 - params.m_tolerance)
        f2_max = f2_target * (1 + params.m_tolerance)

        # Binary search for candidates
        lo = bisect.bisect_left(focal_lengths, f2_min)
        hi = bisect.bisect_right(focal_lengths, f2_max)

        for j in range(lo, hi):
            if i == j:
                continue  # skip pairing a lens with itself

            row2 = rows[j]
            f2_mm = row2.focal_length_mm

            # Aperture check — side 1
            min_dia_1_m = min_clear_aperture_m(w1_m, mm_to_m(f1_mm), wavelength_m,
                                                params.aperture_safety)
            if row1.diameter_mm < m_to_mm(min_dia_1_m):
                continue

            # Aperture check — side 2
            min_dia_2_m = min_clear_aperture_m(w2_m, mm_to_m(f2_mm), wavelength_m,
                                                params.aperture_safety)
            if row2.diameter_mm < m_to_mm(min_dia_2_m):
                continue

            # Compute result details
            actual_M = f2_mm / f1_mm
            m_error = abs(actual_M - M) / M

            total_length = system_length_mm(f1_mm, f2_mm)

            price1 = row1.price_usd
            price2 = row2.price_usd
            if price1 is not None and price2 is not None:
                total_cost = price1 + price2
            else:
                total_cost = None

            # Lens type suitability
            suitable1 = is_lens_type_suitable(row1.lens_type, na1)
            suitable2 = is_lens_type_suitable(row2.lens_type, na2)
            type_penalty = (0 if suitable1 else 1) + (0 if suitable2 else 1)

            # Beam diameters at lenses (for display)
            beam_r1 = beam_radius_at_lens(w1_m, mm_to_m(f1_mm), wavelength_m)
            beam_r2 = beam_radius_at_lens(w2_m, mm_to_m(f2_mm), wavelength_m)

            # Composite score (lower is better)
            cost_for_score = total_cost if total_cost is not None else 500.0
            score = (
                10.0 * m_error
                + 0.001 * total_length
                + 0.002 * cost_for_score
                + 2.0 * type_penalty
            )

            results.append(LensPair(
                lens1=_row_to_lens(row1),
                lens2=_row_to_lens(row2),
                actual_magnification=actual_M,
                magnification_error=m_error,
                total_length_mm=total_length,
                total_cost_usd=total_cost,
                score=score,
                na_side1=na1,
                na_side2=na2,
                beam_dia_at_lens1_mm=m_to_mm(2.0 * beam_r1),
                beam_dia_at_lens2_mm=m_to_mm(2.0 * beam_r2),
                lens1_type_suitable=suitable1,
                lens2_type_suitable=suitable2,
            ))

    # Sort by score and truncate
    results.sort(key=lambda r: r.score)
    return results[:params.max_results]
