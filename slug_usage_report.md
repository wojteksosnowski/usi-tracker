# Raport z użycia slugów w funkcjach

Poniżej znajduje się lista funkcji, które przyjmują argumenty zawierające słowo 'slug'.

- `crawler_api.py` -> `badge_reset`
- `discovery.py` -> `_run_with_event`
- `discovery.py` -> `discover_dev_new`
- `discovery_service.py` -> `_register_new_investment`
- `discovery_service.py` -> `_save_discovery_snapshot`
- `discovery_service.py` -> `discover_for_developer`
- `discovery_service.py` -> `get_unregistered_count`
- `image_resolver.py` -> `resolve_images`
- `investment_identity.py` -> `get_investment_resources_by_slug`
- `investment_loader.py` -> `find_inv_file`
- `investment_loader.py` -> `load_investment`
- `investment_service.py` -> `download_raw_json`
- `investment_service.py` -> `get_investment`
- `investment_service.py` -> `mark_deleted_photos`
- `investment_service.py` -> `update_investment`
- `investment_sync.py` -> `_backfill_developer_mapping`
- `investment_sync.py` -> `_check_investment_exists`
- `investment_sync.py` -> `_fetch_and_transform_portal_data`
- `investment_sync.py` -> `_resolve_developer_for_registration`
- `investment_sync.py` -> `_sync_investment_images`
- `investment_sync.py` -> `download_raw_json`
- `investment_sync.py` -> `register_investment`
- `investments.py` -> `_resolve_system_id`
- `investments.py` -> `dismiss_investment_suggestion`
- `investments.py` -> `dismiss_suggestion`
- `investments.py` -> `download_raw_route`
- `investments.py` -> `get_developer_detail`
- `investments.py` -> `investment_data`
- `investments.py` -> `mark_reviewed_legacy`
- `investments.py` -> `merge_developer`
- `investments.py` -> `merge_investment`
- `investments.py` -> `refresh_investment_route`
- `investments.py` -> `reload_investment`
- `investments.py` -> `report_issue`
- `investments.py` -> `run_register_job`
- `investments.py` -> `save_deletion_list`
- `investments.py` -> `serve_dev_logo`
- `investments.py` -> `suggest_similar_investments`
- `investments.py` -> `unmerge_developer`
- `investments.py` -> `unmerge_investment`
- `poi.py` -> `_load_inv`
- `poi.py` -> `_poi_path`
- `poi.py` -> `fetch_poi`
- `poi.py` -> `get_poi`

## Analiza użycia i nieuprawnione wystąpienia
Większość powyższych funkcji używa sluga wyłącznie w warstwie rutingu (np. API blueprinty w `investments.py` i `discovery.py`), co jest dozwolone jako wejście systemu.
Nieuprawnione przekazywanie sluga do głębokich warstw (gdzie powinno być używane ID i API `usi-scrapers`) wykryto w:
1. `investment_sync.py` -> `_fetch_and_transform_portal_data`
2. `investment_loader.py` -> `load_investment`
3. `investment_identity.py` -> `get_investment_resources_by_slug`

Wnioski: Głębokie warstwy (usługi) powinny być zrefaktoryzowane, aby operować wyłącznie na system_id i resolverach z biblioteki usi-scrapers.
