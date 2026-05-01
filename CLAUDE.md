# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

USI Tracker is a Python worker that scrapes Polish real estate portals (RynekPierwotny.pl, Otodom.pl) and stores structured data + images into a Dropbox folder. A separate Coda.io pack reads and writes JSON files in that folder as a message bus — the Python worker is one side of that contract.

**Runtime flow:**
1. Coda writes `coda_request_{id}.json` into `Public/USIdata/{developer}/{investment}/`
2. Watchdog (`bus.py`) detects the file, routes to the right scraper
3. Scraper fetches data (via ScraperAPI for Otodom), downloads images to `Public/USI/`
4. Worker writes `app_result_{id}.json` alongside the request

## Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r python_worker/requirements.txt
mkdir -p logs   # required before first run; main.py opens logs/worker.log at startup
cp python_worker/.env python_worker/.env.local  # then edit with your keys
```

## Commands

```bash
# Run tests
pytest python_worker/

# Run a single test file
pytest python_worker/test_scraper_rp.py

# Run a single test function
pytest python_worker/test_scraper_rp.py::test_function_name

# Start watchdog (continuous monitoring)
python3 -m python_worker.main

# Manual scrape of a single URL
python3 -m python_worker.main https://rynekpierwotny.pl/oferty/...

# Fetch recent investments from both portals
python3 -m python_worker.main fetch
python3 -m python_worker.main fetch --limit-per-portal 5

# Quick smoke test (3 random items per portal)
python3 -m python_worker.main test

# Import all investments from USImaster.csv into USIdata/
python3 -m python_worker.main import-csv
python3 -m python_worker.main import-csv --limit 10 --dry-run
python3 -m python_worker.main import-csv --folder supernova-gdynia-redlowo
# Split dual-portal rows (both RP + Otodom) into separate app_result files
python3 -m python_worker.main import-csv --split-dual

# Audit dual-portal records in USImaster.csv (read-only, no files written)
python3 -m python_worker.main audit-dual

# Rename legacy app_result_imported.json in dual-portal folders (dry-run by default)
python3 -m python_worker.main migrate-dual
python3 -m python_worker.main migrate-dual --execute

# Start local Flask web UI (browse investments, view maps/images)
python3 -m python_worker.main ui
# Or use the convenience wrapper (sets up venv + opens browser automatically):
./start-ui.sh

# Enrich existing app_result files with sibling stage data from rp_details.json
python3 -m python_worker.main detect-stages

# Find cross-portal investment matches (RP ↔ Otodom/TO) by name/geo similarity
python3 -m python_worker.main match-portals
python3 -m python_worker.main match-portals --min-confidence high
```

## Configuration

Copy `python_worker/.env` and set:
- `SCRAPERAPI_KEY` — required for Otodom and TabelaOfert scraping (bot protection bypass)
- `DROPBOX_PATH` — absolute path to the local Dropbox root (differs between testing and deployment)
  - Testing: `/Volumes/Samsam/claude-py/usi-tracker/`
  - Deployment: `/Users/ws/Library/CloudStorage/Dropbox/`
- `HERE_API_KEY` — HERE Maps API key for satellite map image generation (has a hardcoded fallback in `config.py`)
- `DROPBOX_ACCESS_TOKEN` — Dropbox API OAuth token (reserved; the Python worker writes images to local disk and relies on the Dropbox desktop client for sync — this key is not called by any Python module today)
- `USI_PORT` — port for the local Flask UI (defaults to 5000)

`config.py` derives `USI_DATA_DIR`, `PUBLIC_USI_DIR`, and `CSV_PATH` from `DROPBOX_PATH`.

## Directory Layout

```
python_worker/   Python scraper package (entry point: main.py)
  ui/            Web assets served by ui_server.py (HTML/JS/CSS)
  data/
    wyrozniki.csv  Amenity-scoring reference table (facility codes → score tiers)
  schemas/       JSON Schema definitions (app_result, coda_request, rp_details, oto_details)
coda/            Coda.io TypeScript packs (scraperapi, dropbox, rynekpierwotny)
docs/            Documentation and specs; pdf/ for Coda UI screenshots
reference-data/  Static reference files: coda/ (CSV + request samples), rynekpierwotny/, otodom/
Public/          Dropbox-synced folder (do not rename)
  USI/           Downloaded images: {dev_slug}/{inv_slug}/{file}
  USIdata/       JSON data exchange: {dev_slug}/{inv_slug}/
logs/            Runtime logs (worker.log)
```

## Architecture

| Module | Role |
|---|---|
| `main.py` | CLI entry point; dispatches to watchdog, fetch, import-csv, ui, detect-stages, match-portals, or single-URL modes |
| `bus.py` | Watchdog file monitor; parses `coda_request_*.json`, dispatches scrapers, writes results; also calls `enrich_with_here_map` on every result. **On startup**, re-processes any request files that have no matching `app_result_*.json` sibling (crash recovery). |
| `scraper_rp.py` | RynekPierwotny.pl scraper — hits their REST API directly |
| `scraper_otodom.py` | Otodom.pl scraper — fetches HTML via ScraperAPI, extracts `__NEXT_DATA__` JSON |
| `scraper_to.py` | TabelaOfert.pl scraper — tries direct HTTP first, falls back to ScraperAPI |
| `csv_importer.py` | Bulk importer from USImaster.csv — reads rpJSON/otoJSON columns, writes USIdata structure; `audit_dual()` reports dual-portal records; `migrate_dual()` renames legacy result files |
| `listings.py` | Batch fetch of recent investments from both portals; produces `app_latest_results*.json` |
| `image_saver.py` | Downloads and deduplicates images into `Public/USI/{dev_slug}/{inv_slug}/` |
| `grabber.py` | Generic regex-based link extractor for arbitrary developer sites |
| `url_parser.py` | Classifies URLs as RynekPierwotny or Otodom; extracts slugs and IDs |
| `here_maps.py` | Generates HERE Maps satellite image URLs; `enrich_with_here_map` adds `map_url` to result dicts |
| `stage_detector.py` | Reads `rp_details.json` files, detects multi-stage investments, writes stage metadata back to `app_result` |
| `portal_matcher.py` | Cross-portal fuzzy matcher (name + geo similarity); writes `usi_match_suggestions.json` to `USI_DATA_DIR` |
| `ui_server.py` | Flask local web UI for browsing investments, images, and maps |
| `config.py` | Centralises all paths and API keys |
| `schemas/` | JSON Schema definitions for `app_result`, `coda_request`, `rp_details`, `oto_details` — the canonical data contracts |

## UI JSX Architecture

The web UI (`ui_server.py` + `python_worker/ui/`) uses React 18 with Babel Standalone — **no bundler, no npm**. All JSX files are loaded as `<script type="text/babel">` tags and share a single global scope. There are no `import`/`export` statements; every function defined in any file is immediately available to all files loaded after it.

**Load order in `index.html`** (dependency order matters):
```
theme.jsx           → design tokens, applyTheme()
data.jsx            → useInvestments(), ocenaLog(), avgRating()
components.jsx      → Spinner, Icon, CategoryRating, MiniMap, NavDrawer, …
view-detail-gallery.jsx → tileBtn, DeletionBadge, PhotoOverlay, PhotoTile, SlideShow, Gallery, Lightbox
view-detail-ratings.jsx → _ratingCache, useRatings, RatingsPanel
view-detail.jsx     → Row, MetadataBlock, SourceLinks, HeroBand, ModeC, DetailRightPanel
view-list.jsx       → ListGrid, ListCard, ListToolbar
view-dashboard.jsx  → DashboardGrid, KPI, DashboardMap
app.jsx             → App (root), LoadingScreen, EmptyScreen
```

When adding a new JSX file: place its `<script>` tag after all files it depends on, before all files that use it. Adding a new shared component → `components.jsx`. Adding gallery/photo logic → `view-detail-gallery.jsx`. `design-canvas.jsx` is a standalone design tool not loaded by `index.html`.

## Testing Approach

Tests use `requests-mock` to mock all HTTP calls — no real API calls in the test suite. Test files mirror module names (`test_scraper_rp.py`, etc.). When adding new scrapers or parsers, mock the HTTP layer and test JSON extraction logic directly.

`test_csv_importer.py` uses hardcoded fixture rows with no I/O. Tests that require the real CSV or a ground-truth file are guarded with `@pytest.mark.skipif(not PATH.exists(), ...)` so the suite always passes without the Dropbox data present.

When adding new tests, follow the fixture-builder helper pattern used throughout: private functions like `_make_rp_row()`, `_rp()`, `_oto()`, `_make_dual_row()` construct minimal valid dicts rather than large inline literals. `_make_dual_row()` merges RP and OTO fixtures with RP winning on shared keys (imgList, Latitude, Longitude) so both JSONs are present and coordinates stay consistent.

## USIdata File Structure

`Public/USIdata/` root level also contains:
- `app_latest_results.json` — full batch output from `listings.py` (all recent investments, includes `raw_details`)
- `app_latest_results_brief.json` — same without `raw_details`, for fast Coda table sync
- `usi_match_suggestions.json` — cross-portal match output from `match-portals`

Each investment folder `Public/USIdata/{dev_slug}/{inv_slug}/` contains:

- `rp_details.json` — raw API response from RynekPierwotny (vendor-specific, used by Coda `.ParseJSON`)
- `oto_details.json` — raw Next.js page props from Otodom (vendor-specific)
- `to_details.json` — raw data from TabelaOfert.pl (vendor-specific)
- `app_result_{id}.json` — lightweight metadata written by the worker or importer
- `processing_log.txt` — per-investment append-only log written by `bus.py` on each task

The scrapers (`scraper_rp.py`, `scraper_otodom.py`) still include `raw_details` in their `app_result_*.json`. The CSV importer (`csv_importer.py`) writes result files **without** `raw_details` (raw data goes into the separate `rp_details.json`/`oto_details.json` files). Unifying the two formats is deferred.

**CSV importer result file naming:**
- Single-portal row (RP only or Otodom only) → `app_result_imported.json`
- Dual-portal row with `--split-dual` (both rpJSON + otoJSON present) → `app_result_imported_rp.json` + `app_result_imported_oto.json`

USImaster.csv contains ~438 dual-portal rows (investments present on both RP and Otodom). Before `--split-dual` existed, these produced only `app_result_imported.json` (RP-only result); `migrate-dual` renames those legacy files to `_rp.json` in folders that already have both `rp_details.json` and `oto_details.json`.

`image_paths` in `app_result` are Dropbox API paths (`/Public/USI/{dev}/{inv}/{file}`) used directly by the Coda pinemint-dropbox pack (`DBGetSharedDropboxLink`, `DBUpdateImageThumbnail`).

## Message Bus Contract

Request file written by Coda (`coda_request_{id}.json`):
```json
{
  "type": "rynekpierwotny | otodom | tabelaofert | grabber",
  "rpID": "...",
  "USIfolder": "investment-slug",
  "developer_slug": "dev-slug"
}
```

`bus.py` also infers `type` from field presence when `type` is absent: `rpID` → `rynekpierwotny`, `otoID`/`strona_otodom` → `otodom`. Slugs are derived from the request JSON fields (`developer_slug`, `rpSlug`, `otoSlug`, `USIfolder`) with filesystem path as fallback.

Result file written by worker (`app_result_{id}.json`):
```json
{
  "source": "rynekpierwotny.pl",
  "developer_slug": "...",
  "investment_slug": "...",
  "latitude": 54.0,
  "longitude": 18.0,
  "image_paths": ["/Public/USI/dev/inv/img.jpg"]
}
```

## Portal URL field (`url` in app_result)

`url` in `app_result*.json` is the human-facing portal page (not the internal API endpoint):
- RynekPierwotny: `https://rynekpierwotny.pl/oferty/{vendor_slug}/{rp_slug}-{rpID}/`
- Otodom: value from `strona_otodom` column in CSV

**How `url` is populated (priority order):**
1. `strona_rynek` / `strona_otodom` from the Coda request JSON or CSV row (import path)
2. Auto-constructed by `scraper_rp.py` from `details["slug"]` + `vendor.slug` returned by the RP API (scraper fallback when URL is not passed in)

`csv_importer.py` reads `strona_rynek`/`strona_otodom` directly into the `url` field. `bus.py` (line 87) picks them from the Coda request. Old `app_result_imported.json` files created before this field was tracked will be missing `url` — refresh with `import-csv`.

## Otodom ID Instability

Otodom.pl changes `otoID` (and sometimes the URL slug) for the same investment without warning. `USIfolder` (the investment slug) is the only stable identifier. Multiple CSV rows with the same `USIfolder` but different `otoID` represent the same investment at different points in time — the last row wins on import.

## Known Gotchas

- **CSV nested JSON wrapper**: The `rpJSON`/`otoJSON` CSV columns wrap the full API response in `{"type": "obj", "value": {...}}`. Always unwrap with `data["value"]` before using the payload.
- **Coordinate order in RP API**: `geo_point` from the RynekPierwotny API is `[longitude, latitude]` (GeoJSON order). CSV columns are separate `Latitude`/`Longitude` fields. Don't mix the two read paths.
- **2-second sleep in `bus.py`**: `on_created()` sleeps 2 s before reading the Coda request file to let Coda finish writing atomically. This is intentional — do not remove it.
- **Test fixtures are optional**: Tests guarded by `@pytest.mark.skipif(not PATH.exists(), ...)` are silently skipped when HTML/JSON reference files under `reference-data/` are absent. A fully green test run does not mean all tests ran.
- **`get_val()` for RP API responses**: The RynekPierwotny API wraps scalar values in `{"type": "...", "value": ...}` dicts. `scraper_rp.py` exports `get_val(data, key, default=None)` to unwrap them. Any code reading RP API responses (raw or via `rp_details.json`) must use this helper — plain `data[key]` returns the wrapper dict, not the scalar.
- **Polish `ł` / `Ł` in slugs**: Python's `unicodedata.normalize("NFKD", ...)` does not decompose the Polish stroke letter. Both `csv_importer.py` and `portal_matcher.py` apply `str.maketrans("łŁ", "lL")` first. Omitting that step silently produces slugs containing literal `ł`.
