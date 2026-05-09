# TODO

# TODO

## Bieżący kamień milowy: Naprawa przycisku Odśwież i stabilizacja

### Krok B01
**Plan:** 2026-05-09
- [x] Przeanalizować błędy "ScraperAPI fallback failed" widoczne w `logs/worker.log` oraz sprawdzić obecność pliku logu dla inwestycji `kopalniana-7`.
- [x] Zweryfikować, w jaki sposób błędy z biblioteki `usi-scrapers` (np. wyjątki API) są obsługiwane i logowane przez funkcję `update_investment` w `investment_service.py`.
- [x] Sprawdzić logikę przekazywania stanu zadania (`JobManager`) z backendu do UI w pliku `jobs.py`.
- [x] Utworzyć i uruchomić skrypt symulujący ręczne odświeżenie inwestycji ze szczegółowym logowaniem (`debug_update.py`), aby zidentyfikować w którym miejscu przerywane jest działanie (np. brak RAWjson).

**Podsumowanie:** Wykryto dwie przyczyny: (1) `scraper_api` w przypadku błędu (np. 500 od ScraperAPI) zwraca wynik bez klucza `raw_details`, przez co `update_investment` po cichu pomija procesowanie i zwraca `False`. (2) Główny problem: `JobManager` bezwarunkowo nadpisuje `message` na "Finished successfully." na końcu wywołania `wrapper()`, chyba że zostanie rzucony wyjątek. Przez to komunikat "Błąd odświeżania" jest natychmiast zamazywany, a UI interpretuje to jako sukces zadania.

### Krok B02
**Plan:** 2026-05-09
- [x] Poprawić logikę pobierania inwestycji w `investment_service.py`, by lepiej obsługiwała błędy HTTP (np. błędy 500 z ScraperAPI) bez całkowitego zrywania zadania. Błędy portali są teraz przechwytywane osobno; gdy wszystkie portale zawiodą, rzucany jest `RuntimeError` z czytelnym komunikatem.
- [x] Upewnić się, że po udanym pobraniu danych z wybranego portalu, zaktualizowany obiekt RAWjson jest poprawnie przekazywany i zapisywany w `TechnicalDataManager`. Zastąpiono tworzenie `DeveloperManager` bezpośrednim wywołaniem `self.tech_manager.save_raw_data()`.
- [x] Zweryfikować, dlaczego proces odświeżania nie wyzwala pobierania zdjęć. Dodano jawne ostrzeżenie gdy `tech_manager` jest None (brak `SCRAPERAPI_KEY`/config) oraz log sukcesu po zakończeniu `sync_images`.
- [x] Zintegrować zapis do logu inwestycji z dokładnym powodem braku RAWjson. Processing log zawiera teraz "Fetch failed — Portal: reason" oraz podsumowanie "Updated: …, Failed: …".

### Krok B03
Weryfikacja poprawki i upewnienie się, że zdjęcia pojawiają się w UI po odświeżeniu.
- [x] Przeprowadzić testowe odświeżenie inwestycji `kopalniana-7` via CLI (`update-inv`). Zidentyfikowano i naprawiono 3 dodatkowe bugi: (1) `identifier` dla Otodom preferował `id` zamiast `url`; (2) `OtodomAdapter._from_result` nie wyciągał `address/city/district/units_count` z `raw_details`; (3) `Merger` nie zachowywał pól `existing_data` gdy portal zwrócił null.
- [x] Zweryfikowano na dysku: `raw_oto_kopalniana-7.json` zapisany, 2 zdjęcia w `Public/USI/activ-investment-sp-z-oo/kopalniana-7/`, `usi_kopalniana-7.json` zawiera `address: ul. Kopalniana`, `city: Katowice`, `units_count: 48`, `images_count: 2`.
- [ ] Przeładować widok szczegółów w UI i zweryfikować renderowanie zdjęć (wymaga ręcznego testu).
- [x] Stworzono `test_refresh_e2e.py` (9 testów) pokrywający pełny pipeline: zapis raw, aktualizacja usi_json, wywołanie sync_images, zachowanie image_paths, zachowanie usi_ids, zachowanie istniejących danych, RuntimeError przy błędach portali, priorytet URL dla Otodom, priorytet ID dla RP.
## Następny kamień milowy: Moduł MiniMap - dynamiczne pobieranie i proporcje

## Przyszłe kamienie milowe

- Moduł MiniMap - moduł powinien brać swój rozmiar i pobierać mapę HERE zgodną z tym rozmiarem. Moduł ma stałą proporcję i elastyczną szerokość. Aby nie pobierac z duzo danych z HERE modul sprawdza czy jego rozmiar sie zmienił i nie czesciej niz 5 sekund pobiera mape pasujaca do szerokosci. W czasie elastycznej zmiany szerokosci mapa jest rozciagana do rozmiaru. Proporcja domyślna 3:1 ale moduł powinien akceptować zmienna wejsciową definiującą jego proporcję. Na mapie HERE wymusic pokazywanie pinezki w miejscu określonym przez lokalizacje. Moduł zachowuje dotychczasowe zachowanie wzgledem trybu light/dark

