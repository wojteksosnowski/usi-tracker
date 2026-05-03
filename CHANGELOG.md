# CHANGELOG

## Sklepik szkolny — 2026-05-04

- Przeprowadzono głęboką dekompozycję monolitycznego pliku `components.jsx` na moduły: `core`, `ratings`, `modules` i `analytics`.
- Zmigrowano wszystkie style inline do zewnętrznych arkuszy CSS (`global.css`, `components.css`, `views.css`) z użyciem semantycznych klas.
- Wprowadzono system zmiennych CSS (`_variables.css`) dla kolorów, siatki 8px oraz pełną obsługę motywów Light/Dark bez wstrzykiwania JS.
- Zaimplementowano zautomatyzowane testy regresji wizualnej (`test-regression.js`) porównujące style obliczone z wzorcem baseline.
- **UI Stability & Recovery**: Rozwiązano krytyczne błędy race condition w środowisku Babel Standalone poprzez bezpieczną ekstrakcję globali wewnątrz komponentów.
- Wdrożono system **Diagnostic Overlay** (Czerwony Ekran Śmierci) do natychmiastowego przechwytywania i wyświetlania błędów runtime w UI.
- Dodano mechanizm **Dependency Waiter**, upewniający się o załadowaniu wszystkich modułów przed startem renderowania Reacta.

## Witryna sklepowa — 2026-05-03

- Zsynchronizowano `theme.jsx` z Design Systemem, wprowadzając tokeny CSS i ujednolicając siatkę (8px/16px) we wszystkich widokach.
- Wzbogacono warstwę semantyczną interfejsu poprzez dodanie precyzyjnych atrybutów `data-component` do interaktywnych elementów i sekcji informacyjnych.
- Przeprowadzono refaktoryzację struktury UI, wydzielając logikę analityczną i metadane do reużywalnych komponentów w `components.jsx`.
- Zoptymalizowano pliki widoków (Dashboard, List, Detail) poprzez redukcję nadmiarowego kodu i wprowadzenie uniwersalnych komponentów sterujących.
- Potwierdzono stabilność systemu i poprawność komunikacji przez `DataBus` oraz bezbłędne działanie filtrów i nawigacji po zmianach.

## Dania Fast Food — 2026-05-03

- Zaimplementowano fundamenty architektury modułowej: BaseModule, ModuleErrorBoundary i SkeletonModule.
- Dodano system typowania i walidacji ModuleSchemaValidator dla wejść do modułów.
- Wyciągnięto logikę dostępu do danych w extractModuleContext i zintegrowano ją w widokach listy i szczegółów inwestycji.
- Stworzono uniwersalny ModuleWrapper pozwalający na łatwe podpinanie komponentów pod nową architekturę.
- Dodano responsywność modułów przez ResizeObserver przekazujący szerokość kontenera.
- Zrefaktoryzowano i podpięto MiniMap jako udany test nowej architektury.

## Domowe obiady — 2026-05-03

- Wdrożono infrastrukturę Szyny Danych (DataBus) opartą na React Context, umożliwiającą globalną wymianę stanu między niezależnymi widokami.
- Stworzono system dynamicznych raportów sterowanych plikami JSON z obsługą filtrów (miasto, deweloper, promień geograficzny).
- Zaimplementowano silnik filtrowania inwestycji po stronie serwera zintegrowany z definicjami raportów.
- Wprowadzono modularny system prezentacji danych w raportach z rejestrem komponentów (ModuleRegistry).
- Dodano zaawansowane moduły analityczne: interaktywne mapy punktowe (HERE Maps) oraz wykresy trendów i korelacji (Chart.js).
- Zintegrowano widok szczegółowy z szyną danych, publikując informacje o bieżącej inwestycji i jej sąsiedztwie.

## Kawiarnia — 2026-05-03

- Utworzono centralną bazę danych deweloperów w `Public/USIdev` oraz system unikalnych identyfikatorów `usi_dev_id` i `usi_inv_id`.
- Wdrożono mechanizm automatycznego pobierania surowych profili deweloperów oraz ekstrakcję metadanych (NIP, KRS, adres).
- Zaimplementowano heurystykę wykrywania podobieństw deweloperów, generującą sugestie powiązań dla rekordów z różnych portali.
- Stworzono nowoczesny widok listy i szczegółów dewelopera, integrując go z istniejącym systemem nawigacji.
- Dodano zaawansowaną analitykę "Zasięg inwestycji" z automatyczną agregacją statystyk (liczba mieszkań, oceny) per miasto.
- Wprowadzono system `JobManager` do obsługi asynchronicznych zadań w tle (np. skanowanie portali) z wizualizacją postępu w UI.

## Lodziarnia — 2026-05-03

- Zaimplementowano ujednolicony mechanizm Discovery dla portali RP, Otodom i TabelaOfert wspierający skanowanie globalne.
- Wdrożono mechanizm Stage Flattening dla RynekPierwotny, umożliwiający automatyczne wykrywanie i separację etapów inwestycji.
- Dodano scentralizowany RateLimiter w klasie Fetcher z dedykowanymi opóźnieniami dla domen (np. 3s dla Otodom).
- Przebudowano widok Pobieranie: wprowadzono dwupoziomowy Toolbar, interaktywne SourceBadge oraz masowe pobieranie z paskiem postępu.
- Zoptymalizowano system kart poprzez komponent StandardCard i wdrożono automatyczny wybór najwyższej rozdzielczości zdjęć.
- Usprawniono skraper TabelaOfert o obsługę JSON-LD, fallback geokodowania HERE Maps i czyszczenie nazewnictwa.

## Pizzeria — 2026-05-02

- Odświeżono nawigację UI: dodano wysuwaną szufladę (Drawer) z obsługą trybu jasnego/ciemnego i ulepszono spójność designu.
- Przeniesiono silnik scrapowania na bibliotekę `Scrapling` oraz wdrożono mechanizm bezpiecznej aktualizacji rekordów JSON z logowaniem zmian.
- Zaimplementowano w pełni stylizowaną mapę Dashboardu (HERE Maps) z precyzyjnym oznaczaniem inwestycji.
- Zoptymalizowano widok szczegółów: nowe HeroBand z ocenami waźonymi USI oraz przebudowany układ kolumn i udogodnień.
- Stworzono dedykowaną podstronę "Pobieranie" do zarządzania nowościami z portali (RP, Otodom) wraz z dedykowanymi endpointami API.
- Opracowano i sformalizowano dokumentację Design Systemu oraz nazewnictwo komponentów frontendu.

## Buda z kebabem — 2026-05-01

- Zaimplementowano modułowe scrapery dla Otodom, RynekPierwotny i TabelaOfert z obsługą Fetchera (curl_cffi i ScrapperAI).
- Wdrożono integrację z mapami HERE (minimapy, stylizacja, synchronizacja współrzędnych).
- Stworzono responsywny interfejs użytkownika (React) z widokiem listy 6000+ inwestycji, filtrowaniem i zaawansowanym widokiem detali.
- Wprowadzono system oceniania inwestycji w kategoriach oraz automatyczne obliczanie oceny złożonej.
- Zaimplementowano audyt zmian (created_at/updated_at) oraz mechanizm rozdzielania rekordów dualnych (RP+OTO).
- Zoptymalizowano strukturę danych i schematy JSON oraz usprawniono proces importu z CSV (USImaster).


