# Raport z operacji I/O (zapis na dysk) w funkcjach

Poniżej znajduje się lista funkcji, które prawdopodobnie wykonują zapis na dysk (np. używają `open`, `write_text`, `json.dump`).

- `amenity_scorer.py` -> `load_wyrozniki`
- `common.py` -> `get_ui_config`
- `common.py` -> `log_ui_error_to_file`
- `discovery_service.py` -> `get_unregistered_count`
- `investment_editor.py` -> `add_report`
- `investment_editor.py` -> `mark_as_reviewed`
- `investment_editor.py` -> `mark_deleted_photos`
- `investment_editor.py` -> `save_ratings`
- `investment_sync.py` -> `_fetch_and_transform_portal_data`
- `investment_sync.py` -> `update_investment`
- `investments.py` -> `download_raw_route`
- `poi.py` -> `fetch_poi`

## Weryfikacja uprawnień do zapisu plików na dysk
Zgodnie z architekturą, wszystkie zapisy danych technicznych i surowych z portali powinny odbywać się przez bibliotekę `usi-scrapers`. Zapisy lokalne w trackerze są dozwolone jedynie dla konfiguracji UI, logów, oraz czystych danych biznesowych w ograniczonym stopniu.

**Nieuprawnione wystąpienia (do usunięcia lub zamiany na API biblioteki):**
1. `investment_editor.py` -> `mark_as_reviewed`, `save_ratings` - modyfikują pliki zamiast używać managera biznesowego z trackera (część I/O powinna być wydzielona).
2. `investment_sync.py` -> `_fetch_and_transform_portal_data` - zapis raw jsona, powinno używać `TechnicalDataManager.save_raw_data`.
3. `investments.py` -> `download_raw_route` - ręczne zapisywanie pobranych paczek, powinno przejść przez bibliotekę.

**Wnioski:** Znalezione nieuprawnione zapisy to głównie pozostałości starego kodu pobierającego dane surowe, który nie został zmigrowany do nowego `TechnicalDataManager`.
