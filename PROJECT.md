---
description: Tool to find commercial lens pairs that achieve target magnifications at specified NAs and wavelengths.
---

# LensPairFinder

**[Try it live](https://jonphoton.github.io/LensPairFinder/)**

## Overview

LensPairFinder helps optical engineers and researchers find pairs of commercial lenses that together form a Keplerian telescope achieving desired beam waist transformations. Enter beam waists at two ends of the telescope and a wavelength, and the app searches a database of commercial lenses to find matching pairs — ranked by magnification accuracy, cost, compactness, and aberration suitability.

## Goals

- Accept user-specified beam waists (w1, w2) and wavelength
- Compute required magnification (M = w2/w1), NA on each side, and lens type recommendations
- Search a catalog of commercial lenses from Thorlabs, Edmund Optics, Newport, Asphericon
- Find lens pairs where f2/f1 matches target M within tolerance, filtered by coating wavelength and aperture clearance
- Present ranked results with total system length, cost, and direct purchase links

## Three Ways to Use It

### 1. Static website (GitHub Pages) — no install needed
Visit **https://jonphoton.github.io/LensPairFinder/** — runs entirely in your browser.

### 2. Local web server (Flask)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python run_web.py           # http://localhost:5000
```

### 3. Desktop GUI (PyQt6)
```bash
pip install -e ".[gui]"
python run.py
```

## Tech Stack

- **Static site (docs/):** Pure HTML/CSS/JS with embedded optics engine and JSON lens database
- **Web server:** Python 3.10+ / Flask / SQLAlchemy / SQLite
- **Desktop GUI:** PyQt6 (optional)
- Seed data: 135 curated commercial lenses from 4 vendors
- Extensible via CSV/JSON import (see SCRAPING_GUIDE.md)

## Project Structure

```
docs/                           GitHub Pages static site
  index.html                    Self-contained client-side app
  lenses.json                   Embedded lens database
run.py                          Desktop GUI entry point
run_web.py                      Flask web server entry point
lenspairfinder/
  core/optics.py                Gaussian beam physics
  core/search.py                Lens pair matching algorithm
  web/server.py                 Flask web server + JSON API
  db/                           SQLAlchemy ORM + import tools
  gui/                          PyQt6 GUI panels (desktop)
seed_data/                      Curated lens CSVs
tests/                          pytest test suite (19 tests)
SCRAPING_GUIDE.md               Instructions for full catalog scraping
```

## Current Status

**v0.3.0 — Live on GitHub Pages.** Static site runs in-browser with no backend. Also available as local Flask server or desktop PyQt6 app. 19 tests passing. Column sorting in the web UI.

## Standing Instructions for Claude
- After every substantive change, automatically update PROJECT.md and commit + push to the git repository.
