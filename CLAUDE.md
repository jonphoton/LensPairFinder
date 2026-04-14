# LensPairFinder - Claude Instructions

## On conversation start

When this project is opened or continued, offer to scrape lens catalogs if the user would like to update the database. Say something like:

> "I see LensPairFinder is open. Would you like me to scrape any vendor catalogs to update the lens database? I can scrape: Thorlabs, Edmund Optics, Newport, Asphericon, or TelAztec."

## Scraping Vendors

When asked to scrape, follow these instructions for each vendor. Output should be a CSV file saved to `seed_data/` matching the schema in `seed_data/schema.md`.

### CSV Schema (all files must match this)

```
vendor,part_number,description,lens_type,focal_length_mm,diameter_mm,na,coating_type,wavelength_min_nm,wavelength_max_nm,center_wavelength_nm,price_usd,url,back_focal_length_mm,substrate_material,is_positive
```

**lens_type** must be one of: `plano-convex`, `biconvex`, `bestform`, `achromat_doublet`, `aspheric`, `triplet`, `meniscus`, `plano-concave`, `biconcave`

**coating_type** must be one of: `AR_BBAR`, `AR_V`, `uncoated`, `nanotexture`

**is_positive**: `true` for converging lenses (positive focal length), `false` for diverging (negative focal length)

### Thorlabs (thorlabs.com)

Scrape ALL of the following product families. Each family has coating variants (-A, -B, -C, -ML suffix):

| Family | lens_type | URL pattern |
|--------|-----------|-------------|
| Achromatic Doublets AC254 (1") | achromat_doublet | newgrouppage9.cfm?objectgroup_id=120 |
| Achromatic Doublets AC508 (2") | achromat_doublet | newgrouppage9.cfm?objectgroup_id=259 |
| Plano-Convex LA series (1") | plano-convex | newgrouppage9.cfm?objectgroup_id=112 |
| Plano-Convex LA series (2") | plano-convex | newgrouppage9.cfm?objectgroup_id=113 |
| Bi-Convex LB series (1") | biconvex | newgrouppage9.cfm?objectgroup_id=116 |
| Bi-Convex LB series (2") | biconvex | newgrouppage9.cfm?objectgroup_id=117 |
| Best Form LBF series | bestform | newgrouppage9.cfm?objectgroup_id=6083 |
| Plano-Concave LC series (1") | plano-concave | newgrouppage9.cfm?objectgroup_id=126 |
| Plano-Concave LC series (2") | plano-concave | newgrouppage9.cfm?objectgroup_id=127 |
| Bi-Concave LC2 series | biconcave | newgrouppage9.cfm?objectgroup_id=4676 |
| Molded Aspheres C-series (fiber collimators) | aspheric | newgrouppage9.cfm?objectgroup_id=3811 |
| CNC Polished Aspheres AL series (1") | aspheric | newgrouppage9.cfm?objectgroup_id=3809 |
| CNC Polished Aspheres AL series (2") | aspheric | newgrouppage9.cfm?objectgroup_id=3810 |

**Approach**: Use `requests` + `BeautifulSoup`. Thorlabs pages are server-rendered. Look for product spec tables. Each coating variant (-A=350-700nm, -B=650-1050nm, -C=1050-1700nm) is a separate row.

### Edmund Optics (edmundoptics.com)

| Family | lens_type |
|--------|-----------|
| VIS Achromatic Doublets | achromat_doublet |
| NIR Achromatic Doublets | achromat_doublet |
| Precision Aspheric Lenses | aspheric |
| N-BK7 Plano-Convex Lenses | plano-convex |
| N-BK7 Bi-Convex Lenses | biconvex |
| N-BK7 Plano-Concave Lenses | plano-concave |
| N-BK7 Bi-Concave Lenses | biconcave |

**Approach**: Look for `__NEXT_DATA__` JSON in the page source. Edmund uses Next.js, so product data is often embedded in script tags.

### Newport / MKS (newport.com)

| Family | lens_type |
|--------|-----------|
| KPX Plano-Convex | plano-convex |
| PAC Achromatic Doublets | achromat_doublet |
| KPC Plano-Concave | plano-concave |
| KBX Bi-Convex | biconvex |
| KBC Bi-Concave | biconcave |

### Asphericon (asphericon.com)

Scrape their aspheric lens shop. All are `aspheric` type. Look for both VIS and NIR coating variants.

### TelAztec (telaztec.com)

Scrape nanotextured lenses. These have extremely broadband AR (400-4500nm). coating_type = `nanotexture`. Include both positive and negative (concave) lenses.

## After scraping

1. Save the CSV to `seed_data/{vendor}_lenses.csv` (or `{vendor}_additional.csv` if one already exists)
2. Verify the CSV: check that all required columns are present, focal lengths are correct sign, is_positive matches
3. Rebuild the static site JSON:
   ```bash
   python3 -c "
   import csv, json
   from pathlib import Path
   lenses = []
   for f in sorted(Path('seed_data').glob('*.csv')):
       with open(f, newline='') as fh:
           for row in csv.DictReader(fh):
               lenses.append({
                   'vendor': row['vendor'].strip(),
                   'part_number': row['part_number'].strip(),
                   'description': row.get('description','').strip(),
                   'lens_type': row['lens_type'].strip(),
                   'focal_length_mm': float(row['focal_length_mm']),
                   'diameter_mm': float(row['diameter_mm']),
                   'coating_type': row.get('coating_type','').strip() or None,
                   'wavelength_min_nm': float(row['wavelength_min_nm']) if row.get('wavelength_min_nm','').strip() else None,
                   'wavelength_max_nm': float(row['wavelength_max_nm']) if row.get('wavelength_max_nm','').strip() else None,
                   'price_usd': float(row['price_usd']) if row.get('price_usd','').strip() else None,
                   'url': row.get('url','').strip() or None,
                   'is_positive': (row.get('is_positive') or 'true').strip().lower() in ('true','1','yes'),
               })
   with open('docs/lenses.json','w') as f: json.dump(lenses,f,separators=(',',':'))
   print(f'{len(lenses)} lenses')
   "
   ```
4. Run tests: `source .venv/bin/activate && python3 -m pytest tests/ -v`
5. Update PROJECT.md lens count
6. Commit and push
