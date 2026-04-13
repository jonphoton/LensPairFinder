---
description: Tool to find commercial lens pairs that achieve target magnifications at specified NAs and wavelengths.
---

# LensPairFinder

## Overview

LensPairFinder helps optical engineers and researchers find pairs of commercial lenses that together provide a desired magnification for a given numerical aperture (NA) and operating wavelength. Rather than manually searching through vendor catalogs and computing focal length ratios, this tool automates the search — matching real, purchasable lenses to your optical design requirements.

## Goals

- Accept user-specified target magnification, NA, and wavelength(s)
- Search across commercial lens catalogs (e.g., Thorlabs, Edmund Optics, Newport)
- Identify lens pairs (objective + tube lens, or relay pairs) whose focal length ratio achieves the target magnification
- Filter results by wavelength compatibility, NA coverage, and other optical constraints
- Present ranked results with key specs and purchasing info

## Scope

- **In scope:** Singlet and achromat catalog lenses, common visible/NIR wavelengths, standard magnification ranges used in microscopy and imaging
- **Out of scope (for now):** Custom lens design, full ray-tracing simulation, multi-element compound systems beyond pairs

## Current Status

Project bootstrapped. No application code yet.

## Standing Instructions for Claude
- After every substantive change, automatically update PROJECT.md and commit + push to the git repository.
