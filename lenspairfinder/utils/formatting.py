"""Unit display and number formatting helpers."""


def format_focal_length(mm: float) -> str:
    if mm >= 1000:
        return f"{mm / 1000:.1f} m"
    return f"{mm:.1f} mm"


def format_price(usd: float | None) -> str:
    if usd is None:
        return "N/A"
    return f"${usd:,.2f}"


def format_na(na: float) -> str:
    if na < 0.001:
        return f"{na:.1e}"
    return f"{na:.4f}"


def format_beam_diameter(mm: float) -> str:
    if mm < 0.1:
        return f"{mm * 1000:.1f} \u00b5m"
    return f"{mm:.2f} mm"
