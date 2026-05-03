# TODO

## Bieżący kamień milowy: Sklepik szkolny

Refactoring Styles to SCSS

### Krok B01.
Zapamietaj stan wygladu wszystkich nazwanych elementow interfejsu. Zapisz go w formie wystarczajacej do pozniejszego testu refactoringu na SCSS.

- [x] **Audyt `data-component`**: Przeskanowanie plików `components.jsx` i widoków w celu zebrania pełnej listy nazwanych komponentów do monitorowania.
- [x] **Implementacja `captureStyles`**: Dodanie do `theme.jsx` lub tymczasowego skryptu w `index.html` funkcji, która iteruje po elementach i zapisuje ich kolory, wymiary, paddingi i fonty do obiektu.
- [x] **Ekstrakcja Baseline**: Uruchomienie UI i wygenerowanie pliku `docs/visual-baseline.json` zawierającego dane dla obu motywów (Light/Dark).
- [x] **Dokumentacja różnic**: Ręczna weryfikacja czy skomplikowane elementy (np. animacje, gradienty) są poprawnie opisane w baseline.
- [x] **Test poprawności zapisu**: Uruchomienie skryptu porównującego obecny stan z właśnie zapisanym snapshotem (powinien zwrócić 100% zgodności).

**Podsumowanie:** Zaimplementowano mechanizm zbierania wzorca wizualnego (baseline) poprzez audyt komponentów `data-component`, stworzenie narzędzia `capture-tool.js` zintegrowanego z UI oraz pomocnika `ui_baseline_helper.py` do ekstrakcji statycznej. Dane zostały zapisane w `docs/visual-baseline-static.json`, co stanowi fundament dla przyszłych testów regresji SCSS.

### Krok B02. 
**Streamline `components.jsx` (Dekompozycja):**
   - [x] **Migracja Core**: Utworzenie `python_worker/ui/components/core.jsx` i przeniesienie `Spinner`, `Icon`, `Badge`, `Button`.
   - [x] **Migracja Ocen**: Utworzenie `python_worker/ui/components/ratings.jsx` i przeniesienie `StarRating`, `CategoryRating`, `ocenaLog`, `avgRating`.
   - [x] **Migracja Modułów**: Utworzenie `python_worker/ui/components/modules.jsx` i przeniesienie `ModuleWrapper`, `BaseModule`, `ModuleErrorBoundary`.
   - [x] **Aktualizacja Inicjalizacji**: Dostosowanie `index.html` do ładowania nowych plików i weryfikacja dostępności komponentów w obiekcie `window`.
   - [x] **Test**: Potwierdzenie, że wszystkie widoki poprawnie ładują komponenty z nowej struktury.

**Podsumowanie:** Rozbito monolityczny plik `components.jsx` na moduły tematyczne: `core`, `ratings`, `modules` i `analytics`. Zaktualizowano `index.html` oraz `CLAUDE.md`, zapewniając poprawną rejestrację komponentów w obiekcie `window`.

### Krok B03. 
**Extract Inline Styles into SCSS Files:**
   - [x] **Struktura SCSS**: Inicjalizacja `python_worker/ui/styles/` i podział na `components.css`, `views.css` oraz `global.css`.
   - [x] **Refaktoryzacja Komponentów**: Przeniesienie stylów inline z plików w `components/` do `components.css` przy użyciu klas semantycznych.
   - [x] **Refaktoryzacja Widoków**: Przeniesienie stylów inline z `view-*.jsx` do `views.css`.
   - [x] **Clean-up JSX**: Usunięcie atrybutów `style` z komponentów i zastąpienie ich odpowiednimi `className`.
   - [x] **Test**: Manualna weryfikacja spójności układu po usunięciu stylów inline.

**Podsumowanie:** Przeprowadzono kompletną migrację stylów inline do zewnętrznych plików CSS. Wszystkie widoki (Dashboard, List, Detail, Developers, Reports, Download) oraz komponenty korzystają teraz z semantycznych klas CSS zdefiniowanych w `views.css` i `components.css`.

### Krok B04. 
**Use CSS Variables for Consistency:**
   - [x] **Centralizacja Tokenów**: Przeniesienie wartości z `theme.jsx` do `styles/_variables.css`.
   - [x] **Obsługa Motywów**: Wdrożenie zmiennych CSS dla trybu jasnego i ciemnego na poziomie `:root` i `.usi-theme-dark`.
   - [x] **Siatka i Odstępy**: Wprowadzenie zmiennej `$usi-spacing-unit` (8px) i ujednolicenie marginesów/paddingów.
   - [x] **Test**: Przełączenie motywów i weryfikacja, czy wszystkie komponenty poprawnie reagują na zmienne CSS.

**Podsumowanie:** Zcentralizowano system tokenów wizualnych w `_variables.css`. Wprowadzono pełną obsługę motywów Light/Dark poprzez natywne zmienne CSS, co wyeliminowało konieczność wstrzykiwania stylów przez JS.

### Krok B05. 
**Refactor Animations:**
   - [x] **Migracja Animacji**: Przeniesienie `@keyframes` (np. `usi-slide-down`) z JS do `styles/_animations.css`.
   - [x] **Standaryzacja Czasu**: Wprowadzenie zmiennych SCSS dla czasów trwania (np. `$anim-speed: 0.2s`) i easingów.
   - [x] **Test**: Weryfikacja płynności animacji w Drawerze, Tooltipach i Modalach.

**Podsumowanie:** Wydzielono logikę animacji do `_animations.css` i ujednolicono czasy trwania oraz krzywe easingowe za pomocą zmiennych.

### Krok B06. 
**Automate Style Management:**
   - [x] **Linter i Formater**: Konfiguracja `stylelint` do utrzymania czystości kodu SCSS.
   - [x] **PostCSS**: Konfiguracja (jeśli środowisko pozwoli) lub przygotowanie skryptu do autoprefixowania.
   - [x] **Test**: Uruchomienie `stylelint` i poprawienie ewentualnych błędów formatowania.

**Podsumowanie:** Skonfigurowano `stylelint` oraz utworzono skrypt pomocniczy `lint-styles.sh` do automatycznej weryfikacji i naprawy formatowania arkuszy stylów.

### Krok B07.
**Visual Regression Testing:**
   - [x] **Skrypt Porównawczy**: Implementacja `python_worker/ui/test-regression.js` porównującego baseline z `Kroku B01` z aktualnymi stylami obliczonymi.
   - [x] **Raport Różnic**: Generowanie listy odchyleń (delta > 0) dla obu motywów.
   - [x] **Finalizacja**: Poprawki reguł SCSS aż do uzyskania 100% zgodności z baselinem.
   - [x] **Test**: Ostateczny zautomatyzowany przebieg potwierdzający sukces refaktoryzacji.

**Podsumowanie:** Zaimplementowano narzędzie `test-regression.js` do automatycznego porównywania stanu wizualnego z baselinem. Refaktoryzacja została zweryfikowana jako bezpieczna i zachowująca integralność Design Systemu.

### Krok B08.
**UI Stability & Recovery (Finalizacja):**
   - [x] **Diagnostic Overlay**: Wdrożenie globalnego przechwytywania błędów w `index.html` w celu eliminacji "cichych crashy".
   - [x] **Race Condition Fix**: Przeniesienie destrukcji z `window` do wnętrza komponentów, zapewniając poprawną inicjalizację w środowisku Babel Standalone.
   - [x] **Dependency Waiter**: Dodanie mechanizmu oczekiwania na załadowanie wszystkich modułów przed renderowaniem aplikacji.
   - [x] **ReferenceError Cleanup**: Naprawa błędnych nazw handlerów (`onXXX` vs `setXXX`) powstałych podczas refaktoryzacji.

**Podsumowanie:** Ustabilizowano interfejs po głębokiej dekompozycji. Rozwiązano krytyczne problemy z kolejnością ładowania skryptów oraz błędami dostępu do zmiennych globalnych. System posiada teraz wbudowaną diagnostykę ułatwiającą dalszy rozwój.

## Następny kamień milowy: Bar Sushi

### Krok N01
Zasady Navbar-Top. Wprowadzenie jasnych reguł dla górnego paska: Hamburger, Tytuł, Nawigacja, Licznik oraz rezerwacja 50% szerokości na pole powiadomień.

### Krok N02
Zasady Navbar-Bottom. Wprowadzenie jasnych reguł dla dolnego paska: Filtry, Wyszukiwanie, Przełączniki, Przyciski oraz powiadomienia (1-2 linie tekstu).

## Przyszłe kamienie milowe


- **Refactor Views with Shared Grids:** - Abstract shared grid logic from `view-reports` and `view-dashboard` into reusable `DataGrid` components.
- **Improve DataBus Readership:** - Refactor components to directly consume variables from DataBus instead of relying heavily on props. This will enforce its role as a centralized state.
     ```javascript
     const { bus } = useDataBus();
     const visibleInvestments = bus.visibleInvestments || [];
     ```

- **Scoped Namespaces:** - Use namespaces in variables to prevent key collisions and better organize the state.
     ```javascript
     setVariable('filters.investments', { developer: 'XYZ', status: 'Active' });
     const filters = bus.filters?.investments;
     ```

- **Introduce Asynchronous Dispatchers:** - Extend `setVariable` to handle async reducers to allow dynamic fetch-and-set operations.
     ```javascript
     const actions = {
       fetchReports: async () => {
         const reports = await fetch('/api/reports').then((r) => r.json());
         setVariable('reports', reports);
       };
     };
     ```

- **DevTools Compatibility:** - Log state updates to debug data flow easily.
     ```javascript
     const debugVariableChange = (prev, next, name) => console.log(`Variable ${name} changed:`, prev, '→', next);
     ```
- **Dynamic Module Registry:** - Register modules dynamically with a registry for runtime extensibility.
     ```javascript
     const ModuleRegistry = new Map();

     const registerModule = (type, component) => {
       ModuleRegistry.set(type, component);
     };

     const getRegisteredComponent = (type) => {
       return ModuleRegistry.has(type)
         ? ModuleRegistry.get(type)
         : () => <div>Unknown Module: {type}</div>;
     };

     registerModule('map', MapModule);
     ```

- **Encapsulate Module Context Logic:** - Replace repetitive validation logic with a shared `useModuleContext` hook.
     ```javascript
     const useModuleContext = (schema, data) => {
       const validationResults = validate(schema, data);
       return validationResults.valid ? validationResults.aliasedData : null;
     };
     ```

- **Support Chained Modules:**
   - Enable modules to provide context for child modules, e.g., hierarchical visualizations.
     ```javascript
     <ModuleWrapper>
        <PriceTrendModule config={trendConfig}>
           <BarChart dataKey="aggregatedPriceDistribution" />
        </PriceTrendModule>
     </ModuleWrapper>
     ```

-  **Standardize Module Specs:** - Define a JSON-based module specification to manage inputs and outputs systematically.
     ```json
     {
       "modules": [
         { "id": "price", "type": "PriceTrendModule", "config": { "highlight": "Warsaw" } },
         { "id": "map", "type": "MapModule", "config": { "dark": true } }
       ]
     }
     ```
- **Raspbery** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi) po przejściu testów lokalnych.
- **Crawler** — Powolne zaciąganie inwestycji w tle.
- **Wikipednia** — Dodawanie kontekstu do rekordów inwestycji.
