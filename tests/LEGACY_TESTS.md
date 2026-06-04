# Legacy Tests Inventory

This report documents the purpose and coverage of the tests in the `tests/` directory before their removal as part of the architectural transition to ID-only and thin-client scrapers.

## Test Files and Purposes

| File | Purpose |
|------|---------|
| `compare_adapters.py` | Compares data output from different portal adapters. |
| `test_adapters_new.py` | Tests `RPAdapter`, `AdapterFactory`, and basic `Merger` functionality. |
| `test_api_refactor.py` | Tests API endpoints with Flask mocks, focused on refactored structure. |
| `test_api_reports_poi.py` | Tests Points of Interest (POI) data handling and reporting in the API. |
| `test_api_utils.py` | Unit tests for API utility functions. |
| `test_crawler_api.py` | Tests for the crawler management API endpoints. |
| `test_developer_manager.py` | Tests developer profile merging, parent/child relationships, and resource resolution. |
| `test_discovery_service.py` | Tests the discovery of new investments and basic registration flow. |
| `test_extraction_logic.py` | Deep verification of field extraction logic for RP, Otodom, and TabelaOfert. |
| `test_fix_segment_filter.py` | Verifies the logic for filtering investments by property segment. |
| `test_here_service.py` | Tests integration with HERE Maps API (geocoding, POI, maps) via `HereMapsService`. |
| `test_investment_identity.py` | Tests `InvestmentIdentityResolver` (early adoption of TechnicalDataManager). |
| `test_investment_merger_v3.py` | Tests the V3 logic for merging multiple portal records into a unified USI record. |
| `test_investment_service_optimizations.py` | Benchmarks and verifies performance optimizations in data loading. |
| `test_investment_service.py` | Core business logic tests for investment lifecycle (get, update, delete). |
| `test_investment_sync.py` | Tests the synchronization process between raw portal data and unified records. |
| `test_jobs.py` | Verifies `JobManager` lifecycle, background threading, and status tracking. |
| `test_merger.py` | Detailed tests for the core merging algorithm and field priority. |
| `test_migration_v3.py` | Tests data migration scripts and schema upgrades for V3. |
| `test_otodom_id_unification.py` | Specifically targets Otodom's unstable ID behavior and unification strategy. |
| `test_portal_matcher.py` | Tests fuzzy name matching, geographic distance (haversine), and candidate ranking. |
| `test_raw_io_analysis.py` | Meta-test for the tool that detects non-compliant direct disk writes. |
| `test_raw_io_report.py` | Verifies the generation and accuracy of the Raw I/O usage report. |
| `test_raw_metadata_extraction.py` | Tests low-level extraction of technical metadata from raw JSON files. |
| `test_refresh_e2e.py` | End-to-end regression tests for the full pipeline: Fetch -> Save -> Adapt -> Merge. |
| `test_resolution_choice.py` | Tests the logic for choosing specific values when portal data conflicts. |
| `test_rp_discovery_dedup.py` | Tests deduplication logic for RynekPierwotny discovery results. |
| `test_segment_classification.py` | Verifies classification of properties into Mieszkania, Domy, Działki, etc. |
| `test_segment_index_integrity.py` | Checks the health and consistency of segment-based search indices. |
| `test_slug_analysis.py` | Meta-test for the tool that detects legacy slug usage in the codebase. |
| `test_slug_report.py` | Verifies the generation and accuracy of the Slug usage report. |
| `test_stage_detector.py` | Tests the algorithm that detects and splits multi-stage investments from a single portal ID. |
| `test_suggestion_integration.py` | Tests the automated suggestion system for linking portal records. |
| `test_ui_server.py` | Tests Flask UI server logic, validation helpers, and static asset serving. |
| `test_url_parser.py` | Verifies parsing and normalization of portal URLs into internal identifiers. |

## Key Scenarios to Recreate

1. **Adapter Field Mapping**: Ensure that new tests thoroughly verify the `JsonPathExtractor` logic defined in `portal_data_mapping.json`.
2. **Identity Resolution**: Tests must verify that all file operations use `TechnicalDataManager` and USI IDs, never slugs.
3. **Merging Consistency**: Re-verify that merging portal data into `usi_unified.json` preserves critical metadata and correctly applies priority rules.
4. **Developer Relationship**: Re-implement tests for developer merging (`parent_id`) and logo resolution.
5. **E2E Ingestion**: A robust test that mocks `usi-scrapers` output and verifies the internal processing pipeline.
