"""Flask web server for LensPairFinder."""

import sys
from pathlib import Path

from flask import Flask, jsonify, render_template, request

from lenspairfinder.core.models import SearchParams
from lenspairfinder.core.optics import (
    magnification, numerical_aperture, um_to_m, nm_to_m,
)
from lenspairfinder.core.search import find_lens_pairs
from lenspairfinder.db.database import get_session
from lenspairfinder.db.importer import import_csv, import_json
from lenspairfinder.db.queries import get_lens_count, get_vendor_summary
from lenspairfinder.db.seed import seed_if_empty
from lenspairfinder.utils.constants import NA_ASPHERIC_THRESHOLD


app = Flask(__name__, template_folder=str(Path(__file__).parent / "templates"))

# Initialize DB and seed on first request
_initialized = False


def _ensure_db():
    global _initialized
    session = get_session()
    if not _initialized:
        seed_if_empty(session)
        _initialized = True
    return session


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search", methods=["POST"])
def api_search():
    data = request.get_json()
    session = _ensure_db()

    params = SearchParams(
        w1_um=float(data["w1_um"]),
        w2_um=float(data["w2_um"]),
        wavelength_nm=float(data["wavelength_nm"]),
        m_tolerance=float(data.get("m_tolerance", 5.0)) / 100.0,
        aperture_safety=float(data.get("aperture_safety", 3.0)),
    )

    results = find_lens_pairs(params, session)

    # Compute derived values for display
    w1_m = um_to_m(params.w1_um)
    w2_m = um_to_m(params.w2_um)
    lam_m = nm_to_m(params.wavelength_nm)
    M = magnification(w1_m, w2_m)
    na1 = numerical_aperture(w1_m, lam_m)
    na2 = numerical_aperture(w2_m, lam_m)

    return jsonify({
        "computed": {
            "magnification": round(M, 4),
            "na_side1": na1,
            "na_side2": na2,
            "asphere_recommended_side1": na1 > NA_ASPHERIC_THRESHOLD,
            "asphere_recommended_side2": na2 > NA_ASPHERIC_THRESHOLD,
        },
        "count": len(results),
        "results": [
            {
                "rank": i + 1,
                "lens1_vendor": r.lens1.vendor,
                "lens1_part": r.lens1.part_number,
                "lens1_desc": r.lens1.description,
                "lens1_type": r.lens1.lens_type.replace("_", " "),
                "lens1_f_mm": r.lens1.focal_length_mm,
                "lens1_dia_mm": r.lens1.diameter_mm,
                "lens1_coating": r.lens1.coating_type or "N/A",
                "lens1_price": r.lens1.price_usd,
                "lens1_url": r.lens1.url,
                "lens1_suitable": r.lens1_type_suitable,
                "lens2_vendor": r.lens2.vendor,
                "lens2_part": r.lens2.part_number,
                "lens2_desc": r.lens2.description,
                "lens2_type": r.lens2.lens_type.replace("_", " "),
                "lens2_f_mm": r.lens2.focal_length_mm,
                "lens2_dia_mm": r.lens2.diameter_mm,
                "lens2_coating": r.lens2.coating_type or "N/A",
                "lens2_price": r.lens2.price_usd,
                "lens2_url": r.lens2.url,
                "lens2_suitable": r.lens2_type_suitable,
                "actual_M": round(r.actual_magnification, 4),
                "m_error_pct": round(r.magnification_error * 100, 2),
                "total_length_mm": round(r.total_length_mm, 1),
                "total_cost": round(r.total_cost_usd, 2) if r.total_cost_usd else None,
                "score": round(r.score, 4),
                "na_side1": r.na_side1,
                "na_side2": r.na_side2,
                "beam_dia_l1_mm": round(r.beam_dia_at_lens1_mm, 3),
                "beam_dia_l2_mm": round(r.beam_dia_at_lens2_mm, 3),
            }
            for i, r in enumerate(results)
        ],
    })


@app.route("/api/database")
def api_database():
    session = _ensure_db()
    return jsonify({
        "total": get_lens_count(session),
        "vendors": [
            {
                "vendor": s["vendor"],
                "count": s["count"],
                "last_scraped": s["last_scraped"].isoformat() if s["last_scraped"] else None,
                "source": s["source"],
            }
            for s in get_vendor_summary(session)
        ],
    })


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    _ensure_db()
    print(f"Starting LensPairFinder web server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
