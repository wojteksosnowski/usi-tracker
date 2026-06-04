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
Przygotuj liste wszystkich funkcji ktore zapisuja pliki na dysk. Zapisz te liste w pliku .md. Przygotuj zadanie sprawdzenia kazdej funkcji czy zapisywanie jest uprawnione i czy nie powinno byc zastapione przez API usi-scrapers. Jezeli nie jest uprawnione zapisz do pliku miejsca takich wystapien.
