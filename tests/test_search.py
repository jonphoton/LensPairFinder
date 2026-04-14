"""Unit tests for the lens pair search algorithm."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from lenspairfinder.core.models import SearchParams
from lenspairfinder.core.search import find_lens_pairs
from lenspairfinder.db.schema import Base, LensRow


@pytest.fixture
def db_session():
    """In-memory SQLite session with test lenses."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # Insert test lenses: f=50mm and f=500mm achromat doublets, VIS coating
    session.add(LensRow(
        vendor="TestVendor", part_number="AC-050",
        description="f=50mm doublet", lens_type="achromat_doublet",
        focal_length_mm=50.0, diameter_mm=25.4, na=0.23,
        coating_type="AR_BBAR", wavelength_min_nm=400, wavelength_max_nm=700,
        price_usd=30.0, url="https://example.com/ac050",
        is_positive=True,
    ))
    session.add(LensRow(
        vendor="TestVendor", part_number="AC-500",
        description="f=500mm doublet", lens_type="achromat_doublet",
        focal_length_mm=500.0, diameter_mm=50.8, na=0.05,
        coating_type="AR_BBAR", wavelength_min_nm=400, wavelength_max_nm=700,
        price_usd=50.0, url="https://example.com/ac500",
        is_positive=True,
    ))
    # A small plano-convex that should fail aperture check for large beams
    # With w1=5000um at f=50mm, beam at lens is large enough to clip on 5mm aperture
    session.add(LensRow(
        vendor="TestVendor", part_number="PCX-050-SMALL",
        description="f=50mm plano-convex tiny", lens_type="plano-convex",
        focal_length_mm=50.0, diameter_mm=5.0, na=0.05,
        coating_type="AR_BBAR", wavelength_min_nm=400, wavelength_max_nm=700,
        price_usd=10.0, is_positive=True,
    ))
    # NIR-only lens — should not appear in VIS search
    session.add(LensRow(
        vendor="TestVendor", part_number="AC-500-NIR",
        description="f=500mm NIR doublet", lens_type="achromat_doublet",
        focal_length_mm=500.0, diameter_mm=50.8, na=0.05,
        coating_type="AR_BBAR", wavelength_min_nm=900, wavelength_max_nm=1100,
        price_usd=55.0, is_positive=True,
    ))
    session.commit()
    yield session
    session.close()


def test_finds_10x_pair(db_session):
    """Should find a pair with 10x magnification (f=50 + f=500)."""
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633, m_tolerance=0.05)
    results = find_lens_pairs(params, db_session)
    assert len(results) >= 1
    # At least one result should be the exact 10x pair
    part_pairs = {(r.lens1.part_number, r.lens2.part_number) for r in results}
    assert ("AC-050", "AC-500") in part_pairs


def test_magnification_within_tolerance(db_session):
    """All results should have M within tolerance."""
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633, m_tolerance=0.05)
    results = find_lens_pairs(params, db_session)
    for pair in results:
        assert pair.magnification_error <= 0.05


def test_nir_excluded_from_vis_search(db_session):
    """NIR-only lens should not appear in a 633nm search."""
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633, m_tolerance=0.05)
    results = find_lens_pairs(params, db_session)
    for pair in results:
        assert pair.lens1.part_number != "AC-500-NIR"
        assert pair.lens2.part_number != "AC-500-NIR"


def test_small_aperture_filtered(db_session):
    """The tiny 5mm lens should be filtered out when beam is large enough to clip."""
    # w1=5000um -> beam at f=50mm lens is large, should clip on 5mm aperture
    params = SearchParams(w1_um=5000, w2_um=50000, wavelength_nm=633, m_tolerance=0.05)
    results = find_lens_pairs(params, db_session)
    for pair in results:
        assert pair.lens1.part_number != "PCX-050-SMALL"


def test_results_sorted_by_score(db_session):
    """Results should be in ascending score order."""
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633, m_tolerance=0.10)
    results = find_lens_pairs(params, db_session)
    scores = [r.score for r in results]
    assert scores == sorted(scores)


def test_total_length_correct(db_session):
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633)
    results = find_lens_pairs(params, db_session)
    for pair in results:
        if pair.config_type == "Keplerian":
            expected = pair.lens1.focal_length_mm + pair.lens2.focal_length_mm
        else:  # Galilean
            expected = pair.lens2.focal_length_mm - abs(pair.lens1.focal_length_mm)
        assert pair.total_length_mm == pytest.approx(expected)


def test_total_cost_correct(db_session):
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633)
    results = find_lens_pairs(params, db_session)
    for pair in results:
        if pair.lens1.price_usd and pair.lens2.price_usd:
            expected = pair.lens1.price_usd + pair.lens2.price_usd
            assert pair.total_cost_usd == pytest.approx(expected)


def test_empty_db_returns_empty():
    """Search on empty database should return empty list."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633)
    results = find_lens_pairs(params, session)
    assert results == []
    session.close()


def test_finds_galilean_pair():
    """Should find Galilean pair when negative lens is available."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    # f=-50mm concave + f=500mm convex -> M = 500/50 = 10
    session.add(LensRow(
        vendor="Test", part_number="PC-NEG-050",
        description="f=-50mm plano-concave", lens_type="plano-concave",
        focal_length_mm=-50.0, diameter_mm=25.4,
        coating_type="AR_BBAR", wavelength_min_nm=400, wavelength_max_nm=700,
        price_usd=18.0, is_positive=False,
    ))
    session.add(LensRow(
        vendor="Test", part_number="AC-POS-500",
        description="f=500mm doublet", lens_type="achromat_doublet",
        focal_length_mm=500.0, diameter_mm=50.8, na=0.05,
        coating_type="AR_BBAR", wavelength_min_nm=400, wavelength_max_nm=700,
        price_usd=55.0, is_positive=True,
    ))
    session.commit()

    params = SearchParams(w1_um=50, w2_um=500, wavelength_nm=633, m_tolerance=0.05)
    results = find_lens_pairs(params, session)

    galilean = [r for r in results if r.config_type == "Galilean"]
    assert len(galilean) >= 1
    g = galilean[0]
    assert g.actual_magnification == pytest.approx(10.0)
    # Galilean length = f_pos - |f_neg| = 500 - 50 = 450
    assert g.total_length_mm == pytest.approx(450.0)
    session.close()
