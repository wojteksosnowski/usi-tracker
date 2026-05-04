# TODO

## Bieżący kamień milowy: Pobieranie
### Krok B01: Refaktoryzacja UI strony Pobieranie
Uproszczenie układu strony, naprawa interakcji i integracja z Design Systemem.
- [ ] Naprawa pola URL i przycisku szukaj.
- [ ] Implementacja selektora portali jako `FilterGroup`.
- [ ] Refaktoryzacja `ActionBar` (przeniesienie filtrów i akcji).
- [ ] Test: Weryfikacja działania przycisków skanowania/pobierania i układu ActionBar.

### Krok B02: Integracja z Design Systemem
Spójność wizualna modułów pobierania.
- [ ] Dostosowanie stylów komponentów na stronie Pobieranie.
- [ ] Test: Weryfikacja spójności z innymi widokami.

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
