# TODO

## Zrealizowany kamień milowy: Długoterminowe i QA

### Krok B01
Analiza i projekt systemu subskrypcji w `DataBus` — określenie sposobu powiadamiania komponentów o zmianach tylko wybranych fragmentów stanu (selektory).
- [x] Zdefiniować interfejs subskrypcji w DataBusProvider.

### Krok B02
Implementacja `useDataBusSelector` — stworzenie hooka pozwalającego komponentom na subskrypcję konkretnych ścieżek (np. `filters.search`) bez rerenderingu przy zmianie innych danych.
- [x] Wdrożyć mechanizm shallowCompare dla selektorów.

### Krok B03
Wdrożenie mechanizmu `USI Storyboard` — lekkie narzędzie wewnątrz aplikacji do izolowanego testowania komponentów `atomic` i `modules` z mockowanymi danymi.
- [x] Stworzyć plik `view-storyboard.jsx` z podstawową architekturą rejestru "stories" i nawigacją.
- [x] Zintegrować widok `ViewStoryboard` w `app.jsx` (stan, NavDrawer, renderowanie).
- [x] Dodać początkowe "opowieści" (stories) dla komponentów `Icon`, `Loading` i `ListCard` z mockami.
- [x] Zaimplementować panel "Knobs" do dynamicznej zmiany propsów w Storyboardzie.
- [x] Zweryfikować działanie izolacji i obsługę błędów w nowym widoku.

### Krok B04
Dekompozycja i testy izolacji dla komponentów `DataGrid` i `MapModule` — migracja do nowego systemu Storyboard i weryfikacja stabilności w izolacji.
- [x] Przygotować zestawy danych testowych (fixtures) dla `DataGrid` oraz `MapModule`.
- [x] Zarejestrować "opowieść" dla `DataGrid` w Storyboardzie z listą mockowanych inwestycji.
- [x] Zarejestrować "opowieść" dla `MapModule` z danymi o lokalizacji i weryfikacją API HERE.
- [x] Zrefaktoryzować komponenty pod kątem lepszej izolacji (wstrzykiwanie zależności przez propsy).
- [x] Zweryfikować poprawność renderowania i reakcję na zmiany "Knobs" dla obu modułów.

### Krok B05
Testy regresji wydajnościowej — porównanie liczby rerenderingów przed i po wdrożeniu selektorów w widoku `ViewList`.
- [x] Wykonać pomiary wydajności w konsoli przy użyciu React Profiler.

## Bieżący kamień milowy: Scoped Namespaces

### Krok B01
Audyt obecnych zmiennych w DataBus — identyfikacja konfliktów i mapowanie płaskiej struktury na logiczne przestrzenie nazw (np. `ui.*`, `data.*`, `auth.*`).

### Krok B02
Migracja stanu globalnego na system zagnieżdżony — refaktoryzacja `DataBusProvider` i `setVariable` dla pełnej obsługi głębokich ścieżek we wszystkich widokach.

### Krok B03
Implementacja `useNamespace` hooka — narzędzie do tworzenia lokalnych aliasów dla fragmentów szyny danych, upraszczające dostęp wewnątrz dużych modułów.

### Krok B04
Testy integralności i migracja widoków — weryfikacja czy wszystkie komponenty poprawnie korzystają z nowych ścieżek po reorganizacji stanu.

## Następny kamień milowy: Asynchronous Dispatchers

## Przyszłe kamienie milowe

- **DevTools Compatibility:** - Log state updates to debug data flow easily.
- **Dynamic Module Registry:** - Register modules dynamically with a registry for runtime extensibility.
- **Encapsulate Module Context Logic:** - Replace repetitive validation logic with a shared `useModuleContext` hook.
- **Support Chained Modules:** - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
- **Standardize Module Specs:** - Define a JSON-based module specification to manage inputs and outputs systematically.
- **Wikipednia:** — Modul - Dodawanie kontekstu do rekordów inwestycji.
- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.