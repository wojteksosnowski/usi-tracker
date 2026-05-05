# TODO

## Bieżący kamień milowy: System Modułów: Rozszerzenia

### Krok B01
Implementacja modułu `PriceTrendModule` (Chart.js) — wizualizacja historii cen i trendów rynkowych dla wybranych rekordów.
**Plan:** 2026-05-06.
- [ ] Implementacja komponentu PriceTrendModule w python_worker/ui/components/modules.jsx (integracja Chart.js).
- [ ] Dodanie specyfikacji __spec (typy: Color, Number) dla parametrów trendu.
- [ ] Rejestracja modułu w ModuleRegistry.
- [ ] **Test**: Weryfikacja renderowania wykresu w view-reports.jsx przy użyciu runModuleRegistryTest.

### Krok B02
Rozbudowa `MapModule` o interaktywne klastrowanie i synchronizację z filtrami DataBus.
**Plan:** 2026-05-06.
- [ ] Zaktualizować logikę HERE Maps o obsługę klastrów punktów dla dużych zbiorów danych.
- [ ] Dodać dwukierunkową synchronizację: kliknięcie na mapie aktualizuje `currentInvestment` w DataBus.
- [ ] **Test**: Zweryfikować, czy filtrowanie na liście automatycznie odświeża punkty na mapie modułu.

### Krok B03
System szablonów (Presets) w `ModuleRegistry` — predefiniowane układy modułów dla typowych raportów.
**Plan:** 2026-05-06.
- [ ] Dodać obsługę `presets` do `ModuleRegistry` (grupy modułów z domyślną konfiguracją).
- [ ] Stworzyć szablon "Przegląd Dewelopera" i "Analiza Okolicy".
- [ ] **Test**: Wywołać renderowanie szablonu na podstawie identyfikatora w JSON raportu.

### Krok B04
Zaawansowane `ModuleKnobs` — obsługa list rozwijanych, walidacja zakresów i podgląd "na żywo".
**Plan:** 2026-05-06.
- [ ] Rozszerzyć `PropEditors` o typy `Select` (Enums) i `Range`.
- [ ] Wdrożyć natychmiastowe odświeżanie parametrów w podglądzie raportu po zmianie w Knobach.
- [ ] **Test**: Zmienić kolor wykresu przez Knoby i potwierdzić natychmiastową aktualizację.

### Krok B05
Testy stabilności i wydajności — weryfikacja pamięci i stabilności rejestru.
**Plan:** 2026-05-06.
- [ ] Przeprowadzić stress-test dynamicznego przełączania między 10 różnymi raportami.
- [ ] Zweryfikować brak wycieków pamięci przy wielokrotnym montowaniu modułów z Chart.js/Maps.
- [ ] **Test**: Uruchomić `runModuleRegistryTest` z zestawem 50 dynamicznych rejestracji.

## Następny kamień milowy: Optymalizacja Logiki Frontendowej

### Krok N01
Wdrożenie hooka `useApi` — centralizacja zapytań HTTP i prosta warstwa cache'owania.
- [ ] Zaimplementować generyczny hook `useApi` obsługujący fetch, błędy i stan ładowania.

### Krok N02
Unifikacja logiki ocen — eliminacja redundancji między widokami a serwisem.
- [ ] Przenieść logikę `handleRating` i obliczenia `ocenaLog` do wspólnego modułu serwisowego.

### Krok N03
Optymalizacja subskrypcji DataBus — selektory ograniczające rerendery.
- [ ] Wprowadzić mechanizm `shallowCompare` lub selektory w `useDataBus` dla namespace'ów.

### Krok N04
Testy jednostkowe logiki transformacji danych.
- [ ] Wdrożyć framework testowy (np. proste asercje w JS) dla kluczowych parserów API.

## Przyszłe kamienie milowe

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
- **Wikipednia:** — Modul - Dodawanie kontekstu do rekordów inwestycji.
- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.