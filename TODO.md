# TODO

## Bieżący kamień milowy: Pobieranie
### Krok B16: Fix: RP Ingestion & Developer Mapping
Rozwiązanie problemu brakujących danych w RP i błędnego przypisania do 'nieznany-deweloper'.
- [x] Discovery: Dodanie nazwy dewelopera i `vendor_slug` do wyników RP.
- [x] Scraper: Zapewnienie pobierania i zapisu 'drugiego JSONa' (galerii) do pliku raw.
- [x] Consistency: Usunięcie nadpisywania `developer_slug` w scraperze (zachowanie spójności folderów USIdata i USI).
- [x] Test: Rejestracja nowej inwestycji z RP i weryfikacja kompletu zdjęć oraz surowego JSONa galerii.
**Podsumowanie:** Wyeliminowano błąd 'nieznany-deweloper' dla RynekPierwotny.pl poprzez wzbogacenie danych odkrywania. Przywrócono pełną kompletność surowych plików JSON (w tym galerii), co pozwala na poprawną unifikację wszystkich zdjęć i metadanych.

### Krok B15: Naprawa regresji pobierania (Raw JSON & Full Sync)
Przywrócenie pełnego mechanizmu pobierania danych i surowych plików JSON.
- [x] Backend: Normalizacja nazw portali (`rp`, `oto`, `to`) w endpointcie `/api/register`.
- [x] Fix: Zapewnienie poprawnego zapisu `sources` w szkielecie inwestycji.
- [x] Integracja: Weryfikacja uruchomienia pełnego procesu `update_investment` przez asynchronicznego joba.
- [x] Test: Ponowna rejestracja 'Lawinowa 18' i sprawdzenie obecności plików `raw_*.json` oraz kompletu zdjęć.
**Podsumowanie:** Naprawiono regresję spowodowaną niezgodnością identyfikatorów portali. Teraz asynchroniczny job poprawnie rozpoznaje źródło inwestycji, co pozwala mu pobrać surowy plik JSON z portalu, wyekstrahować komplet danych (ceny, daty, udogodnienia) oraz wszystkie zdjęcia, zgodnie z pierwotną specyfikacją systemu.

### Krok B14: Automatyczne mapowanie deweloperów i Smart-Ingestion
Eliminacja ręcznego wyboru dewelopera i automatyzacja procesu rejestracji.
- [x] Backend: Implementacja auto-generowania `dev_slug` i profilu dewelopera na podstawie danych z Discovery.
- [x] UI: Usunięcie selektora dewelopera z ActionBar i widoku Pobieranie.
- [x] Fix: Zapewnienie przesyłania pełnych danych URL do asynchronicznego joba (naprawa pobierania zdjęć).
- [x] Test: Rejestracja nowej inwestycji jednym kliknięciem i weryfikacja pobrania kompletu danych (w tym zdjęć).
**Podsumowanie:** Uproszczono proces do poziomu 'One-Click Ingestion'. System teraz automatycznie rozpoznaje dewelopera, tworzy jego profil w razie potrzeby i uruchamia pełny proces pobierania danych (w tym mediów), eliminując błędy typu 'brak zdjęć' i skracając czas rejestracji.

### Krok B13: Naprawa interaktywności przycisków (Feedback UX)
Rozwiązanie problemu 'braku reakcji' przycisków Pobierz.
- [x] Fix: Usunięcie blokady `disabled` przy braku dewelopera (pozwala na uruchomienie `onClick`).
- [x] UX: Zapewnienie wyświetlenia alertu 'Najpierw wybierz dewelopera' zamiast cichego blokowania.
- [x] Test: Weryfikacja reakcji przycisku przy braku wybranego dewelopera.
**Podsumowanie:** Naprawiono krytyczny błąd użyteczności. Przyciski są teraz zawsze aktywne dla zdarzeń kliknięcia, co pozwala systemowi poinformować użytkownika o konieczności wybrania dewelopera zamiast sprawiać wrażenie niedziałającego interfejsu.

### Krok B12: Asynchroniczne pobieranie i system powiadomień
Naprawa przycisków Pobierz i integracja z systemem zadań (JobManager).
- [x] Fix: Naprawa parametrów i URL w `handleRegister` (view-download.jsx).
- [x] Backend: Migracja rejestracji na asynchroniczny `job_manager` w `ui_server.py`.
- [x] DataBus: Implementacja automatycznego odpytywania (polling) stanu zadań przy aktywnych procesach.
- [x] UI: Integracja `NotificationCenter` z procesem pobierania nowej inwestycji.
- [x] Test: Weryfikacja pojawienia się paska postępu po kliknięciu 'Pobierz'.
**Podsumowanie:** Uruchomiono pełny system asynchronicznego pobierania. Rejestracja inwestycji nie blokuje już interfejsu, a użytkownik otrzymuje natychmiastową informację zwrotną w postaci paska postępu w ActionBarze, który aktualizuje się automatycznie do zakończenia procesu.

### Krok B02: Integracja z Design Systemem
Spójność wizualna modułów pobierania.
**Plan:** 2026-05-04

- [x] Dostosowanie stylów komponentów na stronie Pobieranie.
- [x] Test: Weryfikacja spójności z innymi widokami.

### Krok B03: Unifikacja komponentów listy
Użycie wspólnego komponentu ListCard w widokach Inwestycje i Pobieranie w celu eliminacji redundancji.
- [x] Wydzielenie `ListCard` do osobnego pliku `components/views/ListCard.jsx`.
- [x] Rozszerzenie `ListCard` o obsługę customowego stopki i wskaźnika 'NOWE'.
- [x] Refaktoryzacja `view-list.jsx` i `view-download.jsx` na użycie wspólnego komponentu.
- [x] Test: Weryfikacja spójności wizualnej i funkcjonalnej obu widoków.
**Podsumowanie:** Całkowicie wyeliminowano duplikację kodu prezentacji kart. `ListCard` stał się uniwersalnym komponentem zarejestrowanym w systemie, obsługującym zarówno dane produkcyjne z ocenami, jak i surowe dane z Discovery z przyciskiem pobierania i badge'em 'NOWE'.

### Krok B06: Przełącznik trybu widoku w Pobieranie
Dodanie możliwości przełączania między widokiem siatki a listą dla wyników wyszukiwania.
- [x] Dodanie stanu `downloadMode` do globalnego DataBus.
- [x] Implementacja przełącznika `mode-toggle` w lewej części ActionBar dla widoku Pobieranie.
- [x] Synchronizacja `DataGrid` w `view-download.jsx` z nowym stanem.
- [x] Fix: Zdefiniowano brakujące kolumny (`columns`) dla `DataGrid` w trybie listy, co umożliwiło poprawne przełączanie widoków.
- [x] Test: Weryfikacja poprawnego renderowania wyników w obu trybach (Siatka/Lista).
**Podsumowanie:** Wprowadzono przełącznik trybu widoku (Grid/List) do ActionBar w widoku Pobieranie, zapewniając pełną spójność funkcjonalną z głównym widokiem inwestycji.

### Krok B08: Zwiększenie gęstości (Expert UI) i responsywność
Optymalizacja siatki wyników dla dużych monitorów przy zachowaniu elastyczności.
- [x] Refaktor `DataGrid.jsx`: Implementacja dynamicznego wyliczania `itemsPerRow` na podstawie szerokości kontenera i `minCardWidth`.
- [x] Synchronizacja wirtualizacji z dynamiczną liczbą kolumn (poprawne obliczenia rzędów).
- [x] Konfiguracja widoku Pobieranie (`minCardWidth: 180`), co pozwala uzyskać ok. 7-9 kolumn na szerokich ekranach.
- [x] Test: Weryfikacja płynnego przeskakiwania liczby kolumn przy zmianie rozmiaru okna oraz poprawności przewijania.
**Podsumowanie:** Wprowadzono inteligentny, responsywny grid. Liczba kolumn dostosowuje się teraz automatycznie do dostępnej szerokości, co pozwala na znacznie gęstsze upakowanie informacji na dużych ekranach (Expert UI) przy jednoczesnym zachowaniu poprawnego działania wirtualizacji listy.

### Krok B11: Całkowite wyczyszczenie widoku (Full Shell Layout)
Przeniesienie ostatniego elementu sterującego (wybór dewelopera) do ActionBar.
- [x] Dodanie stanu `downloadSelectedDev` do DataBus.
- [x] Przeniesienie selektora dewelopera do prawej sekcji ActionBar w `app.jsx`.
- [x] Usunięcie ostatniego lokalnego paska narzędzi z `view-download.jsx`.
- [x] Test: Weryfikacja możliwości wyboru dewelopera i poprawnej rejestracji inwestycji.
**Podsumowanie:** Ukończono migrację do modelu Shell Layout. Widok Pobieranie jest teraz całkowicie pozbawiony własnych kontrolek, co oddaje 100% powierzchni na prezentację danych. Wszystkie funkcje sterujące (URL, Portal, Opcje, Deweloper, Tryb widoku) są scentralizowane w globalnym ActionBarze.



## Następny kamień milowy: Zaplecze
Separacja warstw (API / Business Logic / Infrastructure)
  Obecnie ui_server.py jest "sercem i mózgiem" interfejsu, co utrudnia
  testowanie i utrzymanie.
   * Extract JobManager: Wydziel JobManager do python_worker/jobs.py. Jest to
     generyczna infrastruktura, która nie powinna "zaśmiecać" definicji tras
     HTTP.
   * Flask Blueprints: Podziel API na moduły:
       * /api/investments/* -> python_worker/api/investments.py
       * /api/jobs/* -> python_worker/api/jobs.py
       * /api/reports/* -> python_worker/api/reports.py
   * Modular Adapters: Podziel adapters.py na katalog python_worker/adapters/
     z plikami rp.py, otodom.py, to.py oraz base.py. Umożliwi to łatwiejsze
     dodawanie nowych źródeł danych bez ryzyka regresji w istniejących.

## Przyszłe kamienie milowe

- **Frontend:** - Atomizacja komponentów i "Window Registry"
  Architektura Babel Standalone powoduje, że komponenty są "wstrzykiwane" do
  window. Jest to podatne na race-conditions (co odnotowano w MEMORY.md).
   * Split core.jsx: Rozbij na atomowe komponenty w katalogu
     ui/components/core/ (np. Badge.jsx, Spinner.jsx).
   * Formalized Registry: Zamiast ręcznego przypisywania window.MyComp = ...,
     wprowadź prosty helper registerComponent('MyComp', MyComp), który mógłby
     np. logować ostrzeżenia przy próbie nadpisania lub brakujących
     zależnościach.
   * Extract Logic from Views: Pliki takie jak view-detail.jsx (12KB) powinny
     wydzielać swoje sekcje (np. DetailAmenities, DetailHistory) do mniejszych
     plików w ui/components/detail/.

- **Remanent:** - Stabilizacja i Design System
   * Dynamic CSS Extraction: Komponenty takie jak DesignCanvas wstrzykują
     style JS-em. Przy tej skali warto przenieść to do dedykowanych plików
     .css w ui/styles/, aby uniknąć problemów z Content Security Policy (CSP)
     i czytelnością kodu JSX.
   * SafeRender Pattern: Rozszerz wzorzec safeRender (z Twojej pamięci
     projektowej) o scentralizowany DataBoundary dla danych z API, który
     automatycznie waliduje typy przed przekazaniem ich do komponentów widoku.

- **Scoped Namespaces:** - Use namespaces in variables to prevent key collisions and better organize the state.
- **Introduce Asynchronous Dispatchers:** - Extend `setVariable` to handle async reducers to allow dynamic fetch-and-set operations.
- **DevTools Compatibility:** - Log state updates to debug data flow easily.
- **Dynamic Module Registry:** - Register modules dynamically with a registry for runtime extensibility.
- **Encapsulate Module Context Logic:** - Replace repetitive validation logic with a shared `useModuleContext` hook.
- **Support Chained Modules:** - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
- **Standardize Module Specs:** - Define a JSON-based module specification to manage inputs and outputs systematically.
- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.
- **Wikipednia:** — Dodawanie kontekstu do rekordów inwestycji.

## Zakończone kamienie milowe

### Front sklepu: Atomizacja komponentów i "Window Registry"

- **Goal:** Split core components, implement a formal registry helper, and extract logic from large view files to prevent race-conditions and improve maintainability.

- Krok C01: Implementacja Registry Helpera
Stworzenie narzędzia `window.usiRegister` do bezpiecznego rejestrowania i pobierania komponentów/hooków z walidacją zależności.
- [x] Implementacja `usiRegister` w `registry.js`.
- [x] Integracja z `index.html` (ładowanie rejestru jako pierwszy skrypt).
- [x] Test: Weryfikacja rejestracji i pobierania komponentów.
**Podsumowanie:** Zaimplementowano globalny rejestr `window.usiRegister` oraz zintegrowano go z systemem ładowania modułów, eliminując problemy z race-conditions w środowisku Babel Standalone.

- Krok C02: Atomizacja Core Components
Rozbicie `core.jsx` i `modules.jsx` na mniejsze, dedykowane pliki (np. `Icon.jsx`, `Button.jsx`, `StandardCard.jsx`).
- [x] Wydzielenie `Icon`, `Spinner` i `Loading` do `atomic/`.
- [x] Wydzielenie `DataGrid` i `ModuleErrorBoundary`.
- [x] Migracja `core.jsx` i `modules.jsx` do `usiRegister`.
- [x] Test: Weryfikacja renderowania atomowych komponentów.
**Podsumowanie:** Wydzielono `Icon`, `Spinner`, `LoadingScreen`, `ModuleErrorBoundary` i `DataGrid` do osobnych plików atomowych. Przeprowadzono pełną migrację `core.jsx` i `modules.jsx` do systemu `usiRegister`.
- [x] Wydzielenie komponentu `DetailsViewA` do pliku `python_worker/ui/components/views/DetailViewA.jsx` i rejestracja w `usiRegister`.
- [x] Wydzielenie komponentu `DetailsViewC` do pliku `python_worker/ui/components/views/DetailViewC.jsx` i rejestracja w `usiRegister`.
- [x] Refaktoryzacja `python_worker/ui/view-detail.jsx` do roli czystego orchestratora, delegującego renderowanie do wydzielonych komponentów.
- [x] Aktualizacja `python_worker/ui/index.html` o nowe ścieżki komponentów widoków.
- [x] Test: Weryfikacja płynnego przejścia między trybami widoku A i C w `view-detail.jsx`.
**Podsumowanie:** Zweryfikowano poprawność renderowania oraz przejść między widokami A (DetailsViewA) i C (DetailsViewC). Architektura rejestru komponentów działa stabilnie dla widoku szczegółowego.

**Podsumowanie:** Dekompozycja widoku szczegółów zakończona sukcesem; komponenty `DetailsA` (jako `DetailsViewA`) oraz `ModeC` (jako `DetailsViewC`) zostały wydzielone do `components/views/` i zarejestrowane. `view-detail.jsx` pełni teraz rolę lekkiego orchestratora.

### Improve DataBus Readership

Refactor components to directly consume variables from DataBus instead of relying heavily on props. This will enforce its role as a centralized state.

#### Krok B01
**Centralizacja stanu filtrowania:** Przeniesienie stanu `search`, `filterDev`, `filterStatus`, `activeSources`, `activeCities` z `App` do DataBus.
- [x] Implementacja domyślnych wartości filtrów w `data.jsx`.
- [x] Aktualizacja `App` w `app.jsx` tak, aby pobierał te zmienne z `useDataBus`.
- [x] Test: Zmiana filtra w UI musi być widoczna w DataBus i wpływać na inne komponenty.

#### Krok B02
**Subskrypcja widoków na DataBus:** Refaktoryzacja widoków `view-list.jsx` i `view-dashboard.jsx` tak, aby pobierały przefiltrowane dane bezpośrednio z DataBus (`visibleInvestments`) zamiast przez propsy.
- [x] Usunięcie przekazywania `filteredInvestments` jako props do `ListGrid`.
- [x] Implementacja `useDataBus` wewnątrz `ListGrid`.
- [x] Test: Weryfikacja czy lista reaguje na globalne zmiany filtrów bez pośrednictwa propsów App.

#### Krok B03
**Asynchroniczne akcje w DataBus:** Rozszerzenie `setVariable` o obsługę akcji asynchronicznych (np. `fetchAndSetInvestments`).
- [x] Refaktoryzacja `data.jsx` w celu wsparcia asynchronicznych dispatcherów.
- [x] Przeniesienie logiki `refetch` z `app.jsx` do DataBus.
- [x] Test: Wywołanie odświeżenia danych z dowolnego komponentu za pomocą DataBus.

**Podsumowanie:** Całkowicie zrefaktoryzowano system przepływu danych. Logika ładowania (refetch) oraz filtrowania inwestycji została przeniesiona do DataBusProvider, który stał się jedynym źródłem prawdy. App.jsx został odciążony i pełni teraz rolę czystego shella nawigacyjnego, a widoki (List, Dashboard) subskrybują dane bezpośrednio z szyny.
