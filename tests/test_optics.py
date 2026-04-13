"""Unit tests for optics calculations."""

import math
import pytest

from lenspairfinder.core.optics import (
    beam_radius_at_lens,
    divergence_half_angle,
    is_lens_type_suitable,
    magnification,
    min_clear_aperture_m,
    numerical_aperture,
    rayleigh_range,
    system_length_mm,
)


def test_divergence_633nm_10um():
    """633nm laser with 10um waist -> theta ~ 20.15 mrad."""
    theta = divergence_half_angle(10e-6, 633e-9)
    assert abs(theta - 633e-9 / (math.pi * 10e-6)) < 1e-8


def test_divergence_1064nm_50um():
    """1064nm laser with 50um waist."""
    theta = divergence_half_angle(50e-6, 1064e-9)
    expected = 1064e-9 / (math.pi * 50e-6)
    assert abs(theta - expected) < 1e-10


def test_na_paraxial():
    """For large waist (low NA), NA ~ theta."""
    na = numerical_aperture(1e-3, 633e-9)
    theta = divergence_half_angle(1e-3, 633e-9)
    assert abs(na - theta) / theta < 0.001


def test_na_high():
    """For small waist, NA = sin(theta) < theta."""
    na = numerical_aperture(1e-6, 633e-9)
    theta = divergence_half_angle(1e-6, 633e-9)
    assert na < theta
    assert abs(na - math.sin(theta)) < 1e-10


def test_rayleigh_range():
    zr = rayleigh_range(10e-6, 633e-9)
    expected = math.pi * (10e-6)**2 / 633e-9
    assert abs(zr - expected) < 1e-12


def test_beam_radius_at_lens():
    """w0=10um, f=50mm, 633nm. z_R ~ 0.496mm, w(f) ~ w0 * f/z_R."""
    w0 = 10e-6
    f = 50e-3
    lam = 633e-9
    z_r = math.pi * w0**2 / lam
    expected = w0 * math.sqrt(1 + (f / z_r)**2)
    result = beam_radius_at_lens(w0, f, lam)
    assert abs(result - expected) / expected < 1e-10


def test_magnification():
    assert magnification(10e-6, 100e-6) == pytest.approx(10.0)
    assert magnification(50e-6, 500e-6) == pytest.approx(10.0)
    assert magnification(100e-6, 50e-6) == pytest.approx(0.5)


def test_min_clear_aperture():
    """Aperture = safety * 2 * beam_radius."""
    w0 = 10e-6
    f = 50e-3
    lam = 633e-9
    safety = 3.0
    result = min_clear_aperture_m(w0, f, lam, safety)
    w_at_lens = beam_radius_at_lens(w0, f, lam)
    assert abs(result - safety * 2 * w_at_lens) < 1e-15


def test_system_length():
    assert system_length_mm(50, 500) == 550.0
    assert system_length_mm(100, 100) == 200.0


def test_lens_type_suitable_high_na():
    assert is_lens_type_suitable("aspheric", 0.05) is True
    assert is_lens_type_suitable("achromat_doublet", 0.05) is True
    assert is_lens_type_suitable("plano-convex", 0.05) is False


def test_lens_type_suitable_low_na():
    assert is_lens_type_suitable("plano-convex", 0.01) is True
    assert is_lens_type_suitable("aspheric", 0.01) is True
