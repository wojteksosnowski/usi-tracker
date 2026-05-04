# TODO

## Bieżący kamień milowy: Refactor Views with Shared Grids

Celem tego kamienia milowego jest ujednolicenie sposobu wyświetlania danych w widokach Dashboardu i Raportów poprzez wprowadzenie współdzielonych komponentów `DataGrid` i ustandaryzowanie logiki filtrowania/agregacji.

### Krok B01
**Definicja DataGrid Component:** Stworzenie generycznego komponentu do wyświetlania zestawów danych (inwestycje, statystyki) z wbudowanym sortowaniem i wirtualizacją.

- [ ] Implementacja bazowego `DataGrid` w `python_worker/ui/components/modules.jsx`.
- [ ] Obsługa definicji kolumn (renderery, szerokości, typy danych).
- [ ] Test: Wyświetlenie prostej tabeli inwestycji z użyciem `DataGrid`.

### Krok B02
**Migracja Raportów na DataGrid:** Zastąpienie statycznych tabel w widoku raportów nowym systemem gridowym.

- [ ] Refaktoryzacja `view-reports.jsx` — integracja `DataGrid` z definicjami raportów JSON.
- [ ] Wdrożenie dynamicznego sortowania po stronie klienta.
- [ ] Test: Weryfikacja działania raportu "Top Inwestycje" w nowym gridzie.

### Krok B03
**Migracja Dashboardu na DataGrid:** Ujednolicenie list "Top Inwestycje" i statystyk kategorii na dashboardzie.

- [ ] Zastosowanie `DataGrid` dla sekcji Top Investments w `view-dashboard.jsx`.
- [ ] Ustandaryzowanie rendererów (MiniMap, StarScore) między listą a dashboardem.
- [ ] Test: Porównanie wydajności dashboardu przed i po migracji.

## Następny kamień milowy: Improve DataBus Readership

- **Goal:** Refactor components to directly consume variables from DataBus instead of relying heavily on props. This will enforce its role as a centralized state.

## Przyszłe kamienie milowe

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

## Archiwum: Sprzatanie

Naprawa regresji po wdrożeniu Shell Layout.

### Krok B01-B05 (Zrealizowane)
- Przywrócenie widoku parametrów (Mode A) i systemu oceniania.
- Optymalizacja galerii (SlideShow) i naprawa przewijania w Mode C.
- Przywrócenie minimap w szczegółach i u deweloperów.
- Stabilizacja widoku Pobieranie (przyciski akcji, Discovery API).
- Korekta układu nagłówka (wyrównanie do lewej).

**Podsumowanie:** Kamień milowy zakończony sukcesem. Przywrócono pełną funkcjonalność aplikacji, eliminując krytyczne błędy (TypeError) oraz regresje wizualne powstałe podczas dużej refaktoryzacji. System jest teraz stabilny i gotowy na dalszą rozbudowę modułów analitycznych.

## Archiwum: Bar Sushi

Ramowa struktura layoutu (Shell Layout)

### Krok B01-B08 (Zrealizowane)
- Wdrożenie `NavbarShell` i `ActionBar`.
- Integracja `NotificationCenter` i `StatusMessenger`.
- Refaktoryzacja `App.jsx` i ujednolicenie filtrów.
- Optymalizacja RWD i stabilizacja UI (Dependency Guarding).

**Podsumowanie:** Kamień milowy został zrealizowany, wprowadzając nowoczesną, ramową strukturę interfejsu (Top Bar | Scroll Area | Bottom Bar). Aplikacja zyskała na spójności wizualnej i stabilności technicznej dzięki mechanizmom obronnym w środowisku Babel Standalone.

## Archiwum: Sklepik szkolny

Refactoring Styles to SCSS
