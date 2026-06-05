# USI Tracker - Gemini Context

USI Tracker is a specialized system for monitoring real-estate investments in Poland across multiple portals (**RynekPierwotny.pl**, **Otodom.pl**, and **TabelaOfert.pl**). It follows a CLI-first architecture with a high-density React-based local UI.

## 🚀 Project Overview

- **Purpose**: Automate the collection of investment data (prices, delivery dates, amenities, photos) and unify them into a canonical JSON format (`usi_*.json`).
- **Core Architecture**:
  - **ID-only**: Universal rule - all identification must be derived from unique ID. Slug based identification is prohibitted.
  - **Ruthless**: Badź bezwgledny dla kodu, nie cackaj sie - tnij, usuwaj, pisz od nowa jezeli jest taka potrzeba. Kieruj sie zasada ID-only oraz obecnoscia API usi-scrapers.
  - **Identity Resolver (Resource Mapping)**: Centralized services (`InvestmentService.get_investment_resources`, `DeveloperManager.get_developer_resources`) that resolve physical file paths exclusively from USI IDs. All I/O operations must use these resolvers to avoid path drift caused by slug changes.
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

## 🛠 Building and Running

### Prerequisites
- Python 3.13+
- ScraperAPI key (for bypassing bot protection on some portals)
- HERE Maps API key (for map enrichment and POI fetch)

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r python_worker/requirements.txt
# Configure .env in python_worker/
```

### Key Commands
- **Start UI**: `./start-ui.sh` or `python3 -m python_worker.main ui`
- **Discover New Investments**: `python3 -m python_worker.main discover {dev_slug}`
- **Update Single Investment**: `python3 -m python_worker.main update-inv {dev_slug}/{inv_slug}`
- **Update Developer**: `python3 -m python_worker.main update-dev {dev_slug}`
- **Bulk Import (CSV)**: `python3 -m python_worker.main import-csv`
- **Backfill IDs**: `python3 -m python_worker.main backfill-ids` (assigns missing USI IDs)

## 📂 Directory Structure

- `python_worker/`: Main Python package.
  - `api/`: Flask API layer and Blueprints.
  - `adapters/`: Unified data transformation package.
  - `services/`: Core business logic layer.
  - `jobs.py`: Background task management (`JobManager`).
  - `crawler.py`: Unified crawler ("Wędrowiec").
  - `ui/`: React frontend (Babel standalone).
- `Public/USIdata/`: Canonical JSON records and investment metadata.
- `Public/USIdev/`: Developer profiles and merging metadata.
- `Public/USI/`: Downloaded investment images.
- `reference-data/`: Static snapshots and CSV source files.

### Raporty i Analizy
- **System raportowy**: Oparty na plikach JSON w `Public/USIdata/reports/`. Definiują one filtry inwestycji oraz moduły prezentacji (mapy, wykresy, tabele).
- **Szyna Danych (DataBus)**: System wymiany danych między niezależnymi komponentami (np. lista -> raport -> widżety). Zaimplementowany w `python_worker/ui/data.jsx` przy użyciu React Context. 
- **Moduły analityczne**: Reużywalne komponenty (np. `MapModule`, `PriceTrendModule`, `PoiModule`) osadzane w raportach i widokach szczegółowych. Wykorzystują Chart.js oraz HERE Maps API.

## ⚖️ Development Conventions

### Scraper Delegation & Library Architecture
- **No Local Scrapers**: Do NOT add new `scraper_*.py` files to `usi-tracker`. All portal interaction logic must reside in the `usi-scrapers` library. 
- `git clone https://wojteksosnowski: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@github.com/wojteksosnowski/usi-scrapers.git`
- **I/O Delegation**: Always use `TechnicalDataManager` from the library to save raw data or sync images. This prevents path drift and ensures consistent storage across environments.
- **Semantic Separation**: Keep data transformation (Adapters) and merging (Merger) in `usi-tracker`. The library provides "Technical Data," while the tracker creates "Business Data."
- **Path Resolution**: Avoid hardcoding paths like `Public/USIdata`. Use `config.public_dir` and library utilities to resolve paths.

### UI Development (React 18)
- **No Bundler**: Files in `python_worker/ui/` are loaded directly in `index.html`.
- **Global Scope**: Components and hooks are shared via the global `window` object. Load order in `index.html` is critical for dependencies.
- **Babel Standalone Race Conditions**: Extraction of variables from `window` (destructuring) MUST occur inside the component function (render-time), not at the module level.
- **Defensive Rendering**: Always use `safeRender` (validation `typeof === 'string' || 'number'`) when rendering API data to prevent "Objects are not valid as a React child" errors.
- **Shell Layout Pattern**: Centralize all view-specific controls (Search, Filters, Mode-Toggles, Actions) in the global `ActionBar`. Use the `DataBus` to manage shared state across navigation. Individual views should focus on data presentation only.
- **Expert UI (Density)**: UIs should prioritize information density. Use `DataGrid` with `minCardWidth` to achieve 7-9 columns on wide screens. 
  - **Grid mode**: Uses virtualization for large lists, RAF-throttled.
  - **Table mode**: Non-virtualized, used for smaller lists (e.g., developers) to prevent flicker.
- **Asynchronous Operations**: Any task longer than 1s (e.g., registration, updates) must use the `JobManager` backend. The UI provides progress feedback via `NotificationCenter` in the navbar.
- **Dynamic MiniMaps**: Generated client-side using HERE Maps API. Supports retina scaling and dark mode switching without backend pre-generation.
- **Library Health Check**: Automatic consistency verification of `usi-scrapers` on startup. Status visible in the navigation drawer.
- **Error Boundaries**: Wrap key views and modules in `ModuleErrorBoundary` to isolate failures.
- **UI Error Logging**: Critical errors are captured and sent to `/api/ui-error`, logged in `logs/ui_errors.log`.

### Data Ingestion & Scrapers
- **Portal Normalization**: Always normalize portal identifiers to `rp`, `oto`, or `to` in the API layer before routing or saving.
- **Portal Data Mapping (THE HOLY GRAIL OF PARSING)**: The library `usi-scrapers` uses `portal_data_mapping.json` to define complex extractions. It natively handles segmentation (`evaluate_signals`), transaction types (`rent`/`sale`), and custom data transformations (`transform`: `cm_to_m`, `clean_street`, `rp_extract_city`, etc.). 
  - 🚨 **CRITICAL RULE**: ALWAYS prioritize updating the JSON mapping in the library (`portal_data_mapping.json`) over writing manual parsing logic inside `python_worker/adapters/`. 
  - **The adapters should be kept as thin as possible**, serving only to assemble already clean data. If you catch yourself writing `if "m2" in value:` or `split(" ")[0]` inside `RPAdapter`, **STOP** and move that logic to `portal_data_mapping.json` via a new transform!
- **Developer Merging**: Use the `parent_id` model. Children records are filtered from main lists but retained for raw data integrity.
- **Discovery Enrichment**: Discovery results must include developer name and vendor slug to ensure correct automated folder mapping.
- **Raw Data Integrity**: Every registered investment must include a `raw_{portal}.json` file containing the complete original payload from the portal API.
- **Slug Consistency**: Maintain strict consistency between `USIdata` folder names and `USI` asset folders.

## 🏗️ Core Architectural Mandates

1.  **Future Repo Split (Frontend/Backend)**: All design decisions must facilitate a future clean separation of the Python backend (API server) and the React frontend. Avoid tight coupling and ensure the API is pure REST.
2.  **Immutability of Portal Slugs**: Raw slugs and identifiers obtained from portals (RP, OTO, TO) are sacred and MUST NOT be modified within the USI system.
3.  **Scraper Delegation**: ALL data fetching from external portals MUST be performed exclusively through the `usi-scrapers` library. No direct portal I/O is allowed in `usi-tracker`.
4.  **Immutability of Raw Files**: Raw investment and developer JSON files downloaded from portals are immutable reference data. They must never be edited.
5.  **Precedence of Organized Files**: The system relies on "Umbrella" files (canonical unified JSONs) that organize and aggregate information. These files take precedence over raw portal data for all business logic and UI presentation.

### Testing
- Use `pytest` for all backend logic.
- Mock all network calls using `requests-mock` or `curl_cffi` mocks.
- Test files mirror module names (e.g., `test_scraper_rp.py`).

## ⚠️ Known Constraints & Technical Debt
- **Otodom ID Instability**: Otodom frequently changes IDs; always rely on `USIfolder` (investment slug) as the stable key.
- **Coordinate Order**: RP API uses `[longitude, latitude]`. Internal USI schema uses `[latitude, longitude]`.
- **Bot Detection**: Some portals (RP, OTO) have aggressive bot detection. Exploration via `Wedrowiec` uses throttled intervals and may require disabling ScraperAPI in favor of `curl_cffi` (or vice versa) depending on current captcha levels.
- **Legacy Fallbacks**: `csv_importer.py` and `USImaster.csv` are legacy mechanisms and will be removed once the transition is complete.
- **Removed Modules**: `bus.py` (watchdog) has been removed; its functionality is handled by `main.py` and `ui_server.py`.
