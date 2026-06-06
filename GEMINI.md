# USI Tracker - Gemini Context

USI Tracker is a specialized system for monitoring real-estate investments in Poland across multiple portals (**RynekPierwotny.pl**, **Otodom.pl**, and **TabelaOfert.pl**). It follows a CLI-first architecture with a high-density React-based local UI.

## 🚀 Project Overview

- **Purpose**: Automate the collection of investment data (prices, delivery dates, amenities, photos) and unify them into a canonical JSON format (`usi_*.json`).
- **Core Architecture**:
  - **ID-only**: Universal rule - all identification must be derived from unique ID. Slug based identification is prohibitted.
  - **Ruthless**: Bądź bezwzględny dla kodu, nie cackaj się - tnij, usuwaj, pisz od nowa jeżeli jest taka potrzeba. Kieruj się zasadą ID-only oraz obecnością API usi-scrapers.
  - **Identity Resolver (Resource Mapping)**: Centralized services (`InvestmentService.get_investment_resources`, `DeveloperManager.get_developer_resources`) that resolve physical file paths exclusively from USI IDs. All I/O operations must use these resolvers to avoid path drift caused by slug changes.
  - **Hot Indexing**: High-performance O(1) memory lookup for investments and developers via dictionaries (slug-to-entry and ID-to-entry). 
  - **Concurrency Guards**: Mandatory locks (`_index_lock`, `_rebuild_lock`) and state flags (`_is_rebuilding`) for index management to prevent race conditions and CPU spikes during filesystem scans.
  - **Thin-Client Scrapers**: ALL technical I/O, raw data fetching, and asset management (images) are delegated to the `usi-scrapers` library. The tracker acts as an orchestrator.
  - **Wedrowiec (Unified Crawler)**: A background daemon (`crawler.py`) that performs periodic "Visits" (discovery for known developers) and "Exploration" (systematic paging of portal catalogs to find new developers).
  - **TechnicalDataManager**: Centralized manager in `usi-scrapers` used for path resolution and technical data persistence.
  - **DeveloperManager**: Handles developer profiles, merging logic (`parent_id` model), and SUGGESTIONS for linking records across portals.
  - **Adapters**: Transforms raw vendor-specific JSON into a unified USI schema. Located in `python_worker/adapters/` (Factory pattern).
  - **Service Layer**: Business logic encapsulated in `python_worker/services/` (`InvestmentService`, `DiscoveryService`). Focuses on semantic merging and ratings.
  - **Data Store**: A file-based structure under `Public/USIdata/` (investments) and `Public/USIdev/` (developer profiles).
  - **UI API**: Modular Flask Blueprints in `python_worker/api/blueprints/`.
  - **Consistency API**: Built-in verification of `usi-scrapers` health, triggered on startup and visible in UI.
  - **UI**: A local Flask-served React application for high-density visualization.
- **Integrations**: Syncs with Coda.io and Dropbox for distributed data access.

- **Cache-Control for Images**: Images served via `/api/image/` MUST include `Cache-Control: public, max-age=604800, immutable` headers. This optimizes frontend gallery performance by reducing redundant server I/O calls for already cached assets.
- **Robust Filesystem Scanning**: Filesystem operations (like `iterdir()`, `glob()`) MUST be wrapped in robust error handling, use `visited_dirs` set for cycle detection in symlinks, and employ `strict=False` in `resolve()` to handle dangling symlinks without crashing. Use backoff/sleep to mitigate CPU thrashing on repeated I/O errors.

## 🛠 Building and Running

### Prerequisites
- Python 3.13+
- ScraperAPI key (for bypassing bot protection on some portals)
- HERE Maps API key (for map enrichment and POI fetch)

### Setup
~~~~bash
python3 -m venv venv
source venv/bin/activate
pip install -r python_worker/requirements.txt
mkdir -p logs   # Required before first run; main.py opens logs/worker.log at startup
cp python_worker/.env python_worker/.env.local  # Then edit with your keys
~~~~

### Key Commands
- **Start UI**: `./start-ui.sh` or `python3 -m python_worker.main ui`
- **Lint CSS**: `./lint-styles.sh` (Requires global stylelint: `npm install -g stylelint stylelint-config-standard`)
- **Run Tests**: `pytest tests/` (Single file: `pytest tests/test_scraper_rp.py`)
- **Discover New Investments**: `python3 -m python_worker.main discover {dev_slug}` (Add `--download` to save raw JSONs)
- **Update Single Investment**: `python3 -m python_worker.main update-inv {dev_slug}/{inv_slug}`
- **Update Developer**: `python3 -m python_worker.main update-dev {dev_slug}`
- **Download Raw JSON Only**: `python3 -m python_worker.main download-raw {dev_slug}/{inv_slug} [--portal rp]`
- **Rebuild from Local Raws**: `python3 -m python_worker.main rebuild-from-raw {dev_slug}/{inv_slug}` (No network requests)
- **Bulk Import (CSV)**: `python3 -m python_worker.main import-csv`
- **Backfill IDs**: `python3 -m python_worker.main backfill-ids` (Assigns missing USI IDs across all records)
- **Initialize Devs**: `python3 -m python_worker.main init-devs` (Seeds `USIdev/` from Konkurenci.csv)
- **Rebuild Dev Profiles**: `python3 -m python_worker.main rebuild-devs [--force] [--dry-run]`
- **Run Similarity Suggestions**: `python3 -m python_worker.main suggest` (Finds duplicates)
- **Rebuild Fast Index**: `python3 -m python_worker.main rebuild-index` (Run after any bulk import or structural change)
- **Audit Developer Duplicates**: `python3 python_worker/audit_dev_duplicates.py [--min-score 0.85]`
- **Clean Portal Mappings**: `python3 -m python_worker.clean_portal_mappings [--apply]`

## 📂 Directory Structure

~~~~text
python_worker/   Python scraper package (entry point: main.py)
  ui/            Web assets served by ui_server.py (HTML/JSX/CSS)
  data/
    wyrozniki.csv      Amenity-scoring reference table (facility codes → score tiers)
    usi_counters.json  Auto-incremented ID counters: dev (DEV-NNNNN), inv (INV-NNNNN), dm (DM-NNNNN)
  schemas/       JSON Schema definitions (usi_unified, usi_dev, rp_details, oto_details)
docs/            Documentation and specs
reference-data/  Static reference files: coda/ (CSV + request samples), rynekpierwotny/, otodom/
Public/          Dropbox-synced folder (do not rename)
  USI/           Downloaded images: {dev_slug}/{inv_slug}/{file}
  USIdata/       Investment JSON data: {dev_slug}/{inv_slug}/
  USIdev/        Developer profile JSONs: {dev_slug}/usi_dev_{DEV-ID}_{slug}.json (one per portal) + raw_{portal}_{slug}.json + dev_master_{DM-ID}.json + dev_log_{slug}.txt
logs/            Runtime logs (worker.log, ui_errors.log)
~~~~

### Raporty i Analizy
- **System raportowy**: Oparty na plikach JSON w `Public/USIdata/reports/`. Definiują one filtry inwestycji oraz moduły prezentacji (mapy, wykresy, tabele).
- **Szyna Danych (DataBus)**: System wymiany danych między niezależnymi komponentami (np. lista -> raport -> widżety). Zaimplementowany w `python_worker/ui/data.jsx` przy użyciu React Context. 
- **Moduły analityczne**: Reużywalne komponenty (np. `MapModule`, `PriceTrendModule`, `PoiModule`) osadzane w raportach i widokach szczegółowych. Wykorzystują Chart.js oraz HERE Maps API.

## ⚖️ Development Conventions

### Scraper Delegation & Library Architecture
- **No Local Scrapers**: Do NOT add new `scraper_*.py` files to `usi-tracker`. All portal interaction logic must reside in the `usi-scrapers` library. 
- **I/O Delegation**: Always use `TechnicalDataManager` from the library to save raw data or sync images. This prevents path drift and ensures consistent storage across environments. Never write portal data directly to `Public/USIdata` from tracker code.
- **Semantic Separation**: Keep data transformation (Adapters) and merging (Merger) in `usi-tracker`. The library provides "Technical Data," while the tracker creates "Business Data."
- **Path Resolution**: Avoid hardcoding paths like `Public/USIdata`. Use `config.public_dir` and library utilities to resolve paths.

### Developer File Layout & Merging Mechanics
Developer profiles use a **three-level** architecture under `Public/USIdev/{slug}/`:
1. **Level 1** (`raw_{portal}_{slug}.json`) — Immutable portal snapshots; one file per portal per developer.
2. **Level 2** (`usi_dev_{DEV-ID}_{slug}.json`) — Definition file; **one per portal, 1:1 with its raw file**. Contains `portal_mapping` with exactly one non-null portal entry. Never put two portals in one Level 2 file. `portal_mapping` is always rebuilt from raws by `_build_dev_from_raws()` — do not write it directly. The `DEV-ID` prefix ensures filename uniqueness across different portals sharing the same slug directory.
3. **Level 3** (`dev_master_{DM-ID}.json`) — Merge/relationship file; groups per-portal Level 2 records for the same company using a `parent_id` model, stores `dismissed[]` suggestions. Created automatically by `merge_developers()`.
4. **Log** (`dev_log_{slug}.txt`) — Append-only JSONL event history per developer slug.

*Mandate*: Never access `usi_dev_*.json` files directly — always go through `DeveloperManager`. `list_developers()` deduplicates records by `usi_dev_id`, not by slug.

### UI Development (React 18)
- **No Bundler**: Files in `python_worker/ui/` are loaded directly in `index.html`. All JSX files share a single global scope.
- **Babel Standalone Race Conditions**: Extraction of variables from `window` (destructuring e.g., `const { useState } = React`) MUST occur inside the component function (render-time), not at the file/module level, because Babel may not have evaluated prior files yet.
- **Defensive Rendering**: Always use `safeRender` (validation `typeof === 'string' || 'number'`) when rendering API data to prevent "Objects are not valid as a React child" errors.
- **Shell Layout Pattern**: Centralize all view-specific controls (Search, Filters, Mode-Toggles, Actions) in the global `ActionBar`. Use the `DataBus` to manage shared state across navigation. Individual views should focus on data presentation only.
- **Expert UI (Density)**: UIs should prioritize information density. Use `DataGrid` with `minCardWidth` to achieve 7-9 columns on wide screens. 
  - **Grid mode**: Uses virtualization for large lists, RAF-throttled.
  - **Table mode**: Non-virtualized, used for smaller lists (e.g., developers) to prevent flicker.
- **Asynchronous Operations**: Any task longer than 1s (e.g., registration, updates) must use the `JobManager` backend. The UI provides progress feedback via `NotificationCenter` in the navbar.
- **Dynamic MiniMaps**: Generated client-side using HERE Maps API. Supports retina scaling and dark mode switching without backend pre-generation.
- **Library Health Check**: Automatic consistency verification of `usi-scrapers` on startup. Status visible in the navigation drawer.
- **Error Boundaries**: Wrap key views and modules in `ModuleErrorBoundary` to isolate failures. UI errors are posted to `/api/ui-error` and logged to `logs/ui_errors.log`.

**Strict Load Order in `index.html`** (Dependency chain must be preserved):
1. `registry.js` (Plain JS module registry)
2. `theme.jsx` (Design tokens, `applyTheme()`)
3. `data.jsx` (`useInvestments()`, `DataBus` Context)
4. `components/atomic/Icon.jsx` & `Loading.jsx` (Primitives)
5. `components/ModuleErrorBoundary.jsx`
6. `components/DataGrid.jsx` (Virtualized grid)
7. `components/core.jsx` (`SourceBadge`, `StandardCard`, `NavDrawer`)
8. `components/ratings.jsx` (`StarRating`, `UsiStarScore`)
9. `modules/modules-core.jsx`, `modules-map.jsx`, `modules-charts.jsx`, `modules-ui.jsx`, `modules-test.jsx` (Analytical panels)
10. `components/analytics.jsx`, `components/Gallery.jsx`, `components/RatingsPanel.jsx`, `components/HeroBand.jsx`
11. `components/views/DetailViewA.jsx`, `DetailViewC.jsx`, `ListCard.jsx`
12. `capture-tool.js` & `test-regression.js` (Plain JS dev tools)
13. `view-*.jsx` (Specific application pages: detail, list, dev-list, reports, dashboard, etc.)
14. `app.jsx` (Root Application Shell)

### Data Ingestion & Scrapers
- **Portal Normalization**: Always normalize portal identifiers to `rp`, `oto`, or `to` in the API layer before routing or saving.
- **Portal Data Mapping (THE HOLY GRAIL OF PARSING)**: The library `usi-scrapers` uses `portal_data_mapping.json` to define complex extractions. It natively handles segmentation (`evaluate_signals`), transaction types (`rent`/`sale`), and custom data transformations (`transform`: `cm_to_m`, `clean_street`, `rp_extract_city`, etc.). 
  - 🚨 **CRITICAL RULE**: ALWAYS prioritize updating the JSON mapping in the library (`portal_data_mapping.json`) over writing manual parsing logic inside `python_worker/adapters/`. 
  - **The adapters should be kept as thin as possible**, serving only to assemble already clean data. If you catch yourself writing `if "m2" in value:` or `split(" ")[0]` inside `RPAdapter`, **STOP** and move that logic to `portal_data_mapping.json` via a new transform!
- **Discovery Enrichment**: Discovery results must include developer name and vendor slug to ensure correct automated folder mapping.
- **Raw Data Integrity**: Every registered investment must include a `raw_{portal}.json` file containing the complete original payload from the portal API. Mock raw files created by `init-devs` contain only IDs plus `"_mock": true`, which is automatically overwritten with full payload on a real scrape.
- **Slug Consistency**: Maintain strict consistency between `USIdata` folder names and `USI` asset folders.

## 🏗️ Core Architectural Mandates

1.  **Future Repo Split (Frontend/Backend)**: All design decisions must facilitate a future clean separation of the Python backend (API server) and the React frontend. Avoid tight coupling and ensure the API is pure REST.
2.  **Immutability of Portal Slugs**: Raw slugs and identifiers obtained from portals (RP, OTO, TO) are sacred and MUST NOT be modified within the USI system.
3.  **Scraper Delegation**: ALL data fetching from external portals MUST be performed exclusively through the `usi-scrapers` library. No direct portal I/O is allowed in `usi-tracker`.
4.  **Immutability of Raw Files**: Raw investment and developer JSON files downloaded from portals are immutable reference data. They must never be edited.
5.  **Precedence of Organized Files**: The system relies on "Umbrella" files (canonical unified JSONs: `usi_{inv_slug}.json`) that organize and aggregate information. These files take precedence over raw portal data for all business logic and UI presentation.

## 🧪 Testing Approach
- Use `pytest` for all backend logic.
- Mock all network calls using `requests-mock` or `curl_cffi` mocks — no real API calls in the test suite.
- Test files mirror module names (e.g., `test_scraper_rp.py`).
- Follow the fixture-builder helper pattern: private functions like `_make_rp_row()`, `_rp()`, `_oto()` must construct minimal valid dicts rather than utilizing large inline literals.
- **Optional Fixtures**: Tests guarded by `@pytest.mark.skipif(not PATH.exists(), ...)` are silently skipped when HTML/JSON reference files under `reference-data/` are absent. A fully green test run does not guarantee all tests executed.

## ⚠️ Known Constraints & Technical Debt
- **Otodom ID Instability**: Otodom frequently changes IDs; always rely on `USIfolder` (investment slug) as the stable key. Multiple CSV rows with the same `USIfolder` but different `otoID` represent the same investment across time; the last row wins.
- **Coordinate Order**: RP API uses `[longitude, latitude]` (GeoJSON order). Internal USI schema and separate fields use `[latitude, longitude]`.
- **Bot Detection**: Some portals (RP, OTO) have aggressive bot detection. Exploration via `Wedrowiec` uses throttled intervals and may require disabling ScraperAPI in favor of `curl_cffi` depending on current captcha levels.
- **Legacy Fallbacks**: `csv_importer.py` and `USImaster.csv` are legacy mechanisms and will be removed once the transition is complete.
- **Removed Modules**: `bus.py` (watchdog) has been removed; its functionality is handled by `main.py` and `ui_server.py`.
- **RP API `get_val()` Constraint**: The RynekPierwotny API wraps scalar values in `{"type": "...", "value": ...}` dicts. `adapters.py` exports `get_val(data, key, default=None)` to unwrap them. Any code reading RP API responses MUST use this helper; plain `data[key]` returns the wrapper dict, causing crashes.
- **Polish `ł` / `Ł` Slugs**: Python's `unicodedata.normalize("NFKD", ...)` fails to decompose the Polish stroke letter. `slug_utils.slugify()` applies `str.maketrans("łŁ", "lL")` first to prevent literal `ł` in directory names.
- **Image Source of Truth**: `image_paths` inside `usi_*.json` is the strict source of truth for the image API URLs. Never modify or guess these paths from `dev_slug` or folder structures. Fallback to filesystem directory scan is only permitted if `image_paths` is completely absent.
- **No Name-based Developer Fallback**: `InvestmentService` does not execute fuzzy-name fallback resolution via `get_developer_by_name()`. If ID lookup fails, the investment is assigned to the `"unknown"` folder immediately. Link developer by ID first.