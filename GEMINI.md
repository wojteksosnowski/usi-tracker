# USI Tracker - Gemini Context

USI Tracker is a specialized system for monitoring real-estate investments in Poland across multiple portals (**RynekPierwotny.pl**, **Otodom.pl**, and **TabelaOfert.pl**). It follows a CLI-first architecture with a high-density React-based local UI.

## 🚀 Project Overview

- **Purpose**: Automate the collection of investment data (prices, delivery dates, amenities, photos) and unify them into a canonical JSON format (`usi_*.json`).
- **Core Architecture**:
  - **Scrapers**: Specialized modules for each portal using direct API access (RP) or ScraperAPI/Impersonation (Otodom/TO).
  - **Adapters**: Transforms raw vendor-specific JSON into a unified USI schema.
  - **Data Store**: A file-based structure under `Public/USIdata/` organized by `{developer_slug}/{investment_slug}/`.
  - **UI**: A local Flask-served React application for high-density visualization and manual rating/annotation.
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
  - `ui/`: React frontend (Babel standalone).
  - `adapters.py`: Transformation logic (Unification).
  - `fetcher.py`: Abstraction for HTTP requests (Impersonation/ScraperAPI).
- `Public/USIdata/`: Canonical JSON records and metadata.
- `Public/USI/`: Downloaded investment images.
- `reference-data/`: Static snapshots and CSV source files.

### Raporty i Analizy
- **System raportowy**: Oparty na plikach JSON w `Public/USIdata/reports/`. Definiują one filtry inwestycji oraz moduły prezentacji (mapy, wykresy, tabele).
- **Szyna Danych (DataBus)**: System wymiany danych między niezależnymi komponentami (np. lista -> raport -> widżety). Zaimplementowany w `python_worker/ui/data.jsx` przy użyciu React Context. 
- **Moduły analityczne**: Reużywalne komponenty (np. `MapModule`, `PriceTrendModule`) osadzane w raportach i widokach szczegółowych. Wykorzystują Chart.js oraz HERE Maps API.

## ⚖️ Development Conventions

### Data Unification
- All new data must be processed through `RPAdapter`, `OtodomAdapter`, or `TOAdapter` before being merged via `Merger.merge`.
- **Slug Normalization**: Always use `slugify` (from `csv_importer.py`) to handle Polish characters (ł -> l) and ensure consistent folder names.

### UI Development (React 18)
- **No Bundler**: Files in `python_worker/ui/` are loaded directly in `index.html`.
- **Global Scope**: Components and hooks are shared via the global `window` object. Load order in `index.html` is critical for dependencies.
- **High Density**: UI with 16px/8px grids and virtualization for 6000+ records.

### Testing
- Use `pytest` for all backend logic.
- Mock all network calls using `requests-mock` or `curl_cffi` mocks.
- Test files mirror module names (e.g., `test_scraper_rp.py`).

## ⚠️ Known Constraints
- **Otodom ID Instability**: Otodom frequently changes IDs; always rely on `USIfolder` (investment slug) as the stable key.
- **Coordinate Order**: RP API uses `[longitude, latitude]`. Internal USI schema uses `[latitude, longitude]`. Be careful during conversion.
