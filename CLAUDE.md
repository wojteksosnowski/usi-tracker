# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

USI Tracker is a Python worker that scrapes Polish real estate portals (RynekPierwotny.pl, Otodom.pl, TabelaOfert.pl) and stores structured data + images into a Dropbox folder. A Coda.io pack reads the resulting JSON files.

**Runtime flow:**
1. CLI commands (`update-dev`, `update-inv`, `discover`) trigger scrapers per portal
2. Each scraper fetches raw data and writes `raw_{portal}_{inv_slug}.json`
3. Portal adapters (`adapters.py`) transform raw responses to a unified schema
4. `Merger` combines all portal results and writes `usi_{inv_slug}.json`
5. Images are downloaded into `Public/USI/{dev_slug}/{inv_slug}/`

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
# Lint CSS (requires stylelint installed globally: npm install -g stylelint stylelint-config-standard)
./lint-styles.sh

# Run tests
pytest python_worker/

# Run a single test file
pytest python_worker/test_scraper_rp.py

# Run a single test function
pytest python_worker/test_scraper_rp.py::test_function_name

# Start local Flask web UI (browse investments, view maps/images)
python3 -m python_worker.main ui
# Or use the convenience wrapper (sets up venv + opens browser automatically):
./start-ui.sh

# Fetch and refresh all investments for a developer
python3 -m python_worker.main update-dev DOM-DEVELOPMENT-SA

# Refresh a single investment (re-scrapes all portals, re-merges)
python3 -m python_worker.main update-inv dom-development-sa/dzielna-one

# Discover new investments on portals for a developer (registers new usi_*.json skeletons)
python3 -m python_worker.main discover dom-development-sa
python3 -m python_worker.main discover dom-development-sa --download   # also download raw JSONs

# Download raw portal JSON for an investment without updating the merged record
python3 -m python_worker.main download-raw dom-development-sa/dzielna-one
python3 -m python_worker.main download-raw dom-development-sa/dzielna-one --portal rp

# Rebuild usi_*.json from already-downloaded raw_*.json files (no network requests)
python3 -m python_worker.main rebuild-from-raw dom-development-sa/dzielna-one

# Import all investments from USImaster.csv into USIdata/
python3 -m python_worker.main import-csv
python3 -m python_worker.main import-csv --limit 10 --dry-run
python3 -m python_worker.main import-csv --no-split   # keep dual-portal rows as single record

# Assign missing usi_dev_id / usi_inv_id across all records
python3 -m python_worker.main backfill-ids
```

## Configuration

Copy `python_worker/.env` and set:
- `SCRAPERAPI_KEY` — required for Otodom and TabelaOfert scraping (bot protection bypass)
- `DROPBOX_PATH` — absolute path to the local Dropbox root (differs between testing and deployment)
  - Testing: `/Volumes/Samsam/claude-py/usi-tracker/`
  - Deployment: `/Users/ws/Library/CloudStorage/Dropbox/`
- `HERE_API_KEY` — HERE Maps API key for satellite map image generation (has a hardcoded fallback in `config.py`)
- `DROPBOX_ACCESS_TOKEN` — reserved; not called by any Python module today
- `USI_PORT` — port for the local Flask UI (defaults to 5000)

`config.py` derives `USI_DATA_DIR`, `PUBLIC_USI_DIR`, `USI_DEV_DIR`, and `CSV_PATH` from `DROPBOX_PATH`.

## Directory Layout

```
python_worker/   Python scraper package (entry point: main.py)
  ui/            Web assets served by ui_server.py (HTML/JSX/CSS)
  data/
    wyrozniki.csv      Amenity-scoring reference table (facility codes → score tiers)
    usi_counters.json  Auto-incremented DEV/INV ID counters (managed by DeveloperManager)
  schemas/       JSON Schema definitions (usi_investment, usi_developer, raw_rp, raw_oto, raw_to)
coda/            Coda.io TypeScript packs (scraperapi, dropbox, rynekpierwotny)
docs/            Documentation and specs
reference-data/  Static reference files: coda/ (CSV + request samples), rynekpierwotny/, otodom/
Public/          Dropbox-synced folder (do not rename)
  USI/           Downloaded images: {dev_slug}/{inv_slug}/{file}
  USIdata/       Investment JSON data: {dev_slug}/{inv_slug}/
  USIdev/        Developer profile JSONs: usi_dev_{dev_slug}.json; raw/ for portal raw profiles
logs/            Runtime logs (worker.log)
```

## Architecture

| Module | Role |
|---|---|
| `main.py` | CLI entry point; dispatches to ui, update-dev, update-inv, discover, download-raw, rebuild-from-raw, import-csv, backfill-ids |
| `adapters/` | Package exposing `AdapterFactory`, `Merger`, and re-exporting the adapter classes from `usi_scrapers` (`RPAdapter`, `OtodomAdapter`, `TOAdapter`). `Merger.merge()` in `adapters/merger.py` combines portal results into the unified schema. |
| `developer_manager.py` | `DeveloperManager` — reads/writes `usi_dev_*.json` profiles, generates `DEV-NNNN`/`INV-NNNN` IDs, saves raw portal JSONs |
| `fetcher.py` | `Fetcher` class + module-level `fetch_html`/`fetch_json` — shared HTTP utilities with rate-limiting |
| `scraper_rp.py` | RynekPierwotny.pl scraper — hits their REST API directly; exports `scrape_rynek_pierwotny`, `discover_rp_investments`, `download_raw_rp_json` |
| `scraper_otodom.py` | Otodom.pl scraper — fetches HTML via ScraperAPI, extracts `__NEXT_DATA__` JSON |
| `scraper_to.py` | TabelaOfert.pl scraper — tries direct HTTP first, falls back to ScraperAPI |
| `services/investment_service.py` | `InvestmentService` — business logic layer used by the Flask API; handles get/register/update investments, auto-creates developer profiles, delegates to `usi_scrapers` library |
| `services/discovery_service.py` | `DiscoveryService` — discover new investments per developer or per portal; filters already-known slugs, auto-registers new ones |
| `api/` | Flask blueprints (`investments`, `discovery`, `jobs`, `reports`, `poi`, `crawler_api`) mounted by `ui_server.py`; thin HTTP layer that delegates to service classes |
| `jobs.py` | `JobManager` — runs long scrape/update operations in background threads; tracks progress/status so the UI can poll `/api/jobs/<id>`. Any operation taking >1 s must go through `JobManager`. |
| `crawler.py` | `Wędrowiec` — background daemon (60 s tick) running two alternating modes: **Wizyta** (visits a known developer and runs discovery) and **Eksploracja** (pages portal catalogues to find new developers). Mounted by `ui_server.py` and exposed via `crawler_api` blueprint. |
| `csv_importer.py` | Bulk importer from USImaster.csv; exports `slugify()` used across the codebase |
| `listings.py` | Batch fetch of recent investments from both portals; produces `app_latest_results*.json` |
| `image_saver.py` | Downloads and deduplicates images into `Public/USI/{dev_slug}/{inv_slug}/` |
| `grabber.py` | Generic regex-based link extractor for arbitrary developer sites |
| `url_parser.py` | Classifies URLs as RynekPierwotny or Otodom; extracts slugs and IDs |
| `here_maps.py` | Generates HERE Maps satellite image URLs; `enrich_with_here_map` adds `map_url` |
| `stage_detector.py` | Reads raw RP files, detects multi-stage investments, writes stage metadata back to `usi_*.json` |
| `portal_matcher.py` | Cross-portal fuzzy matcher (name + geo similarity); `filter_new_investments` used by discover flow |
| `logger_utils.py` | `log_to_processing_log(dev_slug, inv_slug, message)` — appends to per-investment log file |
| `migrator.py` | Legacy schema migration from old `app_result_*.json` format to `usi_*.json` |
| `ui_server.py` | Flask local web UI; mounts API blueprints and serves static JSX/CSS assets |
| `config.py` | Centralises all paths and API keys; `get_scraper_config()` builds config for the `usi_scrapers` library |
| `schemas/` | JSON Schema definitions for `usi_investment`, `usi_developer`, `raw_rp`, `raw_oto`, `raw_to` — the canonical data contracts |

The `usi_scrapers` PyPI library (`from usi_scrapers import api as scraper_api`) handles low-level scraping for the service layer. `InvestmentService` calls it via `get_scraper_config()` and wraps results into the local schema. Direct scraper modules (`scraper_rp.py`, etc.) are still used by CLI commands.

**Scraper Library Convention — critical:** Do NOT add new `scraper_*.py` files to this repo. All new portal interaction logic must live in the `usi_scrapers` library. Use `TechnicalDataManager` from that library for all raw-data saves and image syncs — never write portal data directly to `Public/USIdata` from tracker code. This prevents path drift between environments.

**Developer merging:** Developer profiles use a `parent_id` model — child records are filtered from main lists but retained for raw-data integrity. Use `DeveloperManager` for all reads/writes to `usi_dev_*.json`; never access those files directly.

## UI JSX Architecture

The web UI (`ui_server.py` + `python_worker/ui/`) uses React 18 with Babel Standalone — **no bundler, no npm**. All JSX files are loaded as `<script type="text/babel">` tags and share a single global scope. There are no `import`/`export` statements; every function defined in any file is immediately available to all files loaded after it.

**Load order in `index.html`** (dependency order matters):
```
registry.js                          → non-Babel module registry (plain JS)
theme.jsx                            → design tokens, applyTheme()
data.jsx                             → useInvestments(), ocenaLog(), avgRating()
components/atomic/Icon.jsx           → Icon primitive
components/atomic/Loading.jsx        → Loading primitive
components/ModuleErrorBoundary.jsx   → error boundary wrapper
components/DataGrid.jsx              → DataGrid table component
components/core.jsx                  → Spinner, SourceBadge, StandardCard, NavDrawer, …
components/ratings.jsx               → StarRating, CategoryRating, UsiStarScore, …
modules/modules-core.jsx             → ModuleWrapper, BaseModule
modules/modules-map.jsx              → MiniMap and map helpers
modules/modules-charts.jsx           → chart-based modules
modules/modules-ui.jsx               → UI-only modules
modules/modules-test.jsx             → test/dev modules
components/analytics.jsx             → CategoryAvgRow, ProgressBarAnalytics, MetadataPanel
components/Gallery.jsx               → PhotoOverlay, PhotoTile, SlideShow, Gallery, Lightbox
components/RatingsPanel.jsx          → useRatings, RatingsPanel
components/HeroBand.jsx              → HeroBand hero section
components/views/DetailViewA.jsx     → detail view layout A
components/views/DetailViewC.jsx     → detail view layout C
components/views/ListCard.jsx        → list card component
capture-tool.js / test-regression.js → plain JS dev tools
view-detail.jsx                      → Row, MetadataBlock, SourceLinks, detail page
view-list.jsx                        → list page
view-dev-list.jsx                    → developer list page
view-dev-detail.jsx                  → developer detail page
view-reports.jsx                     → reports/analytics page
view-library.jsx                     → component library browser
view-download.jsx                    → download/export page
view-dashboard.jsx                   → DashboardGrid, KPI, DashboardMap
view-storyboard.jsx                  → storyboard/design preview page
app.jsx                              → App (root), LoadingScreen, EmptyScreen
```

`design-canvas.jsx` is a standalone design tool not loaded by `index.html`.

When adding a new JSX file: place its `<script>` tag after all files it depends on, before all files that use it. Shared primitives → `components/atomic/`. Shared layout components → `components/core.jsx` or a new `components/*.jsx`. Module-panel components → the appropriate `modules/modules-*.jsx`. Gallery/photo logic → `components/Gallery.jsx`. Ratings logic → `components/RatingsPanel.jsx`.

**UI conventions:**
- **Babel race conditions:** Destructuring from `window` (e.g. `const { useState } = React`) MUST happen inside the component function at render time, not at file/module level — Babel Standalone may not have evaluated prior files yet.
- **Defensive rendering:** Use `safeRender` (validates `typeof === 'string' || 'number'`) before rendering any API data — raw API objects crash React with "Objects are not valid as a React child".
- **Shell Layout / DataBus:** Centralise all view-level controls (search, filters, action buttons) in the global `ActionBar`. Use the `DataBus` (React Context in `data.jsx`) to share state between views without prop-drilling.
- **Density-first grid:** Use `DataGrid` with `minCardWidth` targeting 7–9 columns on wide screens. Grid mode uses RAF-throttled virtualisation; Table mode is non-virtualised (use for small lists like developers to avoid flicker).
- **Error boundaries:** Wrap all views and analytics modules in `ModuleErrorBoundary`. Frontend errors are also posted to `/api/ui-error` and logged to `logs/ui_errors.log`.
- **Reports data:** Report definitions live in `Public/USIdata/reports/` as JSON files specifying investment filters and display modules (maps, charts, tables).

## Testing Approach

Tests use `requests-mock` to mock all HTTP calls — no real API calls in the test suite. Test files mirror module names (`test_scraper_rp.py`, etc.). When adding new scrapers or parsers, mock the HTTP layer and test JSON extraction logic directly.

`test_csv_importer.py` uses hardcoded fixture rows with no I/O. Tests that require the real CSV or a ground-truth file are guarded with `@pytest.mark.skipif(not PATH.exists(), ...)` so the suite always passes without the Dropbox data present.

When adding new tests, follow the fixture-builder helper pattern used throughout: private functions like `_make_rp_row()`, `_rp()`, `_oto()`, `_make_dual_row()` construct minimal valid dicts rather than large inline literals.

## USIdata File Structure

Each investment folder `Public/USIdata/{dev_slug}/{inv_slug}/` contains:

- `usi_{inv_slug}.json` — unified investment record written by `Merger.merge()`; the canonical data file read by the UI and Coda
- `raw_rp_{inv_slug}.json` — raw API response from RynekPierwotny
- `raw_oto_{inv_slug}.json` — raw Next.js page props from Otodom
- `raw_to_{inv_slug}.json` — raw data from TabelaOfert.pl
- `meta_{inv_slug}_ratings.json` — user-entered ratings metadata (preserved across re-syncs)
- `processing_log_{slug}.txt` — per-investment append-only log written on each update

Developer profiles are stored separately under `Public/USIdev/`:
- `usi_dev_{dev_slug}.json` — developer profile including `portal_mapping` (RP/Oto/TO IDs)
- `raw/` — raw portal developer profile JSONs

`usi_{inv_slug}.json` `sources` field structure:
```json
{
  "sources": {
    "rp": {"id": "12345"},
    "oto": {"url": "https://www.otodom.pl/..."},
    "to":  {"url": "https://tabelaofert.pl/..."}
  }
}
```

## Otodom ID Instability

Otodom.pl changes `otoID` (and sometimes the URL slug) for the same investment without warning. `USIfolder` (the investment slug) is the only stable identifier. Multiple CSV rows with the same `USIfolder` but different `otoID` represent the same investment at different points in time — the last row wins on import.

## Known Gotchas

- **`get_val()` for RP API responses**: The RynekPierwotny API wraps scalar values in `{"type": "...", "value": ...}` dicts. `adapters.py` exports `get_val(data, key, default=None)` to unwrap them. Any code reading RP API responses (raw or via `raw_rp_*.json`) must use this helper — plain `data[key]` returns the wrapper dict, not the scalar.
- **CSV nested JSON wrapper**: The `rpJSON`/`otoJSON` CSV columns wrap the full API response in `{"type": "obj", "value": {...}}`. Always unwrap with `data["value"]` before using the payload.
- **Coordinate order in RP API**: `geo_point` from the RynekPierwotny API is `[longitude, latitude]` (GeoJSON order). CSV columns are separate `Latitude`/`Longitude` fields. Don't mix the two read paths.
- **Polish `ł` / `Ł` in slugs**: Python's `unicodedata.normalize("NFKD", ...)` does not decompose the Polish stroke letter. Both `csv_importer.py` and `portal_matcher.py` apply `str.maketrans("łŁ", "lL")` first. Omitting that step silently produces slugs containing literal `ł`.
- **Test fixtures are optional**: Tests guarded by `@pytest.mark.skipif(not PATH.exists(), ...)` are silently skipped when HTML/JSON reference files under `reference-data/` are absent. A fully green test run does not mean all tests ran.
