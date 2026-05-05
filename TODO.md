# TODO

## Bieżący kamień milowy: Optymalizacja Logiki Frontendowej

### Krok B01
Wdrożenie hooka `useApi` — centralizacja zapytań HTTP i prosta warstwa cache'owania.
- [ ] Zaimplementować generyczny hook `useApi` obsługujący fetch, błędy i stan ładowania.

### Krok B02
Unifikacja logiki ocen — eliminacja redundancji między widokami a serwisem.
- [ ] Przenieść logikę `handleRating` i obliczenia `ocenaLog` do wspólnego modułu serwisowego.

### Krok B03
Optymalizacja subskrypcji DataBus — selektory ograniczające rerendery.
- [ ] Wprowadzić mechanizm `shallowCompare` lub selektory w `useDataBus` dla namespace'ów.

### Krok B04
Testy jednostkowe logiki transformacji danych.
- [ ] Wdrożyć framework testowy (np. proste asercje w JS) dla kluczowych parserów API.

## Następny kamień milowy: Długoterminowe i QA

### Krok N01
Analiza i projekt systemu subskrypcji w `DataBus` — określenie sposobu powiadamiania komponentów o zmianach tylko wybranych fragmentów stanu (selektory).
- [ ] Zdefiniować interfejs subskrypcji w DataBusProvider.

### Krok N02
Implementacja `useDataBusSelector` — stworzenie hooka pozwalającego komponentom na subskrypcję konkretnych ścieżek (np. `filters.search`) bez rerenderingu przy zmianie innych danych.
- [ ] Wdrożyć mechanizm shallowCompare dla selektorów.

### Krok N03
Wdrożenie mechanizmu `USI Storyboard` — lekkie narzędzie wewnątrz aplikacji do izolowanego testowania komponentów `atomic` i `modules` z mockowanymi danymi.
- [ ] Stworzyć widok 'storyboard' w App.jsx.

### Krok N04
Dekompozycja i testy izolacji dla komponentów `DataGrid` i `MapModule` — migracja do nowego systemu Storyboard i weryfikacja stabilności w izolacji.
- [ ] Przygotować zestawy danych testowych (fixtures) dla modułów.

### Krok N05
Testy regresji wydajnościowej — porównanie liczby rerenderingów przed i po wdrożeniu selektorów w widoku `ViewList`.
- [ ] Wykonać pomiary wydajności w konsoli przy użyciu React Profiler.

## Przyszłe kamienie milowe

- **Scoped Namespaces:** - Use namespaces in variables to prevent key collisions and better organize the state.
- **Introduce Asynchronous Dispatchers:** - Extend `setVariable` to handle async reducers to allow dynamic fetch-and-set operations.
- **DevTools Compatibility:** - Log state updates to debug data flow easily.
- **Dynamic Module Registry:** - Register modules dynamically with a registry for runtime extensibility.
- **Encapsulate Module Context Logic:** - Replace repetitive validation logic with a shared `useModuleContext` hook.
- **Support Chained Modules:** - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
- **Standardize Module Specs:** - Define a JSON-based module specification to manage inputs and outputs systematically.
- **Wikipednia:** — Modul - Dodawanie kontekstu do rekordów inwestycji.
- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.
