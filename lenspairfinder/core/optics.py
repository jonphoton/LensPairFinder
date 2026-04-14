"""Gaussian beam optics calculations for Keplerian and Galilean telescope design.

All internal calculations use SI units (meters). Conversion helpers are
provided for the um/nm/mm units used at the GUI boundary.
"""

import math

from lenspairfinder.utils.constants import (
    NA_ASPHERIC_THRESHOLD,
    HIGH_NA_LENS_TYPES,
    ALL_POSITIVE_LENS_TYPES,
    HIGH_NA_NEGATIVE_LENS_TYPES,
    NEGATIVE_LENS_TYPES,
)


# ---------------------------------------------------------------------------
# Unit conversions
# ---------------------------------------------------------------------------

def um_to_m(x: float) -> float:
    return x * 1e-6

def nm_to_m(x: float) -> float:
    return x * 1e-9

def mm_to_m(x: float) -> float:
    return x * 1e-3

def m_to_mm(x: float) -> float:
    return x * 1e3


# ---------------------------------------------------------------------------
# Gaussian beam fundamentals
# ---------------------------------------------------------------------------

def divergence_half_angle(w0_m: float, wavelength_m: float) -> float:
    """Far-field 1/e^2 divergence half-angle in radians."""
    return wavelength_m / (math.pi * w0_m)


def numerical_aperture(w0_m: float, wavelength_m: float) -> float:
    """NA = sin(divergence half-angle) for a Gaussian beam."""
    theta = divergence_half_angle(w0_m, wavelength_m)
    if theta >= math.pi / 2:
        return 1.0
    return math.sin(theta)


def rayleigh_range(w0_m: float, wavelength_m: float) -> float:
    """Rayleigh range z_R = pi * w0^2 / lambda."""
    return math.pi * w0_m**2 / wavelength_m


def beam_radius_at_lens(w0_m: float, f_m: float, wavelength_m: float) -> float:
    """Beam 1/e^2 radius at a thin lens one focal length from the waist.

    w(z) = w0 * sqrt(1 + (z / z_R)^2)   with z = |f|.
    """
    z_r = rayleigh_range(w0_m, wavelength_m)
    return w0_m * math.sqrt(1.0 + (abs(f_m) / z_r) ** 2)


# ---------------------------------------------------------------------------
# Telescope design
# ---------------------------------------------------------------------------

def magnification(w1_m: float, w2_m: float) -> float:
    """Telescope magnification M = w2/w1 = f2/f1."""
    return w2_m / w1_m


def min_clear_aperture_m(w0_m: float, f_m: float, wavelength_m: float,
                          safety_factor: float = 3.0) -> float:
    """Minimum lens diameter (m) to avoid clipping.

    Diameter >= safety_factor * 2 * beam_radius_at_lens.
    """
    w_at_lens = beam_radius_at_lens(w0_m, f_m, wavelength_m)
    return safety_factor * 2.0 * w_at_lens


def keplerian_length_mm(f1_mm: float, f2_mm: float) -> float:
    """Keplerian telescope total length = f1 + f2 (mm). Both positive."""
    return f1_mm + f2_mm


def galilean_length_mm(f_neg_mm: float, f_pos_mm: float) -> float:
    """Galilean telescope total length = f_pos - |f_neg| (mm).

    f_neg_mm is negative (the diverging lens focal length).
    """
    return f_pos_mm - abs(f_neg_mm)


def is_positive_type_suitable(lens_type: str, na: float,
                               threshold: float = NA_ASPHERIC_THRESHOLD) -> bool:
    """Check whether a positive lens type is suitable for the given NA."""
    if na > threshold:
        return lens_type in HIGH_NA_LENS_TYPES
    return lens_type in ALL_POSITIVE_LENS_TYPES


def is_negative_type_suitable(lens_type: str, na: float,
                               threshold: float = NA_ASPHERIC_THRESHOLD) -> bool:
    """Check whether a negative lens type is suitable for the given NA.

    For negative lenses, all types work at any NA since they don't focus.
    """
    return lens_type in NEGATIVE_LENS_TYPES


# Keep backwards compatibility
def recommend_lens_types(na: float, threshold: float = NA_ASPHERIC_THRESHOLD) -> set[str]:
    if na > threshold:
        return HIGH_NA_LENS_TYPES
    return ALL_POSITIVE_LENS_TYPES


def is_lens_type_suitable(lens_type: str, na: float,
                           threshold: float = NA_ASPHERIC_THRESHOLD) -> bool:
    acceptable = recommend_lens_types(na, threshold)
    return lens_type in acceptable


def system_length_mm(f1_mm: float, f2_mm: float) -> float:
    """4f Keplerian telescope total length = f1 + f2 (mm)."""
    return f1_mm + f2_mm
