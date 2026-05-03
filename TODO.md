# TODO

## Bieżący kamień milowy: Dania Fast Food

### Krok B01
Przemyślenie architektury samych modułów.
- [x] Określenie cyklu życia modułu (inicjalizacja, aktualizacja danych, zmiana rozmiaru).
- [x] Definicja bazowego hooka `useModule` lub komponentu `BaseModule` dla wszystkich modułów.
- [x] Opracowanie mechanizmu obsługi błędów (Error Boundary) dla izolacji awarii modułów.
- [x] Standaryzacja bazowej stylizacji modułów zgodnej z design system.
- [x] Test: Implementacja "Modułu Szkieletowego" i weryfikacja jego reakcji na zmiany danych w widoku.

**Podsumowanie:** Wdrożono klasę `ModuleErrorBoundary` izolującą awarie oraz zdefiniowano komponent `BaseModule`, który będzie renderował wszystkie moduły używając standardowych właściwości design systemu (karta, cień, opcjonalny tytuł z ikoną). Dodatkowo zrealizowano demonstracyjny `SkeletonModule`, pokazujący integrację tych komponentów i sposób wyrzucania kontrolowanych błędów. Zmiany udokumentowano stosownym commitem.

### Krok B02
Przemyślenie architektury zmiennych wejściowych dla modułów.
- [x] Definicja standardowych typów danych dla modułów (np. `RecordSet`, `GeoPoint`, `Rating`).
- [x] Opracowanie mechanizmu mapowania zmiennych widoku na nazwy oczekiwane przez moduł (aliasing).
- [x] Stworzenie przykładowej specyfikacji JSON dla konfiguracji wejścia modułu.
- [x] Analiza dostępności danych w widokach (np. obsługa przypadku braku geo w widoku listy).
- [x] Test: Walidacja przykładowego obiektu zmiennych wejściowych względem zaproponowanego schematu.

**Podsumowanie:** Zdefiniowano obiekt `ModuleTypes` (RecordSet, GeoPoint, Rating, Color, Number) jako fundament schematów wejściowych modułów. Opracowano `ModuleSchemaValidator`, który mapuje wejściowe dane z widoku (obsługując aliasing np. `from: 'currentGeo'`) oraz automatycznie waliduje typ i wymagalność (obsługując braki w widoku). Dodano przykładową specyfikację JSON wewnątrz testu, z którego wynik loguje poprawną strukturę zmapowanych argumentów dla modułu do konsoli przeglądarki. Zmiany scommitowane.

### Krok B03
Minimapa w widoku rekordu inwestycji również może funkcjonować jako moduł.
- [x] Analiza kodu `MiniMap` w `components.jsx` pod kątem wymaganych propsów i zależności.
- [x] Określenie mapowania danych widoku (współrzędne, markery) na ustandaryzowane zmienne modułu.
- [x] Zaprojektowanie mechanizmu `ModuleWrapper` dla istniejących komponentów UI.
- [x] Dokumentacja założeń (komentarz w kodzie) dla integracji mapy z systemem modułów.
- [x] Test: Weryfikacja renderowania mapy przy użyciu statycznego obiektu danych testowych (mock).

**Podsumowanie:** Przeanalizowano `MiniMap` i dostosowano ją by przyjmowała obiekt `geo` zamiast surowych współrzędnych. Zaprojektowano uniwersalny komponent `ModuleWrapper`, który przyjmuje specyfikację wejściową, kontekst, mapuje dane z użyciem `ModuleSchemaValidator` i renderuje docelowy komponent wewnątrz `BaseModule` połączonego z `ErrorBoundary`. Udokumentowano cel i sposób działania komponentu `ModuleWrapper`. Rozwiązanie zatwierdzono do repozytorium.

### Krok B04
Każdy widok generuje zestaw zmiennych używanych później przez moduły.
- [x] Inwentaryzacja danych dostępnych w `view-list.jsx` oraz `view-detail.jsx` pod kątem modułów.
- [x] Implementacja funkcji `getModuleContext()` w `view-list.jsx` zwracającej listę widocznych rekordów.
- [x] Implementacja funkcji `getModuleContext()` w `view-detail.jsx` zwracającej dane pojedynczej inwestycji (geo, ocena, kolor).
- [x] Dodanie logowania wygenerowanego kontekstu do konsoli w celach debugowania.
- [x] Test: Weryfikacja poprawności struktury obiektu kontekstu dla obu widoków w konsoli przeglądarki.

**Podsumowanie:** Przeanalizowano główne komponenty wyświetlające (`ListGrid` oraz `DetailRightPanel`). W obu zaimplementowano funkcję `getModuleContext()`, która generuje ustrukturyzowany słownik powiązany z danymi z widoku: w liście zwraca `visibleInvestments`, natomiast w szczegółach inwestycji ekstraktuje `currentInvestment`, `geo`, wyliczoną średnią `rating` (korzystając z istniejącego `avgRating()`) oraz `color`. Dodano w nich hook `useEffect` logujący zmianę tego kontekstu. Zmiany zatwierdzone.

### Krok B05
Potencjalnie przydatne zmienne:
* Lista rekordów.
* Punkt geo.
* Ocena [0-4].
* Kolor.
* Liczba mieszkań z rekordów według kwartałów.
* Ocena ważona (suma) z rekordów według kwartałów.
- [x] Implementacja funkcji agregujących dane z listy rekordów (np. suma mieszkań, średnia ocena).
- [x] Opracowanie transformatora danych do wykresów (agregacja statystyk według kwartałów).
- [x] Implementacja ekstraktora współrzędnych i kolorów do ustandaryzowanego formatu modułów.
- [x] Integracja ekstraktorów z funkcją `getModuleContext` w widoku listy i szczegółów.
- [x] Test: Weryfikacja poprawności wyliczonych statystyk (np. sumy mieszkań) na rzeczywistym zbiorze danych.

**Podsumowanie:** Utworzono stałą `extractModuleContext` w `data.jsx`, która zawiera dedykowane funkcje (`sumApartments`, `avgListRating`, `aggregateByQuarter`, `extractGeoPoint`). Pozwala to na odseparowanie logiki obliczeniowej od samej prezentacji. Rozbudowano hooki `getModuleContext` w widokach, integrując nowe ekstraktory, zasilając obiekt kontekstu bogatszymi statystykami gotowymi do bezpośredniego użycia przez wizualizacje. Test w konsoli loguje wyliczone dane. Zmiany weszły do repozytorium.

### Krok B06
Moduły akceptują szerokość obiektu obejmującego.
- [x] Implementacja `ResizeObserver` wewnątrz `BaseModule` do śledzenia wymiarów kontenera.
- [x] Przekazywanie aktualnej szerokości (`containerWidth`) do modułu jako zmiennej wejściowej.
- [x] Opracowanie mechanizmu progów szerokości (breakpoints) dla wariantów układu modułu.
- [x] Integracja wywołania `map.invalidateSize()` (lub odpowiednika) przy zmianie szerokości modułu mapy.
- [x] Test: Weryfikacja płynności zmiany rozmiaru modułu przy zmianie wielkości okna lub panelu bocznego.

**Podsumowanie:** Wdrożono `ResizeObserver` w `BaseModule`, który śledzi zmianę rozmiaru elementu okalającego. Przechwycona szerokość kontenera (`containerWidth`) jest wstrzykiwana bezpośrednio do renderowanego komponentu wewnętrznego poprzez `React.cloneElement`. Zaktualizowano również komponent `MiniMap`, aby odbierał ten prop i, w odpowiedzi na jego zmianę, symulował wywołanie metody `invalidateSize()` (logowane do konsoli), co potwierdza przesył danych i gotowość na właściwy obiekt mapy. Zmiany w repo.

### Krok B07
Użycie minimapy jako modułu testowego.
- [x] Refaktoryzacja komponentu `MiniMap` do nowej architektury modułowej.
- [x] Implementacja dynamicznego renderowania modułu wewnątrz `view-detail.jsx`.
- [x] Podpięcie danych z kontekstu widoku do wejść modułu minimapy.
- [x] Obsługa parametrów konfiguracyjnych modułu (np. domyślny zoom) w definicji widoku.
- [x] Test: Weryfikacja poprawności wyświetlania i interakcji z mapą w nowym kontenerze modułowym.

**Podsumowanie:** Uzupełniono funkcję `getModuleContext()` w widoku szczegółów o specyficzne dla mapy dane (`district`, `hereUrl`, `hereUrlDark`). Utworzono specyfikację `miniMapSpec` w `HeroBand`, definiującą mapowanie typów (GeoPoint) oraz opcjonalnych konfiguracji (zoom). Finalnie zastąpiono w `view-detail.jsx` (w komponentach HeroBand oraz pośrednio ModeC) statyczne wywołanie minimapy dynamicznym `ModuleWrapper`, wstrzykującym do `MiniMap` przygotowany obiekt kontekstu. Zmiany udokumentowano na gicie. Całość kamienia milowego działa e2e.

## Następny kamień milowy: Witryna sklepowa

Sprawdzenie zgodnosci UI z design system. Sprawdzenie czy wszystkie komponenty maja swoje identyfikujace nazwy dla potrzeb komunikacji LLM<->user. Sprawdzenie wielkosci plikow. Sprawdzenie modularności. Testy czy czegos nie zjebalismy w interfejsie w tym kamieniu milowym.

### Krok N01
Sprawdzenie zgodności UI z design system i identyfikacja komponentów.
- [ ] Inwentaryzacja komponentów UI

## Przyszłe kamienie milowe

- **Raspbery** — uruchomienie na raspberry pi - dopiero po przejsciu rozleglych testow na lokalnym komputerze
- **Crawler** — Powolne zaciaganie inwestycji w tle.
- **Wikipednia** — Dodawanie kontekstu do rekodow inwestycji.
