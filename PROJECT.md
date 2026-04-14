---
description: Tool to find commercial lens pairs that achieve target magnifications at specified NAs and wavelengths.
---

# LensPairFinder

## Overview

LensPairFinder helps optical engineers and researchers find pairs of commercial lenses that together form a Keplerian telescope achieving desired beam waist transformations. Enter beam waists at two ends of the telescope and a wavelength, and the app searches a local database of commercial lenses to find matching pairs — ranked by magnification accuracy, cost, compactness, and aberration suitability.

## Goals

- Accept user-specified beam waists (w1, w2) and wavelength
- Compute required magnification (M = w2/w1), NA on each side, and lens type recommendations
- Search a local SQLite database of commercial lenses from Thorlabs, Edmund Optics, Newport, Asphericon
- Find lens pairs where f2/f1 matches target M within tolerance, filtered by coating wavelength and aperture clearance
- Present ranked results with total system length, cost, and direct purchase links

## Tech Stack

- Python 3.10+ / SQLite via SQLAlchemy
- **Web interface:** Flask + single-page HTML/JS app (primary)
- **Desktop GUI:** PyQt6 (optional, install with `pip install -e ".[gui]"`)
- Seed data: ~155 curated commercial lenses from 4 vendors
- Extensible via CSV/JSON import (see SCRAPING_GUIDE.md)

## Project Structure

```
run.py                          Desktop GUI entry point
run_web.py                      Web interface entry point
lenspairfinder/
  app.py                        QApplication bootstrap (desktop)
  web/server.py                 Flask web server + JSON API
  web/templates/index.html      Single-page web frontend
  core/optics.py                Gaussian beam physics
  core/search.py                Lens pair matching algorithm
  core/models.py                Dataclasses
  db/schema.py                  SQLAlchemy ORM models
  db/database.py                Engine/session management
  db/queries.py                 Query functions
  db/importer.py                CSV/JSON import with upsert
  db/seed.py                    Auto-load seed data on first run
  gui/                          PyQt6 GUI panels (desktop)
seed_data/                      Curated lens CSVs
tests/                          pytest test suite (19 tests)
SCRAPING_GUIDE.md               Instructions for full catalog scraping
```

## Current Status

**v0.2.0 — Web + Desktop.** Both interfaces fully functional. 19 tests passing. Seed data covers visible and NIR wavelengths across 4 vendors. Repo is public on GitHub.

## Running

### Web interface (recommended)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python run_web.py           # opens at http://localhost:5000
python run_web.py 8080      # or specify a port
```

### Desktop GUI
```bash
pip install -e ".[gui]"
python run.py
```

## Standing Instructions for Claude
- After every substantive change, automatically update PROJECT.md and commit + push to the git repository.
