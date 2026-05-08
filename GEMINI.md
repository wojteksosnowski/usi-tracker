# USI Tracker - Gemini Context

USI Tracker is a specialized system for monitoring real-estate investments in Poland across multiple portals (**RynekPierwotny.pl**, **Otodom.pl**, and **TabelaOfert.pl**). It follows a CLI-first architecture with a high-density React-based local UI.

## 🚀 Project Overview

- **Purpose**: Automate the collection of investment data (prices, delivery dates, amenities, photos) and unify them into a canonical JSON format (`usi_*.json`).
- **Core Architecture**:
  - **Thin-Client Scrapers**: ALL technical I/O, raw data fetching, and asset management (images) are delegated to the `usi-scrapers` library. The tracker acts as an orchestrator.
  - **TechnicalDataManager**: Centralized manager in `usi-scrapers` used for path resolution and technical data persistence.
  - **Adapters**: Transforms raw vendor-specific JSON into a unified USI schema. Located in `python_worker/adapters/` (Factory pattern).
  - **Service Layer**: Business logic encapsulated in `python_worker/services/` (`InvestmentService`, `DiscoveryService`). Focuses on semantic merging and ratings.
  - **Data Store**: A file-based structure under `Public/USIdata/` organized by `{developer_slug}/{investment_slug}/`.
  - **UI API**: Modular Flask Blueprints in `python_worker/api/blueprints/`.
  - **UI**: A local Flask-served React application for high-density visualization.
- **Integrations**: Syncs with Coda.io and Dropbox for distributed data access.

## 🛠 Building and Running

### Prerequisites
- Python 3.13+
- ScraperAPI key (for bypassing bot protection on Otodom/TO)
- HERE Maps API key (for map enrichment)

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

## 📂 Directory Structure

- `python_worker/`: Main Python package.
  - `api/`: Flask API layer and Blueprints.
  - `adapters/`: Unified data transformation package.
  - `services/`: Core business logic layer.
  - `jobs.py`: Background task management (`JobManager`).
  - `ui/`: React frontend (Babel standalone).
- `Public/USIdata/`: Canonical JSON records and metadata.
- `Public/USI/`: Downloaded investment images.
- `reference-data/`: Static snapshots and CSV source files.

### Raporty i Analizy
- **System raportowy**: Oparty na plikach JSON w `Public/USIdata/reports/`. Definiują one filtry inwestycji oraz moduły prezentacji (mapy, wykresy, tabele).
- **Szyna Danych (DataBus)**: System wymiany danych między niezależnymi komponentami (np. lista -> raport -> widżety). Zaimplementowany w `python_worker/ui/data.jsx` przy użyciu React Context. 
- **Moduły analityczne**: Reużywalne komponenty (np. `MapModule`, `PriceTrendModule`) osadzane w raportach i widokach szczegółowych. Wykorzystują Chart.js oraz HERE Maps API.

## ⚖️ Development Conventions

### Scraper Delegation & Library Architecture
- **No Local Scrapers**: Do NOT add new `scraper_*.py` files to `usi-tracker`. All portal interaction logic must reside in the `usi-scrapers` library.
- **I/O Delegation**: Always use `TechnicalDataManager` from the library to save raw data or sync images. This prevents path drift and ensures consistent storage across environments.
- **Semantic Separation**: Keep data transformation (Adapters) and merging (Merger) in `usi-tracker`. The library provides "Technical Data," while the tracker creates "Business Data."
- **Path Resolution**: Avoid hardcoding paths like `Public/USIdata`. Use `config.public_dir` and library utilities to resolve paths.

### UI Development (React 18)
- **No Bundler**: Files in `python_worker/ui/` are loaded directly in `index.html`.
- **Global Scope**: Components and hooks are shared via the global `window` object. Load order in `index.html` is critical for dependencies.
- **Babel Standalone Race Conditions**: Extraction of variables from `window` (destructuring) MUST occur inside the component function (render-time), not at the module level.
- **Defensive Rendering**: Always use `safeRender` (validation `typeof === 'string' || 'number'`) when rendering API data to prevent "Objects are not valid as a React child" errors.
- **Shell Layout Pattern**: Centralize all view-specific controls (Search, Filters, Mode-Toggles, Actions) in the global `ActionBar`. Use the `DataBus` to manage shared state across navigation. Individual views should focus on data presentation only.
- **Expert UI (Density)**: UIs should prioritize information density. Use `DataGrid` with `minCardWidth` to achieve 7-9 columns on wide screens. Virtualization logic must dynamically sync with responsive column counts.
- **Asynchronous Operations**: Any task longer than 1s (e.g., registration, updates) must use the `JobManager` backend. The UI must poll `/api/jobs` to provide progress feedback via `NotificationCenter`.
- **Error Boundaries**: Wrap key views and modules in `ModuleErrorBoundary` to isolate failures.
- **UI Error Logging**: Critical errors are captured and sent to `/api/ui-error`, logged in `logs/ui_errors.log`.
- **Dependency Guarding**: Before `ReactDOM.render`, verify all critical dependencies (React, DataBus, etc.) are present in `window`. Use recursive `setTimeout` if necessary.
- **Diagnostic Overlays**: Use global error listeners to display full-screen overlays for React "White Screen" errors.
- **Icon Fallbacks**: The `Icon` component must render a placeholder for missing keys to avoid rendering crashes.
- **Scroll Management**: Use `overflow-y: hidden` on parent containers when activating full-screen media modes to prevent double scrollbars.

### Data Ingestion & Scrapers
- **Portal Normalization**: Always normalize portal identifiers to `rp`, `oto`, or `to` in the API layer before routing or saving.
- **Discovery Enrichment**: Discovery results must include developer name and vendor slug to ensure correct automated folder mapping and prevent "Unknown Developer" records.
- **Raw Data Integrity**: Every registered investment must include a `raw_{portal}.json` file containing the complete original payload from the portal API (including galleries) to ensure future rebuild capability.
- **Slug Consistency**: Maintain strict consistency between `USIdata` folder names and `USI` asset folders. Avoid overwriting `developer_slug` within scrapers if a local slug has already been established.

### Testing
- Use `pytest` for all backend logic.
- Mock all network calls using `requests-mock` or `curl_cffi` mocks.
- Test files mirror module names (e.g., `test_scraper_rp.py`).

## ⚠️ Known Constraints & Technical Debt
- **Otodom ID Instability**: Otodom frequently changes IDs; always rely on `USIfolder` (investment slug) as the stable key.
- **Coordinate Order**: RP API uses `[longitude, latitude]`. Internal USI schema uses `[latitude, longitude]`.
- **Legacy Fallbacks**: `csv_importer.py` and `USImaster.csv` are legacy mechanisms for Coda.io data and will be removed once the transition to the new scraping architecture is complete.
- **Removed Modules**: `bus.py` (watchdog) has been removed; its functionality is handled by `main.py` and `ui_server.py`.
