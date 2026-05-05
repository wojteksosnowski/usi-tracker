# TODO

## Bieżący kamień milowy: Długoterminowe i QA

### Krok B01
Analiza i projekt systemu subskrypcji w `DataBus` — określenie sposobu powiadamiania komponentów o zmianach tylko wybranych fragmentów stanu (selektory).
- [x] Zdefiniować interfejs subskrypcji w DataBusProvider. (Zrealizowano: zaimplementowano optymalizację DataBus w poprzedniej iteracji).

### Krok B02
Implementacja `useDataBusSelector` — stworzenie hooka pozwalającego komponentom na subskrypcję konkretnych ścieżek (np. `filters.search`) bez rerenderingu przy zmianie innych danych.
- [x] Wdrożyć mechanizm shallowCompare dla selektorów. (Zrealizowano: wdrożono optymalizacje wydajnościowe w DataBus).

### Krok B03
Wdrożenie mechanizmu `USI Storyboard` — lekkie narzędzie wewnątrz aplikacji do izolowanego testowania komponentów `atomic` i `modules` z mockowanymi danymi.
- [ ] Stworzyć widok 'storyboard' w App.jsx.

### Krok B04
Dekompozycja i testy izolacji dla komponentów `DataGrid` i `MapModule` — migracja do nowego systemu Storyboard i weryfikacja stabilności w izolacji.
- [ ] Przygotować zestawy danych testowych (fixtures) dla modułów.

### Krok B05
Testy regresji wydajnościowej — porównanie liczby rerenderingów przed i po wdrożeniu selektorów w widoku `ViewList`.
- [ ] Wykonać pomiary wydajności w konsoli przy użyciu React Profiler.

## Następny kamień milowy: Scoped Namespaces

## Przyszłe kamienie milowe

- **Introduce Asynchronous Dispatchers:** - Extend `setVariable` to handle async reducers to allow dynamic fetch-and-set operations.
- **DevTools Compatibility:** - Log state updates to debug data flow easily.
- **Dynamic Module Registry:** - Register modules dynamically with a registry for runtime extensibility.
- **Encapsulate Module Context Logic:** - Replace repetitive validation logic with a shared `useModuleContext` hook.
- **Support Chained Modules:** - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
- **Standardize Module Specs:** - Define a JSON-based module specification to manage inputs and outputs systematically.
- **Wikipednia:** — Modul - Dodawanie kontekstu do rekordów inwestycji.
- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.
