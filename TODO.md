# TODO

## Bieżący kamień milowy: Optymalizacja Logiki Frontendowej

### Krok B01
Wdrożenie hooka `useApi` — centralizacja zapytań HTTP i prosta warstwa cache'owania.
**Plan:** 2026-05-06
- [x] Zdefiniować useApi w python_worker/ui/modules/modules-core.jsx z obsługą stanu loading/error.
- [x] Dodać prosty mechanizm cache (Map) dla zapytań GET wewnątrz hooka.
- [x] Zrefaktoryzować view-list.jsx i view-detail.jsx, aby korzystały z useApi zamiast fetch.
- [x] Zintegrować obsługę błędów z powiadomieniami UI.
- [x] Test: Weryfikacja cache'owania przy nawigacji oraz poprawne wyświetlanie spinnera i błędów.

**Podsumowanie:** Wdrożono hook `useApi` w `modules-core.jsx` z obsługą `globalApiCache`, stanami ładowania/błędu oraz integracją z powiadomieniami `DataBus`. Zrefaktoryzowano kluczowe komponenty (`data.jsx`, `RatingsPanel.jsx`, `view-dev-detail.jsx`, `view-reports.jsx`, `view-download.jsx`), zastępując surowy `fetch` nowym hookiem. Zapewniono omijanie cache dla zapytań mutujących (POST) oraz dla odpytywania statusu zadań.

### Krok B02
Unifikacja logiki ocen — eliminacja redundancji między widokami a serwisem.
**Plan:** 2026-05-06
- [ ] Przenieść funkcje obliczeniowe (ocenaLog) i pomocnicze do python_worker/ui/modules/modules-ui.jsx.
- [ ] Zunifikować obsługę handleRating, zapewniając spójność z DataBus.
- [ ] Zaktualizować RatingsPanel.jsx i widoki szczegółowe, aby korzystały ze wspólnych funkcji.
- [ ] Upewnić się, że aktualizacja ocen poprawnie wywołuje backend przez nową infrastrukturę (useApi).
- [ ] Test: Weryfikacja spójności obliczeń ocen po zmianach w różnych częściach interfejsu.

### Krok B03
Optymalizacja subskrypcji DataBus — selektory ograniczające rerendery.
- [ ] Implementacja shallowCompare w python_worker/ui/data.jsx do porównywania obiektów filtrów.
- [ ] Rozdzielenie DataBusContext na kontekst stanu (danych) i kontekst sterowania (akcji), aby uniknąć zbędnych rerenderów.
- [ ] Wprowadzenie useDataBusSelector(selector), aby komponenty mogły subskrybować tylko fragmenty stanu.
- [ ] Optymalizacja DataGrid.jsx pod kątem użycia selektorów (rerender tylko przy zmianie visibleInvestments).
- [ ] Test: Weryfikacja liczby rerenderów DataGrid przy zmianach w niepowiązanych częściach stanu (np. statusy zadań).

### Krok B04
Testy jednostkowe logiki transformacji danych.
- [ ] Stworzenie ustandaryzowanej struktury TestSuite w python_worker/ui/modules/modules-test.jsx (obsługa opisów, asercji i testów async).
- [ ] Przeniesienie i rozszerzenie testów logiki danych (ocenaLog, avgRating) do nowej struktury.
- [ ] Implementacja testów integracyjnych dla transformacji danych z portali (mockowanie odpowiedzi API RP/OTO/TO).
- [ ] Dodanie wskaźnika "Test Status" w ActionBar, informującego o stanie zdrowia logiki frontendowej.
- [ ] Test: Weryfikacja, czy wprowadzenie błędu w parserze skutkuje natychmiastowym czerwonym statusem w UI.

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
