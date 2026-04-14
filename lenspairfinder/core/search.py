"""Lens pair search algorithm.

Given beam waists w1, w2 and wavelength, find commercial lens pairs
that form a Keplerian or Galilean telescope with magnification M = w2/w1.

Keplerian: two positive lenses, length = f1 + f2 (inverts beam)
Galilean:  negative lens (small-beam side) + positive lens (large-beam side),
           length = f_pos - |f_neg| (more compact, no inversion)
"""

import bisect

from sqlalchemy.orm import Session

from lenspairfinder.core.models import Lens, LensPair, SearchParams
from lenspairfinder.core.optics import (
    beam_radius_at_lens,
    galilean_length_mm,
    is_lens_type_suitable,
    is_negative_type_suitable,
    is_positive_type_suitable,
    keplerian_length_mm,
    magnification,
    min_clear_aperture_m,
    mm_to_m,
    m_to_mm,
    nm_to_m,
    numerical_aperture,
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


def _compute_cost(row1: LensRow, row2: LensRow) -> float | None:
    if row1.price_usd is not None and row2.price_usd is not None:
        return row1.price_usd + row2.price_usd
    return None


def _score(m_error: float, total_length: float, total_cost: float | None,
           type_penalty: int) -> float:
    cost_for_score = total_cost if total_cost is not None else 500.0
    return (
        10.0 * m_error
        + 0.001 * total_length
        + 0.002 * cost_for_score
        + 2.0 * type_penalty
    )


def find_lens_pairs(params: SearchParams, session: Session) -> list[LensPair]:
    """Search for lens pairs matching the given beam telescope parameters.

    Finds both Keplerian (two positive) and Galilean (negative + positive) pairs.
    Returns a list of LensPair results sorted by score (best first).
    """
    w1_m = um_to_m(params.w1_um)
    w2_m = um_to_m(params.w2_um)
    wavelength_m = nm_to_m(params.wavelength_nm)
    M = magnification(w1_m, w2_m)
    na1 = numerical_aperture(w1_m, wavelength_m)
    na2 = numerical_aperture(w2_m, wavelength_m)

    rows = get_wavelength_compatible_lenses(session, params.wavelength_nm)
    if not rows:
        return []

    # Split into positive and negative lenses
    pos_rows = [r for r in rows if r.is_positive and r.focal_length_mm > 0]
    neg_rows = [r for r in rows if not r.is_positive and r.focal_length_mm < 0]

    # Sort positive lenses by focal length for binary search
    pos_rows.sort(key=lambda r: r.focal_length_mm)
    pos_focals = [r.focal_length_mm for r in pos_rows]

    results: list[LensPair] = []

    # --- Keplerian pairs (positive + positive) ---
    for i, row1 in enumerate(pos_rows):
        f1 = row1.focal_length_mm
        f2_target = f1 * M
        f2_min = f2_target * (1 - params.m_tolerance)
        f2_max = f2_target * (1 + params.m_tolerance)

        lo = bisect.bisect_left(pos_focals, f2_min)
        hi = bisect.bisect_right(pos_focals, f2_max)

        for j in range(lo, hi):
            if i == j:
                continue
            row2 = pos_rows[j]
            f2 = row2.focal_length_mm

            # Aperture checks
            min_d1 = m_to_mm(min_clear_aperture_m(w1_m, mm_to_m(f1), wavelength_m, params.aperture_safety))
            if row1.diameter_mm < min_d1:
                continue
            min_d2 = m_to_mm(min_clear_aperture_m(w2_m, mm_to_m(f2), wavelength_m, params.aperture_safety))
            if row2.diameter_mm < min_d2:
                continue

            actual_M = f2 / f1
            m_error = abs(actual_M - M) / M
            total_length = keplerian_length_mm(f1, f2)
            total_cost = _compute_cost(row1, row2)

            suit1 = is_positive_type_suitable(row1.lens_type, na1)
            suit2 = is_positive_type_suitable(row2.lens_type, na2)
            penalty = (0 if suit1 else 1) + (0 if suit2 else 1)

            beam_r1 = beam_radius_at_lens(w1_m, mm_to_m(f1), wavelength_m)
            beam_r2 = beam_radius_at_lens(w2_m, mm_to_m(f2), wavelength_m)

            results.append(LensPair(
                lens1=_row_to_lens(row1),
                lens2=_row_to_lens(row2),
                actual_magnification=actual_M,
                magnification_error=m_error,
                total_length_mm=total_length,
                total_cost_usd=total_cost,
                score=_score(m_error, total_length, total_cost, penalty),
                na_side1=na1,
                na_side2=na2,
                beam_dia_at_lens1_mm=m_to_mm(2.0 * beam_r1),
                beam_dia_at_lens2_mm=m_to_mm(2.0 * beam_r2),
                lens1_type_suitable=suit1,
                lens2_type_suitable=suit2,
                config_type="Keplerian",
            ))

    # --- Galilean pairs (negative on small-beam side + positive on large-beam side) ---
    # Galilean: M = f_pos / |f_neg|, length = f_pos - |f_neg|
    # Lens 1 (side 1, small beam) = negative lens, Lens 2 (side 2, large beam) = positive lens
    # We need: f_pos / |f_neg| ≈ M, so f_pos ≈ |f_neg| * M
    for neg_row in neg_rows:
        f_neg = neg_row.focal_length_mm  # negative value
        abs_f_neg = abs(f_neg)

        f_pos_target = abs_f_neg * M
        f_pos_min = f_pos_target * (1 - params.m_tolerance)
        f_pos_max = f_pos_target * (1 + params.m_tolerance)

        lo = bisect.bisect_left(pos_focals, f_pos_min)
        hi = bisect.bisect_right(pos_focals, f_pos_max)

        for j in range(lo, hi):
            pos_row = pos_rows[j]
            f_pos = pos_row.focal_length_mm

            # System length must be positive
            sys_len = galilean_length_mm(f_neg, f_pos)
            if sys_len <= 0:
                continue

            # Aperture checks (use |f| for beam propagation)
            min_d_neg = m_to_mm(min_clear_aperture_m(w1_m, mm_to_m(abs_f_neg), wavelength_m, params.aperture_safety))
            if neg_row.diameter_mm < min_d_neg:
                continue
            min_d_pos = m_to_mm(min_clear_aperture_m(w2_m, mm_to_m(f_pos), wavelength_m, params.aperture_safety))
            if pos_row.diameter_mm < min_d_pos:
                continue

            actual_M = f_pos / abs_f_neg
            m_error = abs(actual_M - M) / M
            total_cost = _compute_cost(neg_row, pos_row)

            suit_neg = is_negative_type_suitable(neg_row.lens_type, na1)
            suit_pos = is_positive_type_suitable(pos_row.lens_type, na2)
            penalty = (0 if suit_neg else 1) + (0 if suit_pos else 1)

            beam_r1 = beam_radius_at_lens(w1_m, mm_to_m(abs_f_neg), wavelength_m)
            beam_r2 = beam_radius_at_lens(w2_m, mm_to_m(f_pos), wavelength_m)

            results.append(LensPair(
                lens1=_row_to_lens(neg_row),
                lens2=_row_to_lens(pos_row),
                actual_magnification=actual_M,
                magnification_error=m_error,
                total_length_mm=sys_len,
                total_cost_usd=total_cost,
                score=_score(m_error, sys_len, total_cost, penalty),
                na_side1=na1,
                na_side2=na2,
                beam_dia_at_lens1_mm=m_to_mm(2.0 * beam_r1),
                beam_dia_at_lens2_mm=m_to_mm(2.0 * beam_r2),
                lens1_type_suitable=suit_neg,
                lens2_type_suitable=suit_pos,
                config_type="Galilean",
            ))

    results.sort(key=lambda r: r.score)
    return results[:params.max_results]
