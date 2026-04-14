# Lens Catalog CSV Schema

Each CSV file must have a header row with the following columns.

## Required columns

| Column | Type | Description |
|---|---|---|
| vendor | string | Company name, e.g. "Thorlabs" |
| part_number | string | Vendor part number, e.g. "AC254-050-A" |
| description | string | Free-text description |
| lens_type | string | One of: plano-convex, biconvex, bestform, achromat_doublet, aspheric, triplet, meniscus, plano-concave, biconcave |
| focal_length_mm | float | Effective focal length in mm |
| diameter_mm | float | Clear aperture diameter in mm |

## Optional columns

| Column | Type | Description |
|---|---|---|
| na | float | Numerical aperture (if specified by vendor) |
| coating_type | string | AR_BBAR, AR_V, uncoated, nanotexture |
| wavelength_min_nm | float | Lower bound of AR coating range (nm) |
| wavelength_max_nm | float | Upper bound of AR coating range (nm) |
| center_wavelength_nm | float | For V-coat lenses, the design wavelength |
| price_usd | float | Catalog price in USD |
| url | string | Direct link to product page |
| back_focal_length_mm | float | Back focal length in mm |
| substrate_material | string | e.g. N-BK7, N-SF11, CaF2 |
| is_positive | bool | true/false, default true. Set false for negative lenses. |
