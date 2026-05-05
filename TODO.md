# TODO

## Bieżący kamień milowy: DataBus: Zaawansowane funkcje

### Krok B01
Scoped Namespaces: Implementacja przestrzeni nazw w stanie DataBus (np. `filters.investments`, `ui.settings`) w celu uniknięcia kolizji kluczy.
**Plan:** 2026-05-06

### Krok B02
Introduce Asynchronous Dispatchers: Rozszerzenie `setVariable` o obsługę asynchronicznych reducerów w celu umożliwienia operacji typu "fetch-and-set".
**Plan:** 2026-05-06

### Krok B03
DevTools Compatibility: Wdrożenie mechanizmu logowania zmian stanu do konsoli/pliku w celach debugowania przepływu danych.
**Plan:** 2026-05-06

### Krok B04
Dynamic Module Registry: Implementacja rejestru modułów pozwalającego na ich dynamiczne ładowanie i rozszerzalność w czasie wykonywania.
**Plan:** 2026-05-06

### Krok B05
Encapsulate Module Context Logic: Zastąpienie redundantnej logiki walidacji komponentów wspólnym hookiem `useModuleContext`.
**Plan:** 2026-05-06

### Krok B06
Support Chained Modules: Wdrożenie mechanizmu przekazywania kontekstu do modułów potomnych dla umożliwienia wizualizacji hierarchicznych.
**Plan:** 2026-05-06

### Krok B07
Standardize Module Specs: Opracowanie i wdrożenie specyfikacji JSON dla modułów, umożliwiającej systematyczne zarządzanie wejściami/wyjściami.
**Plan:** 2026-05-06

## Następny kamień milowy: System Modułów: Rozszerzenia

## Przyszłe kamienie milowe

- **Optymalizacja Logiki Frontendowej:** - 
       * Centralizacja API Fetching: Rekomendowany hook useApi (generyczny
         klient) nie został w pełni wdrożony — komponenty nadal korzystają z
         dedykowanych funkcji refetch lub bezpośrednich wywołań fetch w
         useEffect.
       * Konsolidacja logiki ocen: Choć avgRating i ocenaLog są w data.jsx, w
         widokach szczegółowych (view-detail.jsx) wciąż może występować
         redundancja w obsłudze formularzy ocen.

- **Długoterminowe i QA:** - 
       * DataBus Subscriptions: Brak mechanizmu subskrypcji zdarzeń
         (reagowanie tylko na zmiany konkretnych kluczy).
       * Storybook / Testy izolacji: W strukturze plików nie widać narzędzi do
         testowania izolowanych modułów UI.

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
