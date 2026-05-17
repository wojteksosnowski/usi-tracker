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

## Architectural Mandates

These rules govern all design decisions — they override convenience:

1. **Scraper delegation** — All portal I/O must go through the `usi_scrapers` library. No direct portal fetching in the tracker.
2. **Raw file immutability** — `raw_rp_*.json`, `raw_oto_*.json`, `raw_to_*.json` are reference data; never edit them after download.
3. **Portal slug immutability** — Raw slugs and IDs received from portals must never be modified by tracker code.
4. **Umbrella file precedence** — `usi_*.json` canonical files govern all business logic and UI; raw files are inputs only.
5. **Future repo split** — API must stay pure REST; avoid tight Python/React coupling to enable a clean frontend/backend separation later.

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

# Assign missing usi_dev_id / usi_inv_id across all records
python3 -m python_worker.main backfill-ids

# Initialize/update developer records from Konkurenci.csv (creates mock raw files + builds usi_dev_*.json)
python3 -m python_worker.main init-devs

# Rebuild usi_dev_*.json from existing raw files (no CSV needed — covers all USIdev subdirs)
python3 -m python_worker.main rebuild-devs
python3 -m python_worker.main rebuild-devs --force   # overwrite existing usi_dev_*.json too
python3 -m python_worker.main rebuild-devs --dry-run

# Run developer similarity/deduplication algorithm (writes suggestions[] to dev files)
python3 -m python_worker.main suggest

# Rebuild the fast investment list index (run after any bulk import or structural change)
python3 -m python_worker.main rebuild-index

# Audit developer duplicates and missing portal IDs
python3 python_worker/audit_dev_duplicates.py
python3 python_worker/audit_dev_duplicates.py --min-score 0.85

# Clean portal_mapping entries that lack a corresponding raw_*.json file (dry-run then apply)
python3 -m python_worker.clean_portal_mappings
python3 -m python_worker.clean_portal_mappings --apply

# Split any usi_dev_*.json with >1 portal into per-portal files (enforces 1:1 rule)
python3 -m python_worker.split_multi_portal_devs
python3 -m python_worker.split_multi_portal_devs --apply

# Repair stale DEV ID references left by a split (parent_id, suggestions, dev_master)
python3 -m python_worker.repair_stale_dev_refs
python3 -m python_worker.repair_stale_dev_refs --apply
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
    usi_counters.json  Auto-incremented ID counters: dev (DEV-NNNNN), inv (INV-NNNNN), dm (DM-NNNNN)
  schemas/       JSON Schema definitions (usi_investment, usi_developer, raw_rp, raw_oto, raw_to)
coda/            Coda.io TypeScript packs (scraperapi, dropbox, rynekpierwotny)
docs/            Documentation and specs
reference-data/  Static reference files: coda/ (CSV + request samples), rynekpierwotny/, otodom/
Public/          Dropbox-synced folder (do not rename)
  USI/           Downloaded images: {dev_slug}/{inv_slug}/{file}
  USIdata/       Investment JSON data: {dev_slug}/{inv_slug}/
  USIdev/        Developer profile JSONs: {dev_slug}/usi_dev_{DEV-ID}_{slug}.json (one per portal) + raw_{portal}_{slug}.json + dev_master_{DM-ID}.json + dev_log_{slug}.txt
logs/            Runtime logs (worker.log)
```

## Architecture

| Module | Role |
|---|---|
| `main.py` | CLI entry point; dispatches to ui, update-dev, update-inv, discover, download-raw, rebuild-from-raw, backfill-ids, rebuild-devs |
| `adapters/` | Package exposing `AdapterFactory`, `Merger`, and re-exporting the adapter classes from `usi_scrapers` (`RPAdapter`, `OtodomAdapter`, `TOAdapter`). `Merger.merge()` in `adapters/merger.py` combines portal results into the unified schema. |
| `developer_manager.py` | `DeveloperManager` — reads/writes the three-level developer file structure under `USIdev/{slug}/`. Generates `DEV-NNNNN`/`INV-NNNNN`/`DM-NNNNN` IDs. Key lookup methods: `get_developer(slug)` for URL-routing only; `get_developer_by_id(usi_dev_id)` for all cross-record references; `find_by_portal_id(portal, portal_id)` for portal ID lookups. Merge: `merge_developers(target_id, source_id)` writes Level 3 `dev_master_*.json` and logs to `dev_log_*.txt`. Never access `usi_dev_*.json` files directly — always go through `DeveloperManager`. |
| `init_developers.py` | `init_developers_from_konkurenci()` — seeds `USIdev/` from Konkurenci.csv by writing mock raw files then calling `_build_dev_from_raws()`. Split rule: rows with both `rpID` and `otoID` produce two separate records (RP-only + OTO-only) when `otoSlug` ≠ `usiFolder`. `rebuild_devs_from_raws()` — scans all USIdev subdirs and builds per-portal `usi_dev_*.json` from whichever raw files exist (no CSV needed). `_build_dev_from_raws()` calls `create_developer_file()` once per portal — one raw file → one Level 2 file. |
| `clean_portal_mappings.py` | Removes `portal_mapping` entries in `usi_dev_*.json` that lack a corresponding `raw_{portal}_{slug}.json` in the same directory. Run after any bulk import or migration. |
| `split_multi_portal_devs.py` | One-time and ongoing enforcement of the 1:1 portal rule: splits any `usi_dev_*.json` with multiple portal entries into separate per-portal files, each with a new DEV ID. Updates `dev_master_*.json` to group the new records. |
| `repair_stale_dev_refs.py` | Fixes dangling DEV ID references (in `parent_id`, `suggestions[]`, `dev_master.master_usi_dev_id`) left when a multi-portal file was split and its old ID deleted. Reconstructs the old→new mapping from `dev_master.merged_from`. |
| `detect_similar_devs.py` | `detect_similar()` — scans all dev records for name/geo similarity, writes `suggestions[]` array via `create_developer_file()` (never direct file writes). |
| `audit_dev_duplicates.py` | Standalone audit: Section A = unmerged suggestion pairs; Section B = dev records with portal IDs in Konkurenci.csv not yet in the file (split-aware — checks `otoSlug` column before flagging). |
| `fetcher.py` | `Fetcher` class + module-level `fetch_html`/`fetch_json` — shared HTTP utilities with rate-limiting |
| `scraper_rp.py` | RynekPierwotny.pl scraper — hits their REST API directly; exports `scrape_rynek_pierwotny`, `discover_rp_investments`, `download_raw_rp_json` |
| `scraper_otodom.py` | Otodom.pl scraper — fetches HTML via ScraperAPI, extracts `__NEXT_DATA__` JSON |
| `scraper_to.py` | TabelaOfert.pl scraper — tries direct HTTP first, falls back to ScraperAPI |
| `services/investment_service.py` | `InvestmentService` — business logic layer used by the Flask API; handles get/register/update investments, auto-creates developer profiles, delegates to `usi_scrapers` library |
| `services/discovery_service.py` | `DiscoveryService` — discover new investments per developer or per portal; filters already-known slugs, auto-registers new ones |
| `api/` | Flask blueprints (`investments`, `discovery`, `jobs`, `reports`, `poi`, `crawler_api`) mounted by `ui_server.py`; thin HTTP layer that delegates to service classes |
| `jobs.py` | `JobManager` — runs long scrape/update operations in background threads; tracks progress/status so the UI can poll `/api/jobs/<id>`. Any operation taking >1 s must go through `JobManager`. |
| `crawler.py` | `Wędrowiec` — background daemon (60 s tick) running two alternating modes: **Wizyta** (visits a known developer and runs discovery) and **Eksploracja** (pages portal catalogues to find new developers). Mounted by `ui_server.py` and exposed via `crawler_api` blueprint. |
| `slug_utils.py` | `slugify(text)` — converts Polish text to URL slugs; handles `ł/Ł` transliteration that NFKD alone cannot decompose |
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

**Developer ID-first rule:** All cross-references between developer records (suggestions, merged_from, API payloads) must use `usi_dev_id` as the foreign key — never `developer_slug`. Slugs are acceptable only for URL routing and display. The API merge/unmerge endpoints accept `source_id` (not `source_slug`) in the request body.

**Developer file layout — three levels:**
- **Level 1** (`raw_{portal}_{slug}.json`) — immutable portal snapshots; one file per portal per developer.
- **Level 2** (`usi_dev_{DEV-ID}_{slug}.json`) — definition file; **one per portal, 1:1 with its raw file**. Contains `portal_mapping` with exactly one non-null portal entry. Never put two portals in one Level 2 file. `portal_mapping` is always rebuilt from raw files by `_build_dev_from_raws()` — do not write it directly.
- **Level 3** (`dev_master_{DM-ID}.json`) — merge/relationship file; groups per-portal Level 2 records for the same company, stores `dismissed[]` suggestions. Created automatically by `merge_developers()`.
- **Log** (`dev_log_{slug}.txt`) — append-only JSONL event history per developer slug.

Filename uniqueness: `usi_dev_{DEV-ID}_{slug}.json` — the `DEV-ID` makes each file unique even when multiple portals share the same slug directory.

`usi_counters.json` tracks three auto-increment sequences: `dev` (DEV-NNNNN), `inv` (INV-NNNNN), `dm` (DM-NNNNN).

**Portal identifier normalization:** Normalize all portal identifiers to `rp`, `oto`, or `to` in the API layer before any routing, persistence, or branching. Raw payloads may use different internal names — translate at the boundary.

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

Developer profiles are stored under `Public/USIdev/{dev_slug}/`:
- `usi_dev_{DEV-ID}_{dev_slug}.json` — one file **per portal** (Level 2); contains exactly one non-null portal in `portal_mapping`
- `raw_rp_{dev_slug}.json` — raw RP developer profile (or mock with `_mock: true` when seeded from CSV)
- `raw_oto_{dev_slug}.json` — raw Otodom developer profile (or mock)
- `raw_to_{dev_slug}.json` — raw TabelaOfert developer profile (or mock)
- `dev_master_{DM-ID}.json` — Level 3 file; present when portals are grouped or suggestions dismissed
- `dev_log_{dev_slug}.txt` — append-only JSONL event log (merges, unmerges, dismissals)

Mock raw files (created by `init-devs`) contain only the portal IDs from Konkurenci.csv plus `"_mock": true`. When `update-dev` runs a real scrape, it overwrites the mock with the full portal response at the same path — the flag disappears automatically. `_build_dev_from_raws()` handles both mock and real formats when building `portal_mapping`.

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
- **Coordinate order in RP API**: `geo_point` from the RynekPierwotny API is `[longitude, latitude]` (GeoJSON order). Don't mix this with separate `Latitude`/`Longitude` fields.
- **Polish `ł` / `Ł` in slugs**: Python's `unicodedata.normalize("NFKD", ...)` does not decompose the Polish stroke letter. `slug_utils.slugify()` applies `str.maketrans("łŁ", "lL")` first. Omitting that step silently produces slugs containing literal `ł`.
- **Test fixtures are optional**: Tests guarded by `@pytest.mark.skipif(not PATH.exists(), ...)` are silently skipped when HTML/JSON reference files under `reference-data/` are absent. A fully green test run does not mean all tests ran.
- **`detect_similar_devs.py` must save via `DeveloperManager`**: Never write dev files directly (e.g. `open(path, "w")`); always use `dm.create_developer_file()`. Direct writes go to the wrong path after the USIdev subdirectory migration.
- **Real OTO dev profile shape**: The real Otodom developer JSON has `owner.id` and `filterAttributes.sellerId` for the agency ID — not a top-level `agency_id`. `_build_dev_from_raws()` handles both mock and real formats; see the extraction logic there before adding new portal adapters.
- **Canonical investment filename**: `usi_{portal}_{portal_id}.json` (e.g. `usi_rp_14563.json`). `_load_investment()` in `api/utils.py` globs new format first (rp→oto→to), then falls back to legacy slug-based variants (`usi_{slug}.json`, `usi_rp_{slug}.json`, etc.). To migrate old files on disk run `python3 -m python_worker.migrate_inv_filenames --data-dir /path/USIdata --apply`. `_load_inv_dir()` in the developer detail endpoint loads each investment directory exactly once — it does not iterate per `usi_*.json` file.
- **`image_paths` in usi_*.json is the source of truth**: `_load_investment()` uses `image_paths` from the JSON to build image API URLs. Never modify or regenerate these paths — they are written by the scrapers and are exact. Guessing paths from `dev_slug` or directory structure is wrong and will produce broken images. Fallback to filesystem scan only when `image_paths` is absent.
- **`list_developers()` deduplicates by `usi_dev_id`**: After the 1:1 portal split, the same slug can appear in multiple `usi_dev_*.json` files (one per portal). Deduplication is by ID, not slug — both are valid top-level records.
- **`_build_dev_from_raws()` creates one file per portal**: It calls `create_developer_file()` once per non-null portal, producing separate Level 2 files. Do not call it expecting a single multi-portal output file.
