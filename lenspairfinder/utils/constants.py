"""Physical constants and default thresholds."""

import math

PI = math.pi

# Beam clipping safety: lens diameter >= APERTURE_FACTOR * (2 * beam_radius_at_lens)
# Factor of 3 gives < 1e-9 power loss for a Gaussian beam
APERTURE_SAFETY_FACTOR = 3.0

# Above this NA, recommend aspheric or achromat doublet to control spherical aberration
NA_ASPHERIC_THRESHOLD = 0.02

# Default magnification tolerance (fractional)
DEFAULT_M_TOLERANCE = 0.05  # ±5%

# Maximum results to return from search
DEFAULT_MAX_RESULTS = 200

# Lens types considered high-quality for high-NA applications
HIGH_NA_LENS_TYPES = {"aspheric", "achromat_doublet", "triplet"}

# All supported lens types
ALL_LENS_TYPES = {
    "plano-convex", "biconvex", "achromat_doublet",
    "aspheric", "triplet", "meniscus",
}
