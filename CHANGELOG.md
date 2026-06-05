# Changelog

## [Unreleased] - 2026-06-05
### Added
- Pre-calculated nearby investments in `usi_*.json` to improve frontend performance.
- Backend logic in `InvestmentSyncService` for spatial distance calculations.
- Migration script `scripts/backfill_distances.py` for historical data.
### Changed
- Updated `usi_unified.schema.json` to include `nearby_investments`.
- Refactored `view-detail.jsx` to remove expensive on-the-fly distance computations.

## Wersja 0.9.57 — Robustność ID i Sluga — 2026-06-05
- **Naprawa Błędu Odświeżania**: Wyeliminowano przyczynę błędu "Unexpected token '<'" podczas odświeżania inwestycji (np. INV-29863). Przyczyną był crash serwera (500) przy próbie parsowania brakujących slugów.
- **Odporny Loader**: Zaktualizowano `investment_loader.py`, aby automatycznie ekstrahował `portal` i `portal_id` z nazw plików, jeśli brakuje ich w zawartości JSON. Gwarantuje to poprawność indeksu nawet dla niepełnych rekordów.
- **Eliminacja Redundantnych Splitów**: Usunięto kruche i zbędne operacje `.split("/")` na slugach w całym systemie. Metadane `developer_slug` i `investment_slug` są teraz pobierane bezpośrednio z obiektów danych, co upraszcza kod i zwiększa jego stabilność.
- **Robust Identity Resolution**: Wprowadzono mechanizm fallback w `investment_identity.py`, który pozwala na znalezienie plików `usi_*.json` w folderze inwestycji nawet przy braku precyzyjnych informacji o portalu w indeksie.

## Wersja 0.9.56 — Optymalizacja Mechanizmu Cache — 2026-06-05
- **Rozdzielenie Czyszczenia Pamięci**: Całkowicie uniezależniono od siebie procesy czyszczenia cache brakujących obrazów (`_missing_images_cache`) oraz prawidłowych przekierowań CDN (`_cdn_redirect_cache`).
- **Eliminacja Cache Thrashing**: Zwiększono limit dla `_cdn_redirect_cache` do 100 000 wpisów, zachowując limit 5 000 dla brakujących plików. Zapobiega to niepotrzebnemu czyszczeniu wartościowych danych przy dużej liczbie błędów 404, drastycznie zmniejszając obciążenie CPU i dysku podczas ponownych żądań o te same zasoby.

## Wersja 0.9.55 — Fix `detect_similar_invs.py` — 2026-06-05
- **Naprawa Błędu Zmiennych**: Rozwiązano problem `NameError` wynikający z użycia niezdefiniowanych zmiennych `dev_slug` i `inv_slug` w skrypcie wykrywania podobnych inwestycji.
- **Optymalizacja Indeksowania**: Zaktualizowano wywołanie `inv_index.upsert`, aby korzystało z systemowego identyfikatora `inv_id`, co jest zgodne z architekturą ID-only.
- **Korekta Formatowania**: Naprawiono niepoprawne wcięcia (indentation) w głównej pętli skryptu, poprawiając czytelność i stabilność kodu.

## Wersja 0.9.54 — Centralizacja Inicjalizacji Biblioteki — 2026-06-05
- **Współdzielone Instancje**: Wprowadzono wzorzec singleton-like dla kluczowych obiektów biblioteki `usi-scrapers` (`ScraperConfig`, `TechnicalDataManager`, `Fetcher`). Są one teraz inicjowane raz w `config.py` i współdzielone między wszystkimi serwisami.
- **Refaktoryzacja InvestmentSyncService**: Oczyszczono szkielet serwisu synchronizacji, opierając zarządzanie obiektami `Fetcher` i `TechnicalDataManager` w 100% o ujednolicony wzorzec współdzielony. Usunięto redundantne instancje tworzone przy każdym żądaniu.
- **Poprawa Stabilności Importów**: Rozwiązano problemy z kolejnością inicjalizacji `sys.path`, zachowując bezpieczne importy lokalne dla biblioteki zewnętrznej, jednocześnie upraszczając logikę getterów i setterów.
- **Optymalizacja Wydajności**: Redukcja narzutu na wielokrotne tworzenie obiektów managera i konfiguracji, co przekłada się na mniejsze zużycie pamięci i szybszy start usług.

### Wnioski ze zmian
- Centralizacja zasobów technicznych jest kluczowa dla architektury "Thin-Client". Dzięki współdzieleniu instancji `TechnicalDataManager`, system ma jeden, autorytatywny punkt styku z warstwą I/O, co eliminuje ryzyko niespójności konfiguracji między różnymi częściami aplikacji.

## Wersja 0.9.53 — Bezkompromisowe ID-ONLY — 2026-06-05
- **Eliminacja Slugów w I/O**: Usunięto ostatnie bastiony identyfikacji po slugach w warstwie zapisu surowych danych. Funkcje `save_raw` i `save_raw_developer` korzystają teraz wyłącznie z `portal_id`, zgodnie z wymogami `usi-scrapers` v0.7.0+.
- **Refaktoryzacja Facade**: Zastąpiono amatorskie `*args, **kwargs` w `DeveloperManager` jawnymi sygnaturami metod, co zwiększa stabilność i ułatwia debugowanie.
- **Aktualizacja Testów**: Dostosowano asercje w `tests/test_raw_saving.py` do nowej architektury, eliminując fałszywe oczekiwania względem slugów.

### Wnioski ze zmian
- Architektura ID-only jest teraz egzekwowana na każdym poziomie delegacji do biblioteki. Usunięcie niejawnych parametrów (`**kwargs`) w fasadach zapobiega "cichemu" przekazywaniu nielegalnych slugów, które powodowały błędy typu `TypeError`.

## Wersja 0.9.52 — Optymalizacja O(1) dla obrazów — 2026-06-05
- **Wydajność API**: Zastąpiono powolne wyszukiwanie podciągów (substring matching) przez szybkie mapowanie słownikowe (dictionary lookup) w funkcji `serve_image`, co drastycznie skraca czas fallback-u dla brakujących obrazów (O(1) zamiast O(N)).
- **Zarządzanie Pamięcią**: Wdrożono rygorystyczne czyszczenie cache (`_missing_images_cache` oraz `_cdn_redirect_cache`) po przekroczeniu limitu 5000 wpisów, co zabezpiecza serwer przed wyciekami pamięci przy długotrwałym działaniu.

### Wnioski ze zmian
- Dzięki prekompilacji list obrazów do słowników uniknięto zbędnych pętli w obszarach krytycznych dla wydajności (serwowanie zasobów). Regularne czyszczenie cache jest konieczne dla systemów działających w tle, by utrzymać stałe użycie pamięci bez spowolnienia odpowiedzi.

## Wersja 0.9.51 — Kamień 04 (Optymalizacja skanowania dysku dla obrazów) — 2026-06-05
- **Wydajność API**: Wyeliminowano rutynowe, pełne skanowanie folderu inwestycji przy rozwiązywaniu obrazów w `image_resolver.py`.
- **Zmiana logiki `_scan`**: Operacja `glob`/iterdir została zdegradowana do roli ścisłego fallback-u, uruchamiającego się wyłącznie, gdy zapisane w plikach konfiguracyjnych ścieżki do obrazów (`image_paths_raw`) są nieskuteczne lub nie istnieją.

### Wnioski ze zmian
- Dzięki przesunięciu kosztownego skanowania dysku I/O tylko dla przypadków brzegowych, uzyskano redukcję czasu odpowiedzi przy serwowaniu pojedynczych inwestycji przez endpoint API.

## Wersja 0.9.50 — Kamień 03 (Refaktoryzacja mapowania portali) — 2026-06-05
- **Konfiguracja strukturalna**: Wprowadzono słowniki konfiguracyjne (`PORTAL_NAMES`, `PORTAL_FULL_DOMAINS`, `PORTAL_VENDOR_ID_KEYS`) do zarządzania logiką w zależności od portalu (rp, oto, to).
- **Czyszczenie instrukcji warunkowych**: Zrefaktoryzowano pętlę synchronizacji w `InvestmentSyncService`, zastępując bloki `if/elif` mechanizmami Dispatch Maps, co ujednolica i stabilizuje przepływ danych.

### Wnioski ze zmian
- Stosowanie mapowań słownikowych zamiast rozbudowanych i powtarzalnych instrukcji warunkowych drastycznie redukuje stopień skomplikowania kodu, zmniejsza ryzyko błędów przy ręcznej edycji i sprawia, że integracja ewentualnych przyszłych źródeł danych będzie opierać się o proste wpisy w rejestrze mapowań.

## Wersja 0.9.49 — Kamień 02 (Rejestracja inwestycji ID-only) — 2026-06-05
- **Wzmocnienie ID-only**: Usunięto całkowicie parametr `inv_slug` z sygnatury i logiki metody `register_investment`, przenosząc pełny środek ciężkości na `item_id`.
- **Integracja API**: Oczyszczono logikę endpointów oraz serwisu Discovery, optymalizując w nich zapytania na rzecz bazowania wyłącznie na identyfikatorach dostarczanych przez bibliotekę wewnętrzną.

### Wnioski ze zmian
- Rezygnacja ze sluga w logice rejestrowania nowych elementów znacząco poprawia przewidywalność zachowań systemu. Wcześniejsze poleganie na nim powodowało ciche tworzenie się rozbieżności, gdy platformy takie jak Otodom niejawnie podmieniały URL-e.

## Wersja 0.9.48 — Kamień 01 (Refaktoryzacja weryfikacji inwestycji) — 2026-06-05
- **Wzmocnienie ID-only**: Usunięto parametr `inv_slug` i stare mechanizmy weryfikacyjne, opierając `_check_investment_exists` natywnie o wywołanie `get_raw_data` z `usi-scrapers`.
- **Aktualizacja testów**: Oczyszczono i zaktualizowano mocki i argumenty w pliku `scratch_test.py` oraz upewniono się, że pozostałe testy nie wymagają modyfikacji sygnatur.

### Wnioski ze zmian
- Eliminacja `inv_slug` z procesów weryfikacyjnych domyka kolejną dziurę architektoniczną pozwalając na w pełni deterministyczne sprawdzanie duplikatów oparte na oryginalnych identyfikatorach dostawców.

## Wersja 0.9.47 — Kamień 07 i 08 (Wydajność POI i Oczyszczenie ID) — 2026-06-05
- **Optymalizacja stabilności**: Usunięto przestarzałą metodę iterującą za pomocą `glob` po całym dysku w poszukiwaniu brakujących obrazów POI, co wyeliminowało błędy TimeOut oraz blokowanie CPU (Kamień 07).
- **Zabezpieczenie widoku**: Dodano `ModuleErrorBoundary` chroniący front-endową galerię przed wyjątkami.
- **Wzmocnienie ID-only**: Usunięto szukanie po starym `inv_slug` w `_check_investment_exists` przy deduplikacji rekordów w Otodom.

### Wnioski ze zmian
- Legacy fallbacks mogą stać się bombą zegarową: metoda, która miała za zadanie "tylko pomóc" przy braku zasobów (skan nazwy pliku), potrafiła zablokować działanie całej aplikacji przy wielotysięcznej bazie. Zawsze należy egzekwować architekturę `ID-only`.

## Wersja 0.9.46 — Kamień 06 (Uproszczenie process_batch) — 2026-06-05
- **Poprawa czytelności kodu**: Zrefaktoryzowano skomplikowaną metodę `process_batch` w `InvestmentSyncService`, wydzielając logikę parsowania i uzupełniania danych do zwięzłego helpera `_merge_batch_info`.

### Wnioski ze zmian
- Ograniczenie długu technicznego: Pozbycie się kilkudziesięciu linijek duplikowanej logiki z pętli optymalizuje czytelność i pozwala skupić główną metodę procesowania jedynie na wywołaniach rejestrujących. Używanie mniejszych metod (helperów) podnosi testowalność platformy i zmniejsza ryzyko pomyłek.

## Wersja 0.9.45 — Kamień 05 (Wydzielenie DeveloperResolver) — 2026-06-05
- **Hermetyzacja logiki domenowej**: Usunięto odpowiedzialność za rozwiązywanie profilów i mapowań deweloperów z serwisu głównego, zamykając ją w nowym komponencie `DeveloperResolver`.

### Wnioski ze zmian
- Architektura oparta o SRP: Krok ten stanowi kontynuację porządkowania masywnej klasy `InvestmentSyncService`. Oddzielenie identyfikacji developerów sprawia, że główny serwis odpowiada teraz tylko za wysokopoziomową orkiestrację przepływu synchronizacji.

## Wersja 0.9.44 — Kamień 04 (Wydzielenie ImageSyncService) — 2026-06-05
- **Refaktoryzacja struktury**: Usunięto powiązania logiki synchronizacji zdjęć z `InvestmentSyncService` i wydzielono do odrębnej usługi `ImageSyncService` w nowym pliku `image_sync.py`.

### Wnioski ze zmian
- Architektura oparta o zasadę pojedynczej odpowiedzialności (SRP): Zmniejszenie "couplingu" w głównym kontrolerze na rzecz wyspecjalizowanych mikrousług ułatwia testowanie oraz zmniejsza ryzyko regresji przy modyfikacjach.

## Wersja 0.9.46 — Kamień 04 (Wydzielenie ImageSyncService - Krok 04.01) — 2026-06-05
- **Wydzielenie logiki**: Utworzono `ImageSyncService` w `python_worker/services/image_sync.py` i przeniesiono do niej logikę metody `_sync_investment_images` z `InvestmentSyncService`. Poprawiono inicjalizację.
- Zaktualizowano `TODO.md`: Oznaczono zadania Kroku 04.01 jako wykonane i dodano podsumowanie.

## Wersja 0.9.45 — Kamień 04 (Rozpakowanie zadań) — 2026-06-05
- Zaktualizowano `TODO.md` aby dokładnie rozpakować zadania dla Kamienia 04 (Wydzielenie ImageSyncService) oraz dodano zarysy Kamieni 05 i 06.

## Wersja 0.9.43 — Kamień 03 (Weryfikacja odpowiedzialności za pobieranie obrazków) — 2026-06-05
- **Weryfikacja integracyjna**: Potwierdzono, że logika pobierania zasobów graficznych (zdjęć) w serwisie `InvestmentSyncService` nie zawiera samodzielnych wywołań HTTP. Proces jest prawidłowo delegowany do obiektu `tech_manager` (z zewnętrznej biblioteki `usi-scrapers`).

### Wnioski ze zmian
- Centralizacja odpowiedzialności: Pozostawienie operacji I/O i zarządzania mediami w bibliotece `usi-scrapers` gwarantuje jednolitość struktury pobierania. Kod `usi-tracker` aktualnie spełnia reguły ścisłego oddzielenia logiki biznesowej od logiki scrapowania.

## Wersja 0.9.44 — Kamień 03 (Inspekcja kodu synchronizacji zdjęć - Krok 03.01) — 2026-06-05
- **Weryfikacja obrazków**: Przeprowadzono inspekcję kodu `python_worker/services/investment_sync.py`. Potwierdzono, że logika pobierania zdjęć nie używa bezpośrednio bibliotek HTTP (np. requests) i prawidłowo deleguje to zadanie do `usi-scrapers` (`tech_manager.sync_images`). Zaktualizowano odpowiednio `TODO.md`.

## Wersja 0.9.43 — Aktualizacja TODO.md — 2026-06-05
- Zaktualizowano plik `TODO.md` o szczegółowe kroki weryfikacji odpowiedzialności za pobieranie obrazków w ramach zadania (Kamień 03).

## Wersja 0.9.42 — Kamień 02 (Opanowanie wycieku stanu UI oraz integracja POI z USI JSON) — 2026-06-05
- **Poprawa wycieku stanu indeksu zdjęć**: Naprawiono błędną zależność `inv.slug` na poprawną `inv.usi_inv_id` w widoku szczegółów. Poprawia to odświeżanie zdjęć po zmianie inwestycji.
- **Integracja zapisu POI do JSON**: Zmodyfikowano `poi.py` by czytał i zapisywał POI (Places of Interest) jako węzeł w głównym pliku inwestycji (`usi_*.json`), upraszczając strukturę danych i eliminując niepotrzebne zapytania asynchroniczne.

### Wnioski ze zmian
- Migracja pobocznych danych jak POI do rdzennnego obiektu inwestycji (master JSON) zwiększa spójność danych i ogranicza liczbę niezbędnych odpytań i plików. 
- Zawsze należy zachować czujność przy zależnościach hooków React, polegając na pewnych identyfikatorach systemowych (jak `usi_inv_id`), by uniknąć asynchronicznych wycieków stanu pomiędzy komponentami.

## Wersja 0.9.41 — Kamień 01 (Pierwszy blad UI) — 2026-06-05
- **Poprawa błędu UI**: Rozwiązano problem `ReferenceError: investment is not defined` w widokach, naprawiając błędne użycie nazwy zmiennej w module odpowiedzialnym za punkty POI (`modules-ui.jsx`).

### Wnioski ze zmian
- Konsekwentne stosowanie ujednoliconych nazw zmiennych (np. `inv` zamiast `investment`) w parametrach i właściwościach komponentów pomaga unikać błędów referencji i przerw w działaniu interfejsu.

## Wersja 0.9.40 — Czystka TODO — 2026-06-05
- **Wyczyszczenie TODO**: Usunięto zrealizowane zadania.

### Wnioski ze zmian
- Oczyszczenie TODO po udanym wdrożeniu przygotowuje przestrzeń do planowania kolejnych zadań.

## Wersja 0.9.39 — Kamień 23 (Testy API UI) — 2026-06-04
- **Testy API**: Wprowadzono plik testowy `tests/test_api_endpoints.py` weryfikujący poprawność ładowania wszystkich wystawionych dla interfejsu webowego (UI) endpointów (w tym `config`, `metadata-config`, `investments`, `developers`).

### Wnioski ze zmian
- Obudowanie endpointów UI testami gwarantuje wczesne wykrycie ewentualnych uszkodzeń ścieżek dostępowych (Blueprints) na poziomie interfejsu przed użyciem produkcyjnym.
## Wersja 0.9.38 — Kamień 22 (Aktualizacja biblioteki) — 2026-06-04
- **Aktualizacja zależności**: Podniesiono wersję biblioteki `usi-scrapers` do `0.9.8`, która wprowadza odporność i wsparcie fallback dla pobierania zdjęć (błędne ścieżki).
- **Testy**: Usprawniono i zweryfikowano testy integracyjne po aktualizacji.

### Wnioski ze zmian
- Dzięki bieżącym aktualizacjom zewnętrznych paczek, tracker sprawniej radzi sobie z niedoskonałościami po stronie portali ogłoszeniowych (brakujące obrazki) bazując na mechanizmach biblioteki.

## Wersja 0.9.37 — Kamień 21 (Wielkie sprzątanie martwego kodu i CLI) — 2026-06-04
- **Usunięcie legacy skryptów**: Wyczyszczono repozytorium z nieużywanych, jednorazowych skryptów refaktoryzacyjnych (m.in. `mass_update_rp.py`, `verify_ingestion.py`, `ui_baseline_helper.py`).
- **Oczyszczenie CLI**: Z usuniętego już w poprzednich wersjach pliku `audit_worker.py` usunięto pozostałości w parserze `main.py` (komendy `run-audit`, `migrate`), zdejmując z CLI warstwę martwego kodu. 

### Wnioski ze zmian
- Cykliczne audytowanie i usuwanie "narzędziówek" typu "one-off script" podnosi czytelność repozytorium i zmniejsza jego dług techniczny na rzecz utrzymania solidnej struktury docelowej.

## Wersja 0.9.36 — Kamień 20 (Wyeliminowanie logiki I/O z procesu Sync) — 2026-06-04
- **Scraping**: Usunięto lokalną logikę odczytu nazw dewelopera. System polega teraz całkowicie na API biblioteki `usi-scrapers` (`identify_developer`), zachowując w ten sposób pełną separację od mechanizmów zewnętrznych struktur domów ogłoszeniowych.
- **Oddelegowanie zapisu (I/O)**: Oczyszczono tracker z wewnętrznych procedur zapisujących surowy ładunek RAW; korzysta on wyłącznie z interfejsu API do persystencji ustrukturyzowanych danych, zamykając ścieżkę generowania śmieciowych katalogów dla błędnych ID.

### Wnioski ze zmian
- Dzięki delegacji operacji parsowania surowych atrybutów i logiki zapisu surowych ładunków na zewnątrz (I/O), tracker stał się o wiele lżejszy. Warstwa synchronizacji odpowiada już tylko za zawiadowanie modelami biznesowymi i obsługą relacji między obiektami w domenie.
## Wersja 0.9.35 — Kamień 19 (Ostateczne wymuszenie polityki ID-only) — 2026-06-04
- **Identity Resolver**: Ostatecznie zweryfikowano brak użycia funkcji `get_investment_resources_by_slug`. Rezolucja zasobów odbywa się wyłącznie na bazie systemowych identyfikatorów.
- **Odporność i Fail-Fast**: System ładujący inwestycje rygorystycznie zgłasza błędy w przypadku przekazania zdezaktualizowanych kluczy opartych na slugach, unikając ryzykownych zachowań typu fallback.

### Wnioski ze zmian
- Architektura oparta o systemowe identyfikatory jest teraz szczelna. Gwarantuje to spójność operacji oraz chroni przed sytuacjami, w których dynamiczne zmiany slugów po stronie portali ogłoszeniowych prowadziły do rozszczepienia rekordów.
## Wersja 0.9.34 — Kamień 18 (Przeniesienie logiki obrazów i optymalizacja lookupów) — 2026-06-04
- **Refaktoryzacja lookupów**: Ostatecznie zweryfikowano i przypieczętowano usunięcie logiki `find_inv_file(dev_slug, inv_slug)` na rzecz wyłącznego korzystania z systemowych identyfikatorów z wykorzystaniem mechanizmów tożsamości.
- **Delegacja logiki I/O**: Usunięto lokalne, zawodne heurystyki naprawy ścieżek obrazków (`_find_by_*`), przerzucając odpowiedzialność za to zadanie do biblioteki `usi-scrapers`.

### Wnioski ze zmian
- Oczyszczenie USI Trackera z mechanizmów naprawczych I/O ugruntowuje jego pozycję jako warstwy orchestracji danych, pozostawiając szczegóły komunikacji technicznej dedykowanej bibliotece.

## Wersja 0.9.33 — Kamień 06 (Ostateczne wyparcie slugów i porządki) — 2026-06-04
- **ID-Only Finalization**: Całkowicie wyeliminowano funkcję `find_inv_file` i powiązane z nią aliasy. System lokalizuje teraz wszystkie zasoby wyłącznie poprzez systemowe identyfikatory ID.
- **Wielkie sprzątanie**: Usunięto ponad 20 przestarzałych skryptów migracyjnych, audytowych i narzędziowych (`migrate*`, `audit*`, `fix*`) oraz katalogi śmieciowe (`scratch`, `forgettable`, `tmp_USIdev`).
- **Stabilizacja testów**: Zaktualizowano testy integracyjne w celu dopasowania ich do nowej, odchudzonej architektury.
- **Optymalizacja I/O**: Usunięto moduł `repair_image_paths.py`, kończąc erę heurystyk opartych na slugach.

### Wnioski ze zmian
- Tracker osiągnął stan docelowy: jest "cienkim" klientem, delegującym całe techniczne I/O do biblioteki `usi-scrapers`. Usunięcie długu technicznego w postaci skryptów legacy drastycznie poprawia czytelność repozytorium i ułatwia wdrożenie nowych deweloperów.

## Wersja 0.9.32 — Kamień 05 (Wielka czystka slugów w systemie) — 2026-06-04
- **ID-Only API & Frontend**: Zaktualizowano wszystkie trasy Flask w `investments.py` oraz `crawler_api.py` do obsługi unikalnych identyfikatorów `system_id`, jednocześnie synchronizując całą warstwę React.
- **Refaktoryzacja Serwisów**: Warstwy Discovery, Sync i Image Resolver zostały całkowicie uniezależnione od parametrów slug.
- **POI Migration**: Moduł POI korzysta teraz z `poi.json` wewnątrz kanonicznych katalogów inwestycji.
- **Cleanup**: Usunięto przestarzałe i niedziałające fragmenty kodu (`report_issue`, `mark_reviewed_legacy`).
- **Testy**: Dodano nowe pakiety testów dla Discovery (`test_discovery_service.py`), POI (`test_poi_api.py`) oraz Loadera inwestycji (`test_investment_loader.py`).

### Wnioski ze zmian
- System jest teraz gotowy na przyszłe rozszerzenia i separację repozytoriów, będąc w pełni odpornym na zmiany identyfikatorów tekstowych w portalach ogłoszeniowych. Scentralizowanie całej rezolucji w `TechnicalDataManager` i ID-only Resolverach zamyka rozdział architektury opartej na heurystykach slugów.

## Wersja 0.9.31 — Kamień 04 (Naprawa slug i I/O) — 2026-06-04
- **Refaktoryzacja load_investment**: Usunięto fallback w `investment_loader.py` polegający na budowaniu ścieżek z użyciem slugów, zmuszając do twardej rezolucji poprzez ID.
- **Audyt Legacy API**: Potwierdzono, że nieuprawnione zapisy na dysk oraz użycie przestarzałych metod w `investment_editor.py` i `investments.py` zostały całkowicie zmigrowane w poprzednich wersjach.
- **Dodanie testów**: Stworzono `test_investment_loader.py`, który weryfikuje poprawność odrzucania operacji z brakującymi systemowymi tożsamościami.

### Wnioski ze zmian
- Ujednolicanie całego systemu w stronę "ID-only" ogranicza luki dla rzadkich brzegowych wariantów. Zamknięcie furtki z przestarzałą rezolucją plików uodparnia tracker na potencjalnie niestabilną zmianę identyfikatorów slug ze strony portali ogłoszeniowych.

## Wersja 0.9.30 — Kamień 03 (Raw Inquisitor) — 2026-06-04
- **Audyt Zapisów (Raw I/O)**: Wygenerowano raport `raw_io_usage_report.md` wskazujący wszystkie funkcje dokonujące lokalnego zapisu w systemie.
- **Weryfikacja Uprawnień**: Zaktualizowano raport o listę nieuprawnionych wywołań naruszających architekturę "Thin-Client", ze wskazówkami do refaktoryzacji.
- **Testy**: Upewniono się, że procedury audytujące I/O działają poprawnie i są weryfikowalne.

### Wnioski ze zmian
- Zmapowanie wszystkich punktów zapisu ułatwi nam planowanie następnych kroków czyszczenia trackera, zapobiegając dalszemu łamaniu zasady delegacji do biblioteki. Pozwala to na bardziej świadomą migrację nieuprawnionych operacji IO do `usi-scrapers`.

## Wersja 0.9.29 — Kamień 01 (Integracja TechnicalDataManager i Czyszczenie Serwisów) — 2026-06-04
- **ID-Only Resolution**: `InvestmentIdentityResolver` został zintegrowany z `TechnicalDataManager`, całkowicie eliminując ręczne budowanie ścieżek na podstawie slugów.
- **Wyczyszczenie Serwisów**: Usunięto logikę fallbacków w `InvestmentEditorService.save_ratings` i zaktualizowano oznaczanie rekordów.
- **Refaktoryzacja SyncService**: Zmodyfikowano `register_investment` i synchronizację obrazów w `InvestmentSyncService`, aby używały poprawnie ścieżek z biblioteki.
- **Aktualizacje Indeksu**: Wymuszono wywoływanie `upsert` w indeksie przy użyciu `inv_id`, co zapobiega dublowaniu wpisów z różnymi slugami.
- **Testy**: Dodano czyste przypadki testowe w `test_investment_sync_clean.py` i naprawiono brakujące właściwości mocków `ScraperConfig`.

### Wnioski ze zmian
- Architektura oparta na tożsamościach ID, a nie na slugach, drastycznie zmniejsza złożoność logiki w serwisach aplikacyjnych. Przesunięcie całej odpowiedzialności za struktury plików do `TechnicalDataManager` usuwa luki bezpieczeństwa i zjawisko tzw. "dryfu ścieżek". Zmiany te są krytyczne w kontekście stabilności środowiska.

## Wersja 0.9.28 — Kamień 17 (Zapis surowych danych) — 2026-06-04
- **Delegacja zapisu Raw I/O**: Zastąpienie `TechnicalDataManager.save_raw_data` wysokopoziomowym API `scraper_api.save_raw` w `InvestmentSyncService`.
- **Czysta rezolucja download_raw**: Usunięcie lokalnego wyznaczania `target_dir` w `download_raw_json` — biblioteka teraz samodzielnie zarządza ścieżkami na podstawie ID.
- **Konsystencja DeveloperRepository**: Migracja `save_dev_raw_json` na `scraper_api.save_raw_developer`.
- **Fix API download-raw**: Naprawa błędu `TypeError` w blueprintcie `investments.py` wynikającego z przekazywania nadmiarowych slugów.
- **Regresja I/O**: Dodanie `tests/test_raw_saving.py` weryfikującego poprawność przekierowania zapisów do biblioteki.

### Wnioski ze zmian
- Architektura "Thin-Client" została wzmocniona: Tracker stał się całkowicie agnostyczny względem fizycznej struktury plików surowych.
- Wykorzystanie `scraper_api.save_raw` zamiast bezpośrednich metod managera upraszcza kod i przygotowuje system pod przyszły split repozytoriów.

## Wersja 0.9.27 — Kamień 16 (Geocoding & HERE API Encapsulation) — 2026-06-04
- **Utworzenie HereMapsService**: Skonsolidowano całą logikę obsługi HERE API (geokodowanie, POI, statyczne mapy) w nowej usłudze, eliminując rozproszenie tych funkcji w projekcie.
- **Refaktoryzacja Blueprintu poi**: Zastąpiono bezpośrednie wywołania do API HERE przez `urllib` i `requests` czystymi wywołaniami do `HereMapsService`.
- **Usunięcie modułu here_maps.py**: Pozbyto się przestarzałego pliku z głównego katalogu, przenosząc jego niezbędną logikę do warstwy serwisowej.
- **Aktualizacja dokumentacji**: Dostosowano przewodniki techniczne oraz dokumentację integracji z portalami do nowej struktury usług.
- **Weryfikacja testowa**: Dodano `tests/test_here_service.py` sprawdzający poprawność komunikacji z API geokodowania i miejsc.

### Wnioski ze zmian
- Centralizacja usług zewnętrznych w dedykowanych klasach znacząco podnosi testowalność systemu poprzez ułatwienie mockowania. System zyskał twardą barierę między logiką biznesową a specyficznymi protokołami zewnętrznych dostawców map.

## Wersja 0.9.26 — Kamień 15 (Developer Identification Delegation) — 2026-06-04
- **Delegacja identyfikacji do biblioteki**: Zaimplementowano wykorzystanie API `identify_developer` z `usi-scrapers` do pozyskiwania kanonicznych nazw deweloperów z adresów URL.
- **Refaktoryzacja Blueprintu register**: Usunięto przesyłanie sztucznych nazw deweloperów ("Nieznany Deweloper"), co wymusza rzetelną identyfikację przez warstwę usług.
- **Modernizacja DiscoveryService**: Oczyszczono mechanizm rejestracji nowych inwestycji z manualnej ekstrakcji `vendor_id` i zgadywania nazw deweloperów.
- **Weryfikacja integracji**: Dodano `tests/test_developer_identification.py` potwierdzający poprawność delegacji wywołań do biblioteki.

### Wnioski ze zmian
- Eliminacja lokalnego zgadywania nazw na rzecz zapytań do API portali gwarantuje, że system operuje na danych identycznych z tymi widocznymi dla użytkownika końcowego. Redukcja odpowiedzialności trackera w tym obszarze upraszcza kod i ułatwia jego utrzymanie.

## Wersja 0.9.25 — Kamień 14 (Resource Resolution Modernization) — 2026-06-04
- **Optymalizacja InvestmentIdentityResolver**: Wprowadzono właściwość `tech_manager` (lazy-loading), która zapewnia efektywny dostęp do API biblioteki bez wielokrotnej reinicjalizacji.
- **Eliminacja get_investment_resources_by_slug**: Całkowicie usunięto przestarzałą metodę, wymuszając korzystanie z tożsamości ID w całym systemie.
- **Refaktoryzacja warstwy usług**: Zaktualizowano `InvestmentEditorService`, `InvestmentService` oraz `InvestmentSyncService`, usuwając legacy-fallbacki oparte na slugach.
- **Modernizacja batch identifier preparation**: Przeniesiono rezolucję ścieżek w operacjach wsadowych na API `TechnicalDataManager`.
- **Weryfikacja regresji**: Dodano `tests/test_id_resolution_final.py` potwierdzający poprawność mapowania po usunięciu starych metod.

### Wnioski ze zmian
- System rygorystycznie wymusza rezolucję ścieżek po ID, co definitywnie rozwiązuje problem "dryfu" danych przy zmianie slugów przez portale. Centralizacja wiedzy o strukturze plików w `TechnicalDataManager` poprawia spójność i ułatwia przyszłe migracje.

## Wersja 0.9.24 — Kamień 13 (ID-Keyed Skeleton Creation) — 2026-06-04
- **Refaktoryzacja InvestmentRepository.create_investment_skeleton**: Zmieniono sygnaturę i implementację na ID-keyed, wykorzystując `TechnicalDataManager` do ustalania ścieżek.
- **Aktualizacja InvestmentSyncService**: Dostosowano przepływ rejestracji nowych inwestycji do nowej architektury, eliminując zależność od slugów przy tworzeniu katalogów.
- **Weryfikacja testowa**: Dodano `tests/test_skeleton_creation.py` sprawdzający poprawność zapisu szkieletów oraz mechanizm fallbacku w przypadku braku konfiguracji.

### Wnioski ze zmian
- Przejście na ID-keyed skeleton creation to kluczowy krok w odpinaniu systemu od niestabilnych slugów portalowych. Użycie `TechnicalDataManager` jako jedynego źródła prawdy o ścieżkach zapobiega fragmentacji danych na etapie ich pierwotnego pobierania.

## Wersja 0.9.23 — Kamień 11 (Slug Generation Removal) — 2026-06-04
- **Usunięcie slugify_dev**: Skasowano lokalny generator slugów z `portal_matcher.py`.
- **Pełna tożsamość portalowa**: System w 100% polega na slugach dostarczanych przez portale lub ID, co eliminuje dryf nazewnictwa deweloperów.

### Wnioski ze zmian
- Eliminacja lokalnego generowania slugów z nazw deweloperów domyka proces standaryzacji tożsamości. Kolejny etap usuwania "martwego kodu" upraszcza architekturę i zwiększa jej przewidywalność.

## Wersja 0.9.22 — Kamień 10 (API Identity Enforcement) — 2026-06-04
- **Usunięcie get_id_by_slug**: Skasowano przestarzały helper w `investment_index.py`, eliminując kolejny punkt nieuprawnionej rezolucji slug→ID.
- **Monitoring fallbacków API**: Wprowadzono logowanie ostrzeżeń w `_resolve_system_id` dla zapytań nieposiadających parametru `id`. Umożliwia to precyzyjną identyfikację legacy-kodu w warstwie UI.
- **Weryfikacja stabilności**: Potwierdzono poprawne działanie systemu po czystce indeksu zestawem testów regresyjnych.

### Wnioski ze zmian
- Eliminacja helperów slugowych w indeksie domyka proces izolacji tożsamości ID. Logowanie ostrzeżeń w API pozwala na monitorowanie długu technicznego w UI bez wpływu na UX, wyznaczając jasny kierunek dalszej refaktoryzacji.

## Wersja 0.9.21 — Kamień 09 (Deterministic Path Resolvers) — 2026-06-04
- **Refaktoryzacja InvestmentIdentityResolver**: Wprowadzono w 100% deterministyczną rezolucję zasobów bazującą na portal ID. Skasowano kaskadowe fallbacki zgadujące foldery na podstawie slugów.
- **Deprecjonowanie slug-identity**: Oznaczono `get_investment_resources_by_slug` jako przestarzałe, wymuszając korzystanie z tożsamości ID.
- **Modernizacja repair_image_paths.py**: Całkowicie usunięto metody `_find_by_*`. Skrypt deleguje teraz rezolucję ścieżek do `TechnicalDataManager`, co eliminuje ryzyko błędnych napraw przy kolizjach nazw.
- **Testy determinizmu**: Dodano `tests/test_deterministic_mapping.py` weryfikujący poprawność nowej architektury resolution.

### Wnioski ze zmian
- Rezygnacja z heurystyk na rzecz twardych ID portalowych eliminuje ryzyko "przypadkowego" dopasowania zasobów. Centralizacja wiedzy o strukturze dyskowej w `TechnicalDataManager` pozwala na bezpieczne przenoszenie plików między folderami deweloperów.

## Wersja 0.9.20 — Kamień 08 (Bidirectional Mapping Cleanup) — 2026-06-04
- **Usunięcie helperów slug**: Skasowano metody `resolve_dev_slug` i `resolve_id_to_slug` z `DeveloperManager` i `DeveloperRepository`.
- **Uproszczenie API**: Eliminacja zbędnych delegacji w fasadzie managera deweloperów, wymuszająca korzystanie z tożsamości bazującej na ID.
- **Weryfikacja regresji**: Potwierdzono poprawne działanie systemu przy użyciu skonsolidowanej logiki `get_developer` w istniejących testach.

### Wnioski ze zmian
- Redukcja publicznego API o pomocniki bazujące na slugach zapobiega powstawaniu niejawnego kodu parsującego i wspiera architekturę ID-only. Brak zewnętrznych wywołań tych metod potwierdził ich status jako długu technologicznego.

## Wersja 0.9.19 — Kamień 07 (ID Resolution Cleanup) — 2026-06-04
- **Konsolidacja get_developer**: Usunięto duplikację metod w `DeveloperRepository`. Nowa implementacja priorytetyzuje USI ID i wyszukiwanie w indeksie O(1), wspierając fallback do nazw (case-insensitive).
- **Deprecjonowanie slug-based lookups**: Oznaczono `_find_anchor_by_slug` jako przestarzałe, wymuszając korzystanie z tożsamości bazującej na ID.
- **Refaktoryzacja InvestmentSyncService**: Zmodernizowano `_canonical_slug_from_raw`, która używa teraz `usi_scrapers.resolve_path` do ekstrakcji portal ID i mapowania go na kanoniczny slug USI.
- **Stabilizacja testowa**: Wdrożono `tests/test_id_resolution.py` oraz `tests/test_canonical_slug_resolution.py` potwierdzające odporność systemu na dryf slugów.

### Wnioski ze zmian
- Eliminacja lokalnego "zgadywania" slugów na rzecz systemowej rezolucji ID znacząco zwiększa odporność systemu na zmiany w strukturze folderów portalowych. Użycie silnika mapowania z biblioteki pozwala na ujednolicenie logiki ekstrakcji kluczowych identyfikatorów.

## Wersja 0.9.18 — Kamień 06 (Czystka po crawlerach) — 2026-06-04
- **Usunięcie legacy crawlera**: Skasowano przestarzałą implementację `python_worker/crawler.py` oraz jej testy.
- **Integracja usi-crawlers**: Pełne przejście na `WedrowiecDaemon` i `DoktorDaemon` z zewnętrznej biblioteki przez centralny moduł `python_worker/daemons.py`.
- **Naprawa ui_server.py**: Usunięto błąd podwójnego importu Blueprintów crawlera.
- **Nowe testy integracyjne**: Dodano `tests/test_crawler_api_new.py` weryfikujący poprawność komunikacji API z nowymi daemonami.

### Wnioski ze zmian
- Delegacja logiki daemonów do zewnętrznej biblioteki znacząco upraszcza kod główny trackera, czyniąc go bardziej "thin-client". Centralizacja instancji w `daemons.py` ułatwia testowanie i zarządzanie cyklem życia procesów tła.

## Wersja 0.9.17 — Kamień 12 (Naprawa testów) — 2026-06-04
- **Inwentaryzacja testów legacy**: Dokumentacja 35 scenariuszy testowych w `tests/LEGACY_TESTS.md` przed ich usunięciem.
- **Reset środowiska testowego**: Usunięcie wszystkich przestarzałych plików `.py` i wyczyszczenie `__pycache__` w celu eliminacji długu technologicznego.
- **Fundament nowej generacji**: Implementacja `tests/test_usi_scrapers_integration.py` oraz `tests/test_adapters_base.py` bazujących na nowym API.
- **Rozszerzenie TechnicalDataManager**: Dodanie metod `get_investment_path`, `get_image_path` i `get_raw_filename` do biblioteki `usi-scrapers` w celu obsługi architektury ID-only.

### Wnioski ze zmian
- **Oczyszczenie długu testowego**: Pozbycie się testów bazujących na starej architekturze jest niezbędne, aby uniknąć fałszywych sygnałów o stabilności systemu podczas głębokiej refaktoryzacji.
- **Konsolidacja I/O**: Rozszerzenie `TechnicalDataManager` o twarde rezolucje ścieżek na podstawie portal ID domyka pętlę izolacji I/O, pozwalając na całkowite usunięcie logiki sklejania ścieżek z trackera.

## Wersja 0.9.16 — Kamień 04 (Naprawa slug i I/O - Krok 04.01) — 2026-06-04
- **Refaktoryzacja InvestmentSyncService**: Zrefaktoryzowano metodę `_fetch_and_transform_portal_data`, aby przyjmowała `system_id` zamiast slugów, korzystając z `InvestmentIdentityResolver` do dynamicznego pozyskiwania ścieżek.
- **Testy automatyczne**: Dodano test potwierdzający to zachowanie.
- Zaktualizowano `TODO.md`: Oznaczono zadania Kroku 04.01 jako wykonane i dodano podsumowanie.

## Wersja 0.9.15 — Kamień 04 (Planowanie: Naprawa slug i I/O) — 2026-06-04
- Zaktualizowano `TODO.md`: Połączono zadania z kamienia 04 ("Naprawa slug") i 05 ("Naprawa zapisu") w jeden spójny kamień "Naprawa slug i I/O".

## Wersja 0.9.14 — Kamień 03 (Raw Inquisitor - Krok 03.01) — 2026-06-04
- **Raport użycia I/O**: Zidentyfikowano wszystkie funkcje wykonujące zapis na dysk w katalogach `python_worker/services/` i `python_worker/api/` i wygenerowano raport `raw_io_usage_report.md`.
- **Testy automatyczne**: Dodano test weryfikujący wygenerowanie tego raportu.

## Wersja 0.9.13 — Kamień 02 (Slug Inquisitor) — 2026-06-04
- **Raport użycia slugów**: Wygenerowano listę funkcji z argumentem `slug` przy pomocy parsera AST w `python_worker/services` oraz `python_worker/api/`.
- **Analiza użycia**: Zidentyfikowano nieuprawnione wywołania sluga do wewnętrznych serwisów i zapisano w nowym pliku `slug_usage_report.md`.
- **Testy automatyczne**: Dodano testy weryfikujące generację i zawartość raportu analizy.

### Wnioski ze zmian
- Architektura wymaga głębokiej refaktoryzacji, w szczególności usługi takie jak `InvestmentSyncService` czy `InvestmentLoader`, aby w pełni zrezygnować ze slugów na rzecz uniwersalnych USI ID oraz systemowych resolverów z `usi-scrapers`.
## Wersja 0.9.12 — Kamień 02 (Slug Inquisitor - Krok 02.01) — 2026-06-04
- **Raport użycia slugów**: Wygenerowano listę wszystkich funkcji z argumentem 'slug' używając parsera AST do pliku `slug_usage_report.md`.
- **Testy**: Dodano test weryfikujący wygenerowanie raportu (`test_slug_report.py`).

## Wersja 0.9.11 — Kamień 01 (Aktualizacja do usi-scrapers v0.9.7) — 2026-06-04
- **Aktualizacja Biblioteki**: Podniesienie wersji `usi-scrapers` do 0.9.7 w `requirements.txt`.
- **Refaktoryzacja I/O**: Dostosowanie wywołań `sync_images` i `save_raw_data` do nowego modelu wstrzykiwania ścieżek i slugów.
- **Warstwa Kompatybilności**: Wdrożenie shimów w `InvestmentService` i `InvestmentRepository` wspierających zarówno USI ID, jak i legacy slugi w testach i API.
- **Poprawki Ekstrakcji**: Naprawa unwrappingu wartości RP oraz dostosowanie testów do zagnieżdżonego formatu Otodom (`ad.`).
- **Stabilizacja Inwestycji**: Usunięcie błędów `AttributeError` poprzez przywrócenie delegacji `dev_dir`, `build_index` i `append_dev_log`.

### Wnioski ze zmian
- Zachowanie kompatybilności wstecznej (shimy) w serwisach biznesowych jest niezbędne podczas migracji na architekturę ID-only, aby umożliwić stopniową aktualizację ogromnej bazy testów bez blokowania rozwoju.
- Ścisłe powiązanie transformatorów adresu z formatem portalu (np. `City, Street`) oznacza, że każda zmiana formatu musi być odzwierciedlona w mockach testowych w celu zachowania spójności.

## Wersja 0.9.10 — Kamień 02 (Wdrozenie zmian na podstawie wczesniejszej analizy) — 2026-06-04
- **Natywne Transformatory (usi-scrapers)**: Wdrożono mechanizmy transformujące (parsowanie dat Otodom, rzutowanie float) bezpośrednio w `usi-scrapers`, odciążając adaptery w głównym repozytorium z manualnego parsowania stringów.
- **Architektura I/O Isolation**: Całkowicie wyizolowano logikę ścieżek z biblioteki zewnętrznej. Funkcje takie jak zapisu JSON czy pobierania zdjęć przyjmują teraz gotowe instancje `Path`, wymuszając stosowanie systemowego `IdentityResolver` wewnątrz trackera.
- **Naprawa Rejestracji z Discovery**: Wyeliminowano problemy z zapisem dla nowo odkrywanych inwestycji i zaktualizowano `register_investment`, gwarantując spójne podawanie `usi_inv_id`.
- **Integracja "Thin-Adapters"**: Potwierdzono stabilność "chudych adapterów", które po zmianach polegają w 100% na `portal_data_mapping.json`, eliminując ręczne bloki try-except na rzecz reguł konfiguracji.

### Wnioski ze zmian
- Architektura ścisłego wstrzykiwania `Path` w `usi-scrapers` ostatecznie zabezpiecza system przed powstawaniem rozbieżności pomiędzy nazwami katalogów na dysku, a wewnętrznymi slugami API. Tracker w pełni zarządza miejscem zapisu.
- Translacja i parsowanie niestandardowych typów danych (daty słowne, jednostki walut) to domena scrapera (biblioteki), a nie aplikacji biznesowej. Użycie natywnych transformatorów znacząco poprawia stabilność adapterów i jakość surowych danych.

## Kamień 01 — Analiza usi-scrapers API — 2026-06-04
* Przeprowadzono głęboki audyt mechanizmów wejścia/wyjścia z paczki `usi-scrapers` oraz jej silnika do transformowania surowych odpowiedzi z portali.
* Zidentyfikowano problem grubych adapterów w głównym repozytorium (manualne formatowanie dat i parsowanie walut m.in. w `OtodomAdapter`), które powinny zostać przeniesione jako natywne funkcje do biblioteki scraperów.
* Zdiagnozowano krytyczne naruszenie reguły **ID-only** – serwisy `investment_sync.py` wymieniają informacje poprzez slugi (wymuszając na bibliotece zewnętrzne sklejanie ścieżek), omijając w pełni stabilny mechanizm weryfikujący `IdentityResolver`.
* Automatycznie sformułowano i opublikowali przy użyciu API GitHuba (jako Issue #2) kompleksowy raport refaktoryzacyjny do wdrożenia w repozytorium paczki scraperów.

## Aktualizacje — 2026-06-03
- **Wdrożenie InvestmentRepository**: Całkowicie usunięto logikę I/O z serwisów biznesowych (`InvestmentEditorService`, `InvestmentSyncService`, `DiscoveryService`) wprowadzając centralne `InvestmentRepository`. Repozytorium w hermetyczny sposób posługuje się `InvestmentIdentityResolver` by ukryć fizyczne ścieżki i spełnić ostatecznie postulat architektury *ID-only*.
- **Niezmienność Danych Surowych (Immutability)**: Usunięto awaryjne bloki zapisu ręcznego w warstwie repozytoriów. Odczyt i zapis źródłowych plików `raw_*.json` jest teraz kontrolowany wyłącznie przez bibliotekę `usi-scrapers`.
- **Refaktoryzacja InvestmentService (Fasada)**: Rozbicie monolitycznego `InvestmentService` na 3 modularne komponenty (`InvestmentIdentityResolver`, `InvestmentSyncService`, `InvestmentEditorService`), rozwiązując problem "God Object" i poprawiając zgodność z zasadami SRP, zachowując 100% kompatybilność starego API poprzez wykorzystanie wzorca projektowego *Fasada*.
- **Optymalizacja Fast-Path Image Sync**: Całkowicie wyeliminowano wąskie gardło I/O (`os.walk` po całym drzewie `Public/USI/`) na etapie aktualizacji obrazów. Proces ten zredukowano do szybkiego wyszukiwania tablicowego w uprzednio wygenerowanym obiekcie `image_paths` z poziomu jsona. Znacząco przyspieszyło to wykonywanie *Bulk Updates*.
- **Naprawa Błędu W Pętli Pobierania**: Zlikwidowano krytyczny `TypeError` wewnątrz `process_batch`, który "cichaczem" powodował załamania pętli `update_investment` po zmuszeniu systemu do polityki *ID-Only*.
- **Aktualizacja Dokumentacji**: Wzmocniono w dokumentacji rolę pliku `portal_data_mapping.json` – to on powinien być modyfikowany jako pierwszy przed próbą dodania kodu rzutującego do `python_worker/adapters/`.
- **usi-scrapers v0.9.0**: Zaktualizowano bibliotekę `usi-scrapers` do wersji 0.9.0.
- **Mapping API Refaktor**: Kompletnie zrefaktoryzowano kod adapterów (`python_worker/adapters/`), zastępując stare, ręczne reguły ekstrahujące (segmentacja, czyszczenie adresów, rzutowanie wartości, galerie zdjęć) nowymi deklaratywnymi możliwościami w `portal_data_mapping.json` (zagnieżdżone klucze `transform` oraz `evaluate_signals`).

## Aktualizacje — 2026-06-02
- **Scraper Delegation**: Zaktualizowano bibliotekę `usi-scrapers` do v0.8.5 wspierającą zaawansowane mapowanie (operator `|`).
- **Refaktoryzacja RPAdapter**: Usunięto przestarzały kod fallbacków dla lokalizacji i dat zakończenia z RynekPierwotny, delegując odpowiedzialność do zaktualizowanego API mapującego z `usi-scrapers`.
- **Poprawka CLI**: Naprawiono błąd iteracji przy korzystaniu z komendy `update-inv` dla formy dev_slug/inv_slug, rozwiązując `TypeError` / `AttributeError`.

## UI — 2026-05-15
- **Refaktoryzacja stylów**: Przeprowadzono audyt i migrację stylów inline do dedykowanych klas CSS, poprawiając separację warstw i ułatwiając przyszłe modyfikacje wyglądu.
- **Standaryzacja**: Wprowadzono klasy pomocnicze dla powtarzalnych wzorców layoutowych (np. wyrównanie w osi, spacing w powiadomieniach).

## Powiadomienia — 2026-05-15
- **Poprawa czytelności**: Zwiększono szerokość paska powiadomień w Navbarze, co eliminuje agresywne przycinanie długich nazw inwestycji.
- **Stylistyka**: Wyłączono wymuszony tryb ALL CAPS dla nazw zadań, nadając powiadomieniom bardziej naturalny wygląd.
- **Komunikacja**: Ujednolicono komunikaty postępu, unikając generycznego "Pobieram..." na rzecz bardziej precyzyjnych informacji o przetwarzaniu danych.


- **UI Components**: Wydzielono `CategoryRatingRow` jako modularny komponent, ujednolicając system ocen w panelu bocznym i stopce widoku Media (Mode C).
- **Gallery Fix**: Naprawiono usterkę resetowania pozycji galerii `SlideShow` przy przełączaniu widoków lub edycji danych.
- **System Raportowania**: Przeniesiono przycisk "Report" do globalnego `ActionBar`.
- **Audit Workflow**: Zmieniono charakter zgłoszeń na flagowanie do audytu (`audit_needed: true`). Wprowadzono narzędzie CLI `python3 -m python_worker.main run-audit` do zarządzania oflagowanymi rekordami.


- **Cleanup**: Usunięto martwy moduł 'grabber' z dokumentacji (CLAUDE.md, specyfikacja) oraz schematów JSON.
- **UI Fix**: Naprawiono błąd 'health check' w NavDrawer, dostosowując parsowanie odpowiedzi do formatu v0.3.0 library health.
- **Nawigacja**: Zmieniono kolejność elementów w szufladzie nawigacyjnej (Inwestycje, Deweloperzy, Pobieranie na początku).
- **Refactoring**: Uporządkowano strukturę TODO.md i zarchiwizowano pierwszy kamień milowy.

## Deweloperzy — 2026-05-11

- **Filtr "Tylko powiązane"**: Zaimplementowano filtr `only_merged` w backendzie (`DeveloperManager`), API oraz interfejsie użytkownika (`ActionBar`), umożliwiający szybkie odfiltrowanie deweloperów posiadających mapowania lub rekordy potomne.
- **Ulepszona Heurystyka Sugestii**: Rozbudowano algorytm sugestii deweloperów o zbieżność czasową (lata oddania inwestycji) oraz zaawansowany fuzzy matching nazw (> 85%).
- **Prezentacja Sugestii**: Dodano pole `reason` do sugestii, co pozwala na przejrzyste wyświetlanie uzasadnienia powiązania bezpośrednio w interfejsie użytkownika.


- **System raportowania błędów**: Wdrożono mechanizm "Report", umożliwiający analitykom dodawanie notatek o błędach w danych inwestycji bezpośrednio z interfejsu UI.
- **Backend Raportów**: Zaktualizowano schemat JSON o pole `issue_reports` oraz dodano endpoint API do bezpiecznego zapisywania zgłoszeń.
- **Interfejs Użytkownika**: Dodano przycisk "Report" w widoku szczegółowym oraz dedykowane okno modalne do wprowadzania treści zgłoszenia.



- **Deep Visit & Automatyzacja**: Wdrożono mechanizm automatycznej rejestracji i pobierania danych dla nowo odkrytych inwestycji podczas wizyt Wędrowca.
- **Weryfikacja Rekordów**: Zaimplementowano flagę `reviewed` pozwalającą na oznaczanie stanu weryfikacji inwestycji (nowe vs zatwierdzone).
- **UI - Wyróżniki "NOWE"**: Dodano wizualne oznaczenia ("NOWE") na listach oraz przycisk "Zatwierdź" w widoku szczegółowym.
- **Dashboard & Filtrowanie**: Wdrożono licznik nieprzejrzanych inwestycji na Dashboardzie oraz filtr "Tylko nieprzejrzane" w widoku listy.
- **Optymalizacja Operacyjna**: Zintegrowano system batching z raportowaniem postępu w `NotificationCenter`.

## Pobieranie — 2026-05-11

- **Przebudowa UI**: Wdrożono układ sekcyjny w `view-download.jsx` (Manualne skanowanie vs Wędrowiec) z integracją statusów operacyjnych i sterowaniem crawlerem.
- **Zbiorcza rejestracja (Batching)**: Wdrożono `InvestmentService.process_batch` oraz endpoint `/api/register-bulk`, umożliwiając rejestrację paczek inwestycji z natywnym raportowaniem postępu w `NotificationCenter`.
- **Standaryzacja statusów**: Ujednolicono nazewnictwo stanów rejestracji w całym systemie ("w kolejce") dla większej przejrzystości operacyjnej.
- **Walidacja pełnego cyklu**: Zintegrowano i przetestowano przepływ pełnej rejestracji i synchronizacji zdjęć przy użyciu mechanizmu batching, potwierdzając stabilność dla procesów masowych.



## Dashboard — 2026-05-10
- Refaktoryzacja Dashboardu: Naprawiono "rozsypany" układ strony głównej poprzez wdrożenie 12-kolumnowej siatki CSS Grid.
- Widget Statusu Wędrowca: Dodano interaktywną kartę wyświetlającą stan crawlera, aktualnie odwiedzanego dewelopera oraz statystyki eksploracji portali.
- Integracja MapModule: Zastąpiono statyczną miniaturę mapy pełnoprawnym, interaktywnym modułem mapy z obsługą klastrowania i nawigacji.
- Optymalizacja Responsywności: Dostosowano siatkę dashboardu do urządzeń mobilnych i tabletów (dynamiczne przełączanie kolumn).
- Standaryzacja Kart: Wszystkie moduły dashboardu korzystają teraz ze spójnego komponentu BaseModule.

## v0.9.9 — 2026-05-25

- **Identity Resolver (Resource Mapping)**: Wdrożono scentralizowany mechanizm mapowania ID na zasoby fizyczne (`InvestmentService.get_investment_resources`, `DeveloperManager.get_developer_resources`). 
- **Stabilność ID-ONLY**: Zastąpiono rozproszoną logikę "zgadywania" ścieżek na podstawie slugów jednym, autorytatywnym punktem styku z systemem plików. Gwarantuje to poprawne działanie systemu nawet po zmianie nazw folderów.
- **Robust ID Injection**: Zaktualizowano `_load_investment` o automatyczne wstrzykiwanie `usi_inv_id` do rekordów legacy, które nie posiadają ID wewnątrz pliku, ale są poprawnie zaindeksowane.
- **Refaktoryzacja I/O**: Operacje przeglądu (review), raportowania błędów oraz zarządzania zdjęciami korzystają teraz wyłącznie z nowego resolvera tożsamości.

## v0.9.8 — 2026-05-25

- **Architektura ID-ONLY**: Pełne wdrożenie zasady identyfikacji po ID. Funkcja indeksowania (`rebuild`) korzysta teraz wyłącznie z danych wewnątrz plików JSON, a nie z nazw katalogów.
- **Naprawa szkieletów (T2)**: Przywrócono dane dla ponad 7000 inwestycji ("szkieletów") poprzez automatyczną odbudowę plików `usi_*.json` z lokalnych danych surowych (`raw_*.json`).
- **Dynamiczny routing obrazów**: Wprowadzono elastyczny endpoint `/api/image/<path:filepath>`, który eliminuje błędy ładowania zdjęć wynikające z różnic w strukturze folderów (np. po scalaniu rekordów).
- **Aktualizacja Biblioteki**: Podniesiono wersję `usi-scrapers` do **0.8.1**, wprowadzając wsparcie dla ujednoliconego mapowania współrzędnych (`geo_point`) i Required Fields.
- **Indeks inwestycji**: Zoptymalizowano proces budowania indeksu, zapewniając kompletność pól (`source`, `district`, `developer_slug`) wymaganych przez interfejs React.

## v0.9.7 — 2026-05-10

- **Refaktoryzacja Dashboardu**: Naprawiono "rozsypany" układ strony głównej poprzez wdrożenie 12-kolumnowej siatki CSS Grid.
- **Widget Statusu Wędrowca**: Dodano interaktywną kartę wyświetlającą stan crawlera, aktualnie odwiedzanego dewelopera oraz statystyki eksploracji portali.
- **Integracja MapModule**: Zastąpiono statyczną miniaturę mapy pełnoprawnym, interaktywnym modułem mapy z obsługą klastrowania i nawigacji.
- **Optymalizacja Responsywności**: Dostosowano siatkę dashboardu do urządzeń mobilnych i tabletów (dynamiczne przełączanie kolumn).
- **Standaryzacja Kart**: Wszystkie moduły dashboardu korzystają teraz ze spójnego komponentu BaseModule.


- Naprawiono błąd połączenia z biblioteką usi-scrapers (użycie health_check) i zsynchronizowano z wersją v0.3.0.
- Wdrożono system migawek discovery z licznikami nowości wyświetlanymi na kartach deweloperów.
- Naprawiono błąd skanowania globalnego dla portali Otodom i TabelaOfert.
- Zintegrowano skanowanie globalne z NotificationCenter poprzez JobManager (asynchroniczność).
- Dodano funkcję "Skanuj 5" umożliwiającą szybkie skanowanie pierwszych 150 wyników.
- Rozwiązano problemy z TypeError w StandardCard oraz błędy kodowania nazw plików (%20).
- Zoptymalizowano wyjście konsoli poprzez wyciszenie logów pollingu.


- **Funkcja "Skanuj 5"**: Dodano możliwość ograniczonego skanowania portali (ok. 5 stron / 150 wyników) w widoku Pobieranie, co pozwala na szybki przegląd nowości przy minimalnym ryzyku blokady IP.
- **Optymalizacja DiscoveryService**: Pełne wykorzystanie parametrów limitujących w nowym API v0.3.0.


- **Migracja na usi-scrapers v0.3.0**: Wdrożono pełne wsparcie dla nowej, ujednoliconej wersji biblioteki scraperów ze standaryzowanymi sygnaturami API.
- **Uproszczenie DiscoveryService**: Usunięto portal-specyficzne obejścia (hacks) na rzecz czystych wywołań `discover_{portal}_investments`.
- **Globalne skanowanie**: Naprawiono błąd braku wyników przy skanowaniu całych portali (RP, OTO, TO) — teraz poprawnie zwracane są tysiące ofert.
- **System Discovery Snapshots**: Wprowadzono trwałe zapisywanie wyników discovery do plików `discovery.json` w folderach deweloperów.
- **Nowe liczniki w UI**: Dodano pomarańczowe plakietki "Odkrycia" na liście deweloperów, informujące o liczbie niezarejestrowanych inwestycji.
- **Integracja JobManager**: Skanowanie globalne w widoku Download odbywa się teraz asynchronicznie z podglądem postępu w NotificationCenter.
- **Standaryzacja Health Check**: Ujednolicono format odpowiedzi `/api/system/verify-library` zgodnie z v0.3.0.


- **Model parent_id**: `merge_developers()` ustawia `parent_id` na źródle — żadne pliki nie są archiwizowane ani usuwane. Raw pliki portali (`raw_rp_*.json`, `raw_oto_*.json`, `raw_to_*.json`) pozostają nienaruszone. Slugi portali są święte.
- **`list_developers()` filtruje dzieci**: deweloperzy z `parent_id` znikają z głównej listy — zarówno w `DeveloperManager.list_developers()` jak i w API.
- **Fallback lokalizacji**: `get_developer()` szuka najpierw w `USIdev/`, potem w legacy `USIdata/{slug}/`. Legacy kopie są normalizowane do `USIdev/` przy pierwszym merge.
- **Cache `merged_from[]`**: target dewelopera gromadzi listę wciągniętych slugów; API wzbogaca każdy wpis o `portal_mapping` i `investments_count`.
- **Log zdarzeń `events[]`**: każda operacja (merge_in, dismiss_suggestion) dopisuje wpis newest-first, max 100 pozycji. Publiczna metoda `DeveloperManager.log_event()`.
- **`DevMiniCard`**: nowy komponent karty dewelopera w `view-dev-detail.jsx` — nazwa, slug·ID·liczba inwestycji, sugestia/data (sub), odznaki portali, dowolny footer z przyciskami.
- **Optimistic UI**: kliknięcie "Połącz" natychmiast przenosi kartę do panelu "Połączeni" z animacją CSS `devCardArrive`; wywołanie API w tle; cofnięcie stanu przy błędzie.
- **Odrzucanie sugestii**: przycisk X na karcie sugestii usuwa ją optimistycznie; API `dismiss-suggestion` dopisuje zdarzenie.
- **`DevEventsLog`**: panel 5 ostatnich zdarzeń ze zwijaniem.
- **Naprawa `onToggleTheme`**: prop był przekazywany pod błędną nazwą `handleToggleTheme` — naprawiono (eliminuje ReferenceError w logach).
- **Testy**: `test_developer_manager.py` — 15 testów: get (USIdev, legacy, missing), list (filtr dzieci), merge (7 przypadków w tym niezmienność raw), dismiss (2).

## POI widget + Developer Crawler — 2026-05-09

- **PoiModule (P01 backend)**: nowe endpointy `GET /api/poi/<dev_slug>/<inv_slug>` (odczyt `poi_<inv_slug>.json`) i `POST /api/poi/<dev_slug>/<inv_slug>/fetch` (fetch HERE Places Browse API + Wikimedia geosearch PL, zapis JSON). Współrzędne z `location.coords`. Kategorie: food, entertainment, outdoor, transport, shopping, education, health.
- **PoiModule (P02 frontend)**: nowy `PoiModule` w `modules-ui.jsx` — lista POI pogrupowana po kategorii z odległością. Sekcja Wikipedia z linkami. Stan "idle" pokazuje przycisk "Pobierz POI"; auto-load przy otwarciu. Wbudowany w prawą kolumnę `DetailViewA`.
- **DeveloperCrawler**: moduł `crawler.py` — daemon thread crawlujący discovery dla wszystkich deweloperów. Pierwsze wejście: stagger losowy po 2 tygodniach; powtórka co 30±5 dni. Tempo: 10-20 min przerwa między wizytami. Stan (`last_visit`, `next_visit`, `new_since_review`) zapisywany w `usi_dev_*.json["crawler"]`.
- **Crawler API**: nowe endpointy `GET /api/crawler/status`, `POST /api/crawler/pause`, `POST /api/crawler/resume`, `POST /api/crawler/badge-reset/<dev_slug>`.
- **Badge nowych inwestycji**: pole `new_since_review` w odpowiedzi `/api/developers`; karta dewelopera pokazuje zielony badge "+N nowe" gdy crawler znajdzie nowe inwestycje. Badge zerowany przy otwarciu widoku dewelopera.

## Widok C pasek kategorii + DataGrid bez migotania — 2026-05-09

- **ModeC pasek kategorii**: zastąpiono przycisk "Pokaż panel" stałym paskiem 6 chipów (kolorowa kropka + skrót + wartość). Klik w chip ustawia `focusedCat` i otwiera `RatingsPanel`. Strzałka toggle zwija/rozwija panel (max-height 320px).
- **DataGrid brak migotania**: tryb `table` wyłącza wirtualizację i renderuje wszystkie wiersze bezpośrednio — eliminuje migotanie przy scrollowaniu. Tryb `grid` zachowuje wirtualizację z RAF-throttled scroll handlerem.

## MiniMapa — pinezka SVG + retina + styl wektorowy; Pobieranie bulk — 2026-05-09

- **Pinezka SVG**: HERE Maps Image API v3 nie obsługuje stylowania markera przez query params (wszystkie opcje `icon:`, `color:` zwracają 400). Zamiast tego nakładamy własny różowy SVG marker (`#E5006D`, teardrop z białym kółkiem) przez `position:absolute; left:50%; top:50%; transform:translate(-50%,-100%)` — mapa z `overlay:zoom=16` jest zawsze wycentrowana na koordynatach, więc marker trafia dokładnie w punkt.

## MiniMapa retina + styl wektorowy; Pobieranie bulk — 2026-05-09

- **MiniMap retina**: `_buildHereUrl` mnoży CSS pixels przez `devicePixelRatio` (max 2×, ograniczone do 2048px HERE limit) — mapa ostra na ekranach Retina.
- **Styl wektorowy HERE**: zmieniono z `explore.satellite.day/night` na `explore.day` / `explore.night` — czytelniejsza mapa, lepsza typografia w dark mode.
- **Pobieranie — usunięcie karty**: po udanym `/api/register` karta natychmiast znika z listy (zamiast oznaczenia `registered: true`).
- **Pobierz wszystkie nowe**: pasek `usi-download-bulk-bar` z licznikiem i przyciskiem "Pobierz wszystkie nowe (N)" — sekwencyjna rejestracja, błąd jednej nie przerywa batcha.

## UI — naprawki Inwestycji, Deweloperów i Powiadomień — 2026-05-09

- **CSS `list-table-thumb`**: dodano brakujący constraint (40×40px, `object-fit: cover`, border-radius) — miniaturki w widoku listy przestały być olbrzymie.
- **Nawigacja strzałkami**: `←`/`→` przełączają inwestycje z listy `visibleInvestments` gdy widok `detail` jest aktywny; `[`/`]` (zamiast strzałek) przełączają zdjęcia w `SlideShow` i `Lightbox`.
- **Przycisk "Powrót"**: `prevView` state w `app.jsx` — back z widoku detail inwestycji wraca do poprzedniego widoku (`dev-detail` lub `list`), nie zawsze do listy.
- **Filtr "Aktywni"**: backend `/api/developers` wzbogacony o `last_updated` (max mtime `usi_*.json` w folderze dewelopera); frontend filtruje po 12 miesiącach.
- **StatusMessenger**: usunięto styl pill/badge (border-radius, padding); zastąpiono monosopace text (`font-family: JetBrains Mono`).
- **NotificationConsole**: przeniesiono z dołu na górę ekranu (slide `translateY(-100%)` → `translateY(0)`); toggle klawiszem `§`; konsola zawsze wyrenderowana (animacja CSS, nie warunkowy `return null`).
- **Naprawa `developer: null`**: `RPAdapter._from_raw` wyciąga `vendor.name`; `Merger` zachowuje `developer`/`developer_slug` z `existing_data`.

## MiniMap dynamiczny + naprawki adaptera — 2026-05-09

- **MiniMap ResizeObserver**: `MiniMap` mierzy teraz szerokość kontenera przez `ResizeObserver`, przelicza wysokość z proporcji (`ratio`, domyślnie 3:1) i buduje URL HERE po stronie klienta — bez pre-generowania w backendzie.
- **Dark mode w MiniMap**: generowane są oba warianty URL (light/dark) przy każdym przeliczeniu; przełącznik motywu działa natychmiast bez reloadu obrazu.
- **Debounce URL**: nowy request do HERE nie częściej niż co 5 sekund od ostatniej zmiany rozmiaru; bieżący obraz rozciąga się (`object-fit: cover`) do czasu doładowania.
- **CSS fix — padding-bottom vs height**: usunięto `height: var(--usi-map-height, 140px)` z `.usi-minimap-container`, który kolidował z techniką `padding-bottom` nowego MiniMap i powodował 2× za dużą mapę.
- **Naprawa `developer: null`**: `RPAdapter._from_raw` teraz wyciąga `vendor.name` z raw RP JSON i ustawia pole `developer`; `Merger` zachowuje `developer`/`developer_slug` z `existing_data` gdy portal zwraca null.
- **Usunięto pre-generowanie URL HERE z backendu**: `api/utils.py` nie dodaje już `here_map_url`/`here_map_url_dark` do odpowiedzi (generowanie przeniesione do klienta).

## Weryfikacja zmiany statusu w metadanych — 2026-05-09
- Zdiagnozowano i naprawiono błąd synchronizacji statusu inwestycji między backendem a UI.
- Poprawiono hook useRatings, aby automatycznie aktualizował lokalny stan DataBus po udanym zapisie.
- Zweryfikowano poprawność zapisu statusu w głównym pliku usi_*.json na dysku.
- Potwierdzono spójność danych w MetadataPanel po zmianie statusu przez analityka.


- Dodano przycisk "Odśwież dane" w DetailViewA.
- Zintegrować frontend z asynchronicznym mechanizmem JobManager na backendzie.
- Wprowadzono endpoint POST /api/refresh obsługujący pełną aktualizację rekordu i zdjęć.


- Przeprowadzono audyt i lokalizację inline SVG w kodzie UI.
- Wyodrębniono 23 ikony i 5 grafik do zewnętrznych plików .svg.
- Zrefaktoryzowano komponenty Icon, USIStarLogo i StarRating na tagi <img>.
- Ujednolicono użycie logo USI (usi-star-white.svg) w całej aplikacji.
- Zweryfikowano poprawne renderowanie i skalowanie zasobów.

## Standaryzacja stylów i optymalizacja — 2026-05-09
- **Unifikacja Pill Badges**: Zdefiniowano klasę `.usi-pill.info` oraz rozszerzono `.usi-pill.outline` o automatyczne dopasowanie koloru obramowania dla wariantów `success`, `danger` i `info`.
- **Eliminacja Inline Styles**: Usunięto style inline z widoków deweloperów i biblioteki modułów, zastępując je semantycznymi klasami pomocniczymi (`.usi-text-accent`, `.usi-weight-400`).
- **Poprawa Wyświetlania Sugestii**: Ujednolicono wygląd etykiet sugestii deweloperów, korzystając z nowego systemu klas CSS.
- **Standaryzacja DataGrid**: Migracja stylów inline (layout, wyrównanie) do `components.css` oraz wprowadzenie klas pomocniczych w `global.css`. Wykorzystano zmienne CSS dla dynamicznych parametrów siatki.
- **Standaryzacja RatingsPanel**: Wyeliminowano style inline z `RatingsPanel.jsx`, zastępując je klasami pomocniczymi marginesów i wagi tekstu. Wprowadzono semantyczne klasy dla statusu zapisu i punktacji wyróżników.
- **Optymalizacja Modułów Analitycznych**: Przeprowadzono audit i czyszczenie stylów w `analytics.jsx`, `modules-map.jsx` oraz `modules-charts.jsx`. Wdrożono zmienne CSS dla dynamicznych szerokości pasków postępu i wysokości map.

## Czyszczenie artefaktów kodu — 2026-05-09

- **Unifikacja ActionBar**: Przeniesiono akcje inwestycji (linki źródłowe, przełącznik trybów) z HeroBand do globalnego ActionBar, poprawiając spójność nawigacji.
- **Optymalizacja SlideShow**: Rozwiązano problem scrollowania w trybie Media poprzez uelastycznienie komponentu Gallery (className) i wymuszenie pełnej wysokości viewportu.
- **Integracja Modułowa**: Zarejestrowano brakujący moduł MiniMap w ModuleRegistry, udostępniając go w bibliotece modułów i systemie raportowym.
- **Naprawa Wyszukiwarki Deweloperów**: Wdrożono brakującą logikę filtrowania i wyszukiwania w widoku deweloperów zintegrowaną z DataBus.
- **Oczyszczenie Interfejsu**: Usunięto zbędne filtry miast z widoku deweloperów, upraszczając nawigację.
- **Stabilność Funkcji „Połącz”**: Naprawiono błąd 500 przy scalaniu deweloperów poprzez bezpieczniejszą obsługę plików i automatyczne tworzenie katalogu archiwum.


- **Architektura „Thin-Client”**: Zakończono migrację logiki skrapowania i adaptacji danych do zewnętrznej, wersjonowanej biblioteki `usi-scrapers` (v0.1.8).
- **Naprawa TabelaOfert (v0.1.8)**: Rozwiązano krytyczny błąd wycieku zdjęć z niepowiązanych etapów inwestycji poprzez wdrożenie „slicera” HTML (Area-Limited Extraction).
- **Czyszczenie Bazy Danych**: Przeprowadzono automatyczne usunięcie 40 „czystych” rekordów TabelaOfert, które posiadały błędy w strukturze zdjęć, w celu ich ponownej, poprawnej rejestracji.
- **Poprawki RynekPierwotny**: Wdrożono mechanizm „Stage Flattening” w bibliotece, poprawnie mapujący poszczególne etapy inwestycji na niezależne rekordy USI.
- **Stabilność Konfiguracji**: Naprawiono błędy składniowe w `config.py` i usprawniono mechanizm weryfikacji wersji biblioteki przy starcie systemu.
- **Unifikacja Danych**: Przygotowano fundamenty pod standaryzację pól `delivery_date`, identyfikując różnice w raportowaniu terminów między portalami.
- **Optymalizacja Środowiska**: Poprawiono proces instalacji biblioteki `usi-scrapers` poprzez patchowanie `pyproject.toml` (naprawa autodetekcji pakietów).

## Poprawki 2 — 2026-05-08
- **Audyt Stylów i CSS**: Wyeliminowano style inline w komponentach JSX, przenosząc je do semantycznych klas. Zoptymalizowano `views.css`, usuwając ponad 800 linii nieużywanego kodu.
- **Naprawa Modułu „W okolicy”**: Rozwiązano błąd logiczny w wyszukiwaniu pobliskich inwestycji, przywracając poprawne wyświetlanie sąsiedztwa.
- **Optymalizacja Układu DetailsA**: Wprowadzono elastyczny układ kolumn (50/25/25) i przeniesiono metadane do trzeciej kolumny dla lepszej czytelności.
- **Metadane Finansowe**: Dodano obsługę i wyświetlanie minimalnej/maksymalnej ceny za m2 we wszystkich adapterach i widoku szczegółowym.
- **Stabilność Siatki i Kart**: Naprawiono błędy overflow w DataGrid oraz poprawiono proporcje i obsługę błędów miniatur w kartach.
- **System Powiadomień**: Przebudowano NotificationCenter na minimalistyczny styl konsolowy z poprawnym globalnym pollingiem zadań.
- **Poprawki TabelaOfert**: Ulepszono TOAdapter o fallback dla brakujących cen m2 oraz uodporniono config.py na błędy uprawnień macOS.

## Poprawki — 2026-05-07
- **Błąd Discovery Otodom**: Naprawiono filtr „Tylko nowe” poprzez poprawną ekstrakcję ID ofert i usunięcie fałszywych dopasowań do pustych rekordów.
- **Tryb Ciemny i CSS**: Wprowadzono pełne wsparcie dla motywu ciemnego poprzez system zmiennych CSS i unifikację selektorów ([data-dark="1"]).
- **System Powiadomień**: Zaimplementowano NotificationConsole z historią zdarzeń oraz NotificationCenter w Navbarze, zastępując globalne spinnery.
- **Moduły Map**: Zaktualizowano MiniMapy o dynamiczne adresy HERE i naprawiono krytyczny błąd obsługi klastrów (BoundingBox).
- **Ekstrakcja TO**: Udoskonalono identyfikację deweloperów w scraper_to.py poprzez analizę tagów HTML (fallback dla JSON-LD).
- **Zarządzanie Deweloperami**: Zoptymalizowano merge_developers, eliminując ryzyko uszkodzenia ścieżek do zdjęć przy scalaniu rekordów.
- **Responsywność UI**: Wdrożono dynamiczny układ DataGrid (minCardWidth), optymalizując wyświetlanie na szerokich monitorach.

## Długoterminowe i QA — 2026-05-06
- Zaimplementowano mechanizm USI Storyboard do izolowanego testowania komponentów UI w czasie rzeczywistym.
- Wdrożono interaktywny panel Knobs w Storyboardzie, umożliwiający dynamiczną zmianę właściwości komponentów (mock data).
- Przeprowadzono dekompozycję i izolację kluczowych komponentów: DataGrid oraz MapModule (refaktoryzacja pod kątem wstrzykiwania zależności).
- Zaimplementowano system fixtures i mocków dla inwestycji, ułatwiający rozwój interfejsu bez połączenia z API.
- Wprowadzono instrumentację wydajnościową (useRenderTracker) do weryfikacji optymalizacji selektorów DataBus.

## Optymalizacja Logiki Frontendowej — 2026-05-06
- Wdrożono hook `useApi` z centralnym cache i obsługą błędów.
- Zunifikowano logikę ocen (`ocenaLog`, `avgRating`) w dedykowanym module `modules-ui.jsx`.
- Zoptymalizowano `DataBus` wprowadzając selektory (`useDataBusSelector`) i `shallowCompare`.
- Wdrożono framework testów jednostkowych JS (`TestSuite`) z integracją w interfejsie.
- Zredukowano liczbę zbędnych re-renderów w `DataGrid` i widokach głównych.

## System Modułów: Rozszerzenia — 2026-05-06
- **Rozbudowa Systemu Modułów**: Wdrożono zaawansowane moduły analityczne i wizualne, w tym `PriceTrendModule` (wykresy trendów cenowych Chart.js) oraz interaktywny `MapModule` z klastrowaniem punktów (HERE Maps API).
- **System Szablonów (Presets)**: Wprowadzono mechanizm `presets` w `ModuleRegistry`, pozwalający na definiowanie złożonych układów raportów (np. "Przegląd Dewelopera") za pomocą jednego identyfikatora.
- **Zaawansowana Konfiguracja (Knobs)**: Rozszerzono panele edycji modułów o nowe typy pól (`Select`, `Range`), umożliwiając precyzyjną personalizację wizualizacji bezpośrednio w UI.
- **Optymalizacja i Stabilność**: Przeprowadzono kompleksowe testy wydajnościowe i stabilności (`runStressTest`), potwierdzając brak wycieków pamięci i wysoką responsywność rejestru komponentów.
- **Architektura Biblioteki**: Stworzyłem dedykowany widok "Biblioteka", służący jako żywy katalog komponentów z interaktywnym podglądem i dokumentacją parametrów technicznych.

## Stabilność i UX — 2026-05-06
- **Scoped Namespaces**: Zweryfikowano izolację stanu dla wielu instancji tych samych modułów (np. dwóch map) w jednym raporcie.
- **Poprawka PriceTrendModule**: Rozwiązano krytyczny błąd destrukturyzacji `scopedBus`, przywracając interaktywność wykresów.
- **Diagnostyka Interakcji**: Wdrożono szczegółowe logowanie zdarzeń w `MapModule` i `PriceTrendModule` z uwzględnieniem identyfikatorów instancji.
- **Automatyczna Regresja Danych**: Rozszerzono zestaw testów o weryfikację struktury `bus.scopes` i poprawności zagnieżdżonych aktualizacji stanu.
- **Raport Diagnostyczny**: Dodano `test_namespaces.json` jako narzędzie do weryfikacji architektury Interact 2.0.

## DataBus: Zaawansowane funkcje — 2026-05-06
- **Scoped Namespaces**: Wprowadzono przestrzenie nazw `filters` oraz `download` w DataBus z obsługą notacji kropkowej w `setVariable`.
- **Asynchroniczne Dispatchery**: Rozszerzono szynę o obsługę async reducerów i Promises z monitorowaniem stanu `isDispatching`.
- **Debugowanie i DevTools**: Wdrożono logowanie zmian stanu do konsoli (diffy) oraz funkcję eksportu pełnego stanu szyny do JSON.
- **Rejestr Modułów**: Zaimplementowano `ModuleRegistry`, umożliwiając dynamiczne ładowanie komponentów i renderowanie raportów ze specyfikacji.
- **Hook useModuleContext**: Skonsolidowano logikę ekstrakcji danych i agregacji statystyk w uniwersalnym hooku dla modułów.
- **Zagnieżdżone Moduły**: Wprowadzono `LocalModuleContext` i `ContainerModule`, wspierające hierarchiczne wizualizacje (kaskadowy kontekst).
- **Specyfikacje Modułów**: Wdrożono formalną walidację parametrów wejściowych oraz automatyczny generator paneli edycyjnych (`ModuleKnobs`).

## SafeRender Pattern: Implementacja DataBoundary — 2026-05-05
- Wprowadzono wzorzec **SafeRender**, zapewniający odporność interfejsu na uszkodzone lub niekompletne dane z API.
- Zaimplementowano komponent `DataBoundary`, który automatycznie waliduje surowe obiekty JSON względem schematu `USI_INVESTMENT_SCHEMA`.
- Rozszerzono funkcję `safeRender` o inteligentną obsługę typów (string, number, array, object) oraz formatowanie walutowe (`currency`).
- Przeprowadzono refaktoryzację widoków `ViewList` i `DetailRightPanel`, eliminując bezpośrednie ryzyko crashy Reacta ("Objects are not valid as a React child").
- Dodano zestaw testów stabilności danych `runDataIntegrityTest` w `test-regression.js`, umożliwiający automatyczną weryfikację regresji w warstwie danych.
- Uproszczono kod komponentów prezentacyjnych (`ListCard`, `HeroBand`) poprzez usunięcie redundantnych, ręcznych sprawdzeń typów.

## Zaplecze — 2026-05-05
- Pełna dekompozycja `ui_server.py` na modułowe Blueprinty Flask (`jobs`, `investments`, `discovery`, `reports`).
- Ekstrakcja logiki zarządzania zadaniami do dedykowanego modułu `python_worker/jobs.py` (JobManager).
- Wdrożenie warstwy serwisowej (`InvestmentService`, `DiscoveryService`) separującej logikę biznesową od API.
- Refaktoryzacja adapterów do nowoczesnego pakietu `python_worker/adapters/` z wykorzystaniem wzorca Factory.
- Centralizacja pomocników i unifikacja logiczna między interfejsem CLI a webowym.

## Front sklepu: Atomizacja komponentów i "Window Registry" — 2026-05-04
- Ukończono dekompozycję widoku szczegółowego na niezależne komponenty (DetailsViewA, DetailsViewC).
- Zintegrowano wszystkie kluczowe widoki i komponenty z systemem `usiRegister`.
- Uproszczono `view-detail.jsx` do roli lekkiego orchestratora.
- Zlikwidowano race-conditions w środowisku Babel Standalone poprzez rejestr komponentów.

## Sprzatanie — 2026-05-04
- Naprawiono regresje funkcjonalne po wdrożeniu Shell Layout: przywrócono widok parametrów (Mode A) oraz system oceniania w widoku szczegółów.
- Zoptymalizowano tryb mediów (Mode C): wdrożono komponent `SlideShow` z dopasowaniem zdjęć do okna i wyeliminowano problem podwójnego przewijania.
- Przywrócono i ulepszono minimapy: dodano dynamiczną mapę do widoku dewelopera oraz przywrócono podgląd lokalizacji w nagłówku inwestycji.
- Ustabilizowano widok Pobieranie: przywrócono przyciski akcji (Szukaj, Pobierz) i zintegrowano je z systemem API oraz nowym systemem ActionBar.
- Skorygowano układ nagłówka: tytuł widoku został wyrównany do lewej strony (obok menu), poprawiając czytelność i nawigację.
- Rozwiązano krytyczny błąd `TypeError: handleRating is not a function` w trybie media poprzez poprawne przekazywanie propsów w gałęziach warunkowych.

## Bar Sushi — 2026-05-04
- Wdrożono stałą strukturę "Shell Layout" z ramowymi paskami nawigacji (Top) i akcji (Bottom) zarządzanymi centralnie w `App.jsx`.
- Zintegrowano system powiadomień `NotificationCenter` (zadania w tle) oraz `StatusMessenger` (systemowe toasty) w górnym pasku.
- Ujednoliceno system filtrowania i wyszukiwania, przenosząc wszystkie kontrolki widoków listy do ustandaryzowanego komponentu `ActionBar`.
- Przeprowadzono głęboką refaktoryzację widoków (`view-list`, `view-dashboard`, `view-dev-list`), usuwając redundantny kod i lokalne toolbary.
- Zoptymalizowano responsywność interfejsu poprzez media queries i dynamiczne zarządzanie widocznością slotów na urządzeniach mobilnych.
- Wzmocniono stabilność UI poprzez mechanizm **Dependency Guarding**, zapewniający pełną gotowość komponentów przed renderowaniem w Babel Standalone.
- Wprowadzono system raportowania błędów frontendu do serwera (`/api/ui-error`) z zapisem do `logs/ui_errors.log`.

## Sklepik szkolny — 2026-05-04
- Przeprowadzono głęboką dekompozycję monolitycznego pliku `components.jsx` na moduły: `core`, `ratings`, `modules` i `analytics`.
- Zmigrowano wszystkie style inline do zewnętrznych arkuszy CSS (`global.css`, `components.css`, `views.css`) z użyciem semantycznych klas.
- Wprowadzono system zmiennych CSS (`_variables.css`) dla kolorów, siatki 8px oraz pełną obsługę motywów Light/Dark bez wstrzykiwania JS.
- Zaimplementowano zautomatyzowane testy regresji wizualnej (`test-regression.js`) porównujące style obliczone z wzorcem baseline.
- **UI Stability & Recovery**: Rozwiązano krytyczne błędy race condition w środowisku Babel Standalone poprzez bezpieczną ekstrakcję globali wewnątrz komponentów.
- Wdrożono system **Diagnostic Overlay** (Czerwony Ekran Śmierci) do natychmiastowego przechwytywania i wyświetlania błędów runtime w UI.
- Dodano mechanizm **Dependency Waiter**, upewniający się o załadowaniu wszystkich modułów przed startem renderowania Reacta.

## Witryna sklepowa — 2026-05-03
- Zsynchronizowano `theme.jsx` mit Design Systemem, wprowadzając tokeny CSS i ujednolicając siatkę (8px/16px) we wszystkich widokach.
- Wzbogacono warstwę semantyczną interfejsu poprzez dodanie precyzyjnych atrybutów `data-component` do interaktywnych elementów i sekcji informacyjnych.
- Przeprowadzono refaktoryzację struktury UI, wydzielając logikę analityczną i metadane do reużywalnych komponentów w `components.jsx`.
- Zoptymalizowano pliki widoków (Dashboard, List, Detail) poprzez redukcję nadmiarowego kodu i wprowadzenie uniwersalnych komponentów sterujących.
- Potwierdzono stabilność systemu i poprawność komunikacji przez `DataBus` oraz bezbłędne działanie filtrów i nawigacji po zmianach.

## Dania Fast Food — 2026-05-03
- Zaimplementowano fundamenty architektury modułowej: BaseModule, ModuleErrorBoundary i SkeletonModule.
- Dodano system typowania i walidacji ModuleSchemaValidator dla wejść do modułów.
- Wyciągnięto logikę dostępu do danych w extractModuleContext i zintegrowano ją w widokach listy i szczegółów inwestycji.
- Stworzono uniwersalny ModuleWrapper pozwalający na łatwe podpinanie komponentów pod nową architekturę.
- Dodano responsywność modułów przez ResizeObserver przekazujący szerokość kontenera.
- Zrefaktoryzowano i podpięto MiniMap jako udany test nowej architektury.

## Domowe obiady — 2026-05-03
- Wdrożono infrastrukturę Szyny Danych (DataBus) opartą na React Context, umożliwiającą globalną wymianę stanu między niezależnymi widokami.
- Stworzono system dynamicznych raportów sterowanych plikami JSON z obsługą filtrów (miasto, deweloper, promień geograficzny).
- Zaimplementowano silnik filtrowania inwestycji po stronie serwera zintegrowany z definicjami raportów.
- Wprowadzono modularny system prezentacji danych w raportach z rejestrem komponentów (ModuleRegistry).
- Dodano zaawansowane moduły analityczne: interaktywne mapy punktowe (HERE Maps) oraz wykresy trendów i korelacji (Chart.js).
- Zintegrowano widok szczegółowy z szyną danych, publikując informacje o bieżącej inwestycji i jej sąsiedztwie.

## Kawiarnia — 2026-05-03
- Utworzono centralną bazę danych deweloperów w `Public/USIdev` oraz system unikalnych identyfikatorów `usi_dev_id` i `usi_inv_id`.
- Wdrożono mechanizm automatycznego pobierania surowych profili deweloperów oraz ekstrakcję metadanych (NIP, KRS, adres).
- Zaimplementowano heurystykę wykrywania podobieństw deweloperów, generującą sugestie powiązań dla rekordów z różnych portali.
- Stworzono nowoczesny widok listy i szczegółów dewelopera, integrując go z istniejącym systemem nawigacji.
- Dodano zaawansowaną analitykę "Zasięg inwestycji" z automatyczną agregacją statystyk (liczba mieszkań, oceny) per miasto.
- Wprowadzono system `JobManager` do obsługi asynchronicznych zadań w tle (np. skanowanie portali) z wizualizacją postępu w UI.

## Lodziarnia — 2026-05-03
- Zaimplementowano ujednolicony mechanizm Discovery dla portali RP, Otodom i TabelaOfert wspierający skanowanie globalne.
- Wdrożono mechanizm Stage Flattening dla RynekPierwotny, umożliwiający automatyczne wykrywanie i separację etapów inwestycji.
- Dodano scentralizowany RateLimiter w klasie Fetcher z dedykowanymi opóźnieniami dla domen (np. 3s dla Otodom).
- Przebudowano widok Pobieranie: wprowadzono dwupoziomowy Toolbar, interaktywne SourceBadge oraz masowe pobieranie z paskiem postępu.
- Zoptymalizowano system kart poprzez komponent StandardCard i wdrożono automatyczny wybór najwyższej rozdzielczości zdjęć.
- Usprawniono skraper TabelaOfert o obsługę JSON-LD, fallback geokodowania HERE Maps i czyszczenie nazewnictwa.

## Pizzeria — 2026-05-02
- Odświeżono nawigację UI: dodano wysuwaną szufladę (Drawer) z obsługą trybu jasnego/ciemnego i ulepszono spójność designu.
- Przeniesiono silnik scrapowania na bibliotekę `Scrapling` oraz wdrożono mechanizm bezpiecznej aktualizacji rekordów JSON z logowaniem zmian.
- Zaimplementowano w pełni stylizowaną mapę Dashboardu (HERE Maps) z precyzyjnym oznaczaniem inwestycji.
- Zoptymalizowano widok szczegółów: nowe HeroBand z ocenami waźonymi USI oraz przebudowany układ kolumn i udogodnień.
- Stworzono dedykowaną podstronę "Pobieranie" do zarządzania nowościami z portali (RP, Otodom) wraz z dedykowanymi endpointami API.
- Opracowano i sformalizowano dokumentację Design Systemu oraz nazewnictwo komponentów frontendu.

## Buda z kebabem — 2026-05-01
- Zaimplementowano modułowe scrapery dla Otodom, RynekPierwotny i TabelaOfert z obsługą Fetchera (curl_cffi i ScrapperAI).
- Wdrożono integrację z mapami HERE (minimapy, stylizacja, synchronizacja współrzędnych).
- Stworzono responsywny interfejs użytkownika (React) z widokiem listy 6000+ inwestycji, filtrowaniem i zaawansowanym widokiem detali.
- Wprowadzono system oceniania inwestycji w kategoriach oraz automatyczne obliczanie oceny złożonej.
- Zaimplementowano audyt zmian (created_at/updated_at) oraz mechanizm rozdzielania rekordów dualnych (RP+OTO).
- Zoptymalizowano strukturę danych i schematy JSON oraz usprawniono proces importu z CSV (USImaster).
