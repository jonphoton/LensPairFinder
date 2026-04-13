# Lens Catalog Scraping Guide

This guide provides exact instructions for scraping commercial lens catalogs and importing them into LensPairFinder. The recommended approach is to run these as Claude Code sessions, which can adapt to page structure changes.

## Output Format

All scraped data must be saved as CSV files matching the schema in `seed_data/schema.md`. The key columns are:

```
vendor,part_number,description,lens_type,focal_length_mm,diameter_mm,na,coating_type,wavelength_min_nm,wavelength_max_nm,center_wavelength_nm,price_usd,url,back_focal_length_mm,substrate_material,is_positive
```

### lens_type values
Use exactly one of: `plano-convex`, `biconvex`, `achromat_doublet`, `aspheric`, `triplet`, `meniscus`

### coating_type values
Use exactly one of: `AR_BBAR`, `AR_V`, `uncoated`, `nanotexture`

### Important rules
- Only include **positive** lenses (is_positive = true). Skip negative/diverging lenses.
- Prices in USD. If only EUR/GBP available, convert at current rate and note in description.
- URLs should be direct product page links.
- If a lens comes in multiple coating variants (e.g., Thorlabs -A, -B, -C suffixes), each variant is a separate row.

---

## Thorlabs

### Product families to scrape

1. **Achromatic Doublets (AC series)**
   - 1" (25.4mm): https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=120
   - 2" (50.8mm): https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=259
   - Coating variants: -A (400-700nm), -B (650-1050nm), -C (1050-1700nm)

2. **Plano-Convex Lenses (LA series)**
   - N-BK7: https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=112
   - Coating variants: -A (350-700nm), -B (650-1050nm), -C (1050-1620nm)

3. **Aspheric Lenses**
   - Molded (C-series): https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3811
   - CNC Polished (AL series): https://www.thorlabs.com/newgrouppage9.cfm?objectgroup_id=3809

### Scraping approach

```python
import requests
from bs4 import BeautifulSoup
import csv
import time

# Thorlabs pages are mostly server-rendered HTML
# Look for table rows in the product comparison tables

def scrape_thorlabs_group(url):
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(resp.text, "html.parser")

    # Product tables typically have class "SpecTable" or are in
    # div with id containing "tablegroupcontent"
    # Each row has: Item #, description, specs

    # Extract from the spec table rows
    rows = []
    for table in soup.find_all("table", class_="SpecTable"):
        # Parse headers to find column indices
        # Parse each data row
        pass

    return rows

# Rate limit: wait 2 seconds between requests
```

### Known gotchas
- Pricing may require being logged in or may be loaded via AJAX. If prices aren't in the HTML, check for a JSON endpoint like `thorlabs.com/catalogdata/...`
- Some product families span multiple pages. Check for pagination links.
- The `-ML` suffix variants (V-coat) are separate products with narrower wavelength ranges.

---

## Edmund Optics

### Product families to scrape

1. **Achromatic Doublets**
   - VIS: https://www.edmundoptics.com/f/vis-0deg-achromatic-doublets/11779/
   - NIR: https://www.edmundoptics.com/f/nir-achromatic-doublets/12590/

2. **Precision Aspheric Lenses**
   - https://www.edmundoptics.com/f/precision-aspherized-achromatic-lenses/14353/

3. **Plano-Convex Lenses**
   - N-BK7: https://www.edmundoptics.com/f/n-bk7-plano-convex-lenses/11785/

### Scraping approach

Edmund Optics has a product search API that may be accessible:

```python
# Try the API first (much easier than scraping HTML)
api_url = "https://www.edmundoptics.com/api/search/products"
# Parameters may include: category, page, pageSize

# If the API doesn't work, fall back to HTML scraping
# Product pages use React/Next.js so the HTML may need JavaScript rendering
# Consider using requests + checking for JSON data embedded in <script> tags
```

### Known gotchas
- The site is heavily JavaScript-rendered. Look for `__NEXT_DATA__` script tag which contains JSON product data.
- Product stock numbers (e.g., #33-921) are unique identifiers — use as part_number.

---

## Newport (MKS Instruments)

### Product families

1. **Plano-Convex (KPX series)**
   - https://www.newport.com/c/plano-convex-lenses

2. **Achromatic Doublets (PAC series)**
   - https://www.newport.com/c/achromatic-doublet-lenses

### Scraping approach

```python
# Newport pages may use server-side rendering
# Look for product listing tables or JSON data
# Product URLs follow pattern: https://www.newport.com/p/{part_number}
```

---

## Asphericon

### Product families

1. **Aspheric Lenses (AFL series)**
   - https://www.asphericon.com/en/shop/aspheric-lenses

### Scraping approach

Asphericon has a smaller catalog. Their shop pages list lenses with full specs visible.

---

## How to run a scraping session

1. Open a Claude Code session in the LensPairFinder directory
2. Ask Claude to scrape a specific vendor, e.g.:
   ```
   Scrape all Thorlabs achromatic doublets from their website and save
   as seed_data/thorlabs_achromats_full.csv following the schema in
   seed_data/schema.md
   ```
3. Claude will write a Python script, run it, and save the CSV
4. Import into the app: launch the app, go to Database tab, click "Import CSV..."
5. Or place the CSV in `seed_data/` and click "Reload Seed Data"

## Validation

After scraping, verify the data:

```python
import csv
with open("scraped_file.csv") as f:
    reader = csv.DictReader(f)
    for row in reader:
        assert float(row["focal_length_mm"]) > 0
        assert float(row["diameter_mm"]) > 0
        assert row["lens_type"] in ("plano-convex", "biconvex", "achromat_doublet",
                                     "aspheric", "triplet", "meniscus")
        if row.get("wavelength_min_nm"):
            assert float(row["wavelength_min_nm"]) < float(row["wavelength_max_nm"])
print("Validation passed!")
```
