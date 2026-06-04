# TODO

## Kamień 01 — Integracja TechnicalDataManager i Czyszczenie Serwisów

### Krok 01.01
Użycie TechnicalDataManager jako jedynego źródła prawdy o ścieżkach: Zamiast self.data_dir / dev_slug / inv_slug, wywołać metodę z managera biblioteki, która na podstawie ID (lub slugów) zwróci właściwy Path.

- [x] Zmodyfikować `python_worker/services/investment_identity.py`: usunąć manualne budowanie ścieżek `self.data_dir / dev_slug / inv_slug` w `_map_resources_from_entry`.
- [x] Zaimportować i zainicjalizować `TechnicalDataManager` z `usi-scrapers.manager` na podstawie `get_scraper_config()`.
- [x] Wykorzystać API `TechnicalDataManager` (np. `get_investment_path(usi_inv_id)`) do poprawnego ustalenia `inv_dir` i głównych plików.
- [x] Utworzyć zadanie testowe (`tests/test_investment_identity.py`) weryfikujące nowe zachowanie ścieżek.

**Podsumowanie:** Zmodyfikowano InvestmentIdentityResolver, aby korzystał z TechnicalDataManager i utils.io z pakietu usi_scrapers do dynamicznego ustalania ścieżek dostępu. Dodano metody get_investment_path i get_image_path do biblioteki. Utworzono test automatyczny potwierdzający nowe zachowanie.

### Krok 01.02
Wyczyszczenie InvestmentEditorService: Usunąć piętrowe if maybe_payload. Jeśli dostajemy slugi, biblioteka ma API, żeby zamienić je na ID i znaleźć folder.

- [ ] Zmodyfikować `InvestmentEditorService.save_ratings` w pliku `python_worker/services/investment_editor.py`.
- [ ] Usunąć logikę i branch `if maybe_payload is not None:` polegającą na ręcznym translokowaniu slugów.
- [ ] Wprowadzić natywne rozwiązywanie przez API `TechnicalDataManager.get_id_by_slug(dev_slug, inv_slug)`.
- [ ] Zweryfikować przejście istniejących testów lub utworzyć zadanie testowe dla zmienionej logiki `save_ratings`.

### Krok 01.03
Usunięcie "brudnych wstrzyknięć" w InvestmentSyncService: Biblioteka v0.9.7 posiada TechnicalDataManager, który potrafi zarządzać indeksem. Nie musimy mu "podpowiadać" slugami, jeśli rekord jest już znany.

- [ ] Zmodyfikować `python_worker/services/investment_sync.py`.
- [ ] Wyczyścić "brudne wstrzyknięcia" slugów tam, gdzie biblioteka v0.9.7 samodzielnie zarządza indeksem.
- [ ] Polegać bezpośrednio na `self.tech_manager` w klasie `InvestmentSyncService`.
- [ ] Utworzyć dedykowane zadanie testowe sprawdzające czystość wywołań w synchronizacji.



## Kamień 03 - Raw Inquisitor

### Krok 03.01
Przygotowanie listy wszystkich funkcji, które zapisują pliki na dysk, i zapis do pliku Markdown.
- [x] Zidentyfikować funkcje i metody dokonujące zapisu na dysk (np. `open(..., 'w')`, `Path.write_text`, `json.dump`) w katalogu `python_worker/services/` i `python_worker/api/`.
- [x] Zapisać znalezioną listę w nowym pliku `raw_io_usage_report.md`.
- [x] Utworzyć zadanie testowe weryfikujące wygenerowanie tego raportu.

**Podsumowanie:** Zidentyfikowano wszystkie funkcje wykonujące zapis na dysk i wygenerowano raport raw_io_usage_report.md. Dodano również test weryfikujący to zadanie.

### Krok 03.02
Weryfikacja uprawnień do zapisu plików na dysk i wskazanie nieuprawnionych wystąpień.
- [x] Przeanalizować funkcje wymienione w raporcie pod kątem łamania zasady "Brak lokalnych zapisów – używać API usi-scrapers".
- [x] Zaktualizować `raw_io_usage_report.md` o listę nieuprawnionych zapisów wraz z rekomendacjami refaktoryzacji.
- [x] Utworzyć test weryfikujący poprawność wykrywania łamania zasad zapisu plików w projekcie.

**Podsumowanie:** Zaktualizowano raport raw_io_usage_report.md o analizę poprawności użycia I/O oraz utworzono zadanie testowe dla weryfikacji tego kroku.

## Kamień 04 - Naprawa slug i I/O

### Krok 04.01
Naprawa nieuprawnionych wywołań slugów
- [x] Refaktoryzacja `python_worker/services/investment_sync.py` -> `_fetch_and_transform_portal_data`: usunąć operowanie na slug i użyć system_id.
- [x] Zmodyfikowanie testów dla `investment_sync.py`.

**Podsumowanie:** Zrefaktoryzowano metodę _fetch_and_transform_portal_data w InvestmentSyncService, aby przyjmowała system_id zamiast dev_slug i inv_slug, korzystając z InvestmentIdentityResolver do dynamicznego pozyskiwania ścieżek. Dodano test potwierdzający to zachowanie.

### Krok 04.02
Naprawa nieuprawnionych wywołań slugów (kontynuacja)
- [ ] Refaktoryzacja `python_worker/services/investment_loader.py` -> `load_investment`.
- [ ] Refaktoryzacja `python_worker/services/investment_identity.py` -> `get_investment_resources_by_slug`.
- [ ] Aktualizacja związanych z nimi testów jednostkowych.

### Krok 04.03
Naprawa nieuprawnionych zapisów na dysk (Raw I/O)
- [ ] Przenieść logikę zapisów z `investment_editor.py` (`mark_as_reviewed`, `save_ratings`) na odpowiednie warstwy abstrakcji.
- [ ] Zamienić w `investments.py` -> `download_raw_route` ręczny zapis na wywołanie z `usi-scrapers`.
- [ ] Uruchomić pełen pakiet testów w celu weryfikacji.


### Kamień 05
Poniżej znajduje się lista funkcji, które przyjmują argumenty zawierające słowo 'slug'.

- `crawler_api.py` -> `badge_reset`
- `discovery.py` -> `_run_with_event`
- `discovery.py` -> `discover_dev_new`
- `discovery_service.py` -> `_register_new_investment` - to powinno is po API i ID
- `discovery_service.py` -> `_save_discovery_snapshot` - to powinno is po API i ID
- `discovery_service.py` -> `discover_for_developer` - to powinno is po API i ID
- `discovery_service.py` -> `get_unregistered_count` - to powinno is po API i ID
- `image_resolver.py` -> `resolve_images` - to powinno is po API i ID
- `investment_identity.py` -> `get_investment_resources_by_slug` - co kurwa?! resolve by slug? Po co?
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
- `investment_sync.py` -> `download_raw_json` - to powinno robić API usi-scrapers
- `investment_sync.py` -> `register_investment`
- `investments.py` -> `_resolve_system_id`
- `investments.py` -> `dismiss_investment_suggestion`
- `investments.py` -> `dismiss_suggestion`
- `investments.py` -> `download_raw_route`
- `investments.py` -> `get_developer_detail`
- `investments.py` -> `investment_data`
- `investments.py` -> `mark_reviewed_legacy` - sprawdzic czy nie jest to zapomniany kod
- `investments.py` -> `merge_developer`
- `investments.py` -> `merge_investment`
- `investments.py` -> `refresh_investment_route`
- `investments.py` -> `reload_investment`
- `investments.py` -> `report_issue` - do usuniecia, i tak nie dziala
- `investments.py` -> `run_register_job`
- `investments.py` -> `save_deletion_list`
- `investments.py` -> `serve_dev_logo`
- `investments.py` -> `suggest_similar_investments`
- `investments.py` -> `unmerge_developer`
- `investments.py` -> `unmerge_investment`
- `poi.py` -> `_load_inv` - to powinno is po API i ID, poi jest wyszukiwane dla geopoint a nie dla slug!
- `poi.py` -> `_poi_path` - to powinno is po API i ID
- `poi.py` -> `fetch_poi` - to powinno is po API i ID
- `poi.py` -> `get_poi` - to powinno is po API i ID

Utworz zadanie dla kazdego naruszenia. Sprawdz czy jest ono uzasadnione. Staraj sie wykorzystywac jak najwiecej istniejacych funkcji i API. Zasada ID-only i thin-client. Zaplanuj testy.



### Kamień 14

# Zamiast:
def get_investment_resources_by_slug(dev_slug, inv_slug):
    # szukaj na dysku

# Powinno być:
def get_investment_resources(usi_inv_id):
    index = load_index()  # O(1)
    entry = index[usi_inv_id]
    return tech_manager.resolve_paths(entry["portal"], entry["portal_id"])

### Kamień 15 Identyfikacja nazwy dewelopera z URL
Python
# ❌ Tracker robi sam (python_worker/api/blueprints/investments.py):
developer_name = data.get("agency_name")  # Otodom
# lub ręczny scraping HTML

# ✅ API ma już:
from usi_scrapers.api import identify_developer
name = identify_developer(fetcher, portal="otodom", url="https://...")
Gdzie to siedzi w tracker: Głownie w logice discovery i podczas rejestracji — powinno być delegowane do usi-scrapers.

### Kamień 16 Geocodowanie adresu
Python
# ❌ Tracker robi sam (python_worker/here_maps.py):
def geocode_address(address: str):
    # Własna implementacja z HERE API

# ✅ Powinno być w usi-scrapers (lub dedykowanym serwisie)
# Tracker nigdy nie powinien wywoływać HERE API bezpośrednio
Problem: here_maps.py istnieje i jest used w python_worker/api/utils.py do wzbogacania wyników — to powinno być serwisem niezależnym, nie częścią trackera.

### Kamień 17 Zapis surowych danych
Python
# ❌ Tracker robi:
from python_worker.repair_image_paths import _resolve_paths
paths = _resolve_paths(raw_paths, image_urls, dev_slug, inv_slug, ...)

# ✅ Api usi-scrapers już ma:
from usi_scrapers.api import save_raw, save_raw_developer
save_raw(config, data, portal_prefix="rp", portal_id="123")
Tracker powinien: Wyłącznie wywoływać usi-scrapers API, nigdy nie pisać bezpośrednio do USIdata/.

### Kamień 18 

# python_worker/here_maps.py
# → Tego nie powinno być w tracker. Jeśli potrzebne, to jako oddzielny moduł.
# Tracker to FETCH-ONLY. Transformacje (takie jak HERE maps) to obowiązek aplikacji matki.

# python_worker/repair_image_paths.py → Cały plik
# Funkcje _find_by_* to heurystyka. Bez pewnych ID + portal_id = brak gwarancji.

# python_worker/investment_loader.py → find_inv_file()
# Zamienić na ID-based lookup:
# ZAMIAST: find_inv_file(dev_slug, inv_slug)
# POWINNO: identity.get_investment_resources(usi_inv_id) → files["anchor"]

### Kamień 19 

# python_worker/investment_identity.py
# ❌ get_investment_resources_by_slug(dev_slug, inv_slug)
# ✅ Tylko get_investment_resources(usi_inv_id)

# Jeśli brakuje ID, fail-fast + log do operacyjnego — nie fallback.

### Kamień 20

# python_worker/services/investment_sync.py
# ❌ Własny scraping dev name:
developer_name = data.get("agency_name")

# ✅ API:
from usi_scrapers.api import identify_developer
name = identify_developer(fetcher, portal, url)

# ❌ Własne zapisy raw:
# ✅ Delegować to usi-scrapers.api.save_raw()





### Kamień 99 Porządki
Po repo porozrzucane sa pliki nie majace zwiazku z dzialaniem repo. Wyczysc je.
