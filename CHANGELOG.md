## Weryfikacja zmiany statusu w metadanych — 2026-05-09
- Zdiagnozowano i naprawiono błąd synchronizacji statusu inwestycji między backendem a UI.
- Poprawiono hook useRatings, aby automatycznie aktualizował lokalny stan DataBus po udanym zapisie.
- Zweryfikowano poprawność zapisu statusu w głównym pliku usi_*.json na dysku.
- Potwierdzono spójność danych w MetadataPanel po zmianie statusu przez analityka.


- Dodano przycisk "Odśwież dane" w DetailViewA.
- Zintegrować frontend z asynchronicznym mechanizmem JobManager na backendzie.
- Wprowadzono endpoint POST /api/refresh obsługujący pełną aktualizację rekordu i zdjęć.


- Przeprowadzono audyt i lokalizację inline SVG w kodzie UI.
- Wyodrębniono 23 ikony i 5 grafik do zewnętrznych plików .svg.
- Zrefaktoryzowano komponenty Icon, USIStarLogo i StarRating na tagi <img>.
- Ujednolicono użycie logo USI (usi-star-white.svg) w całej aplikacji.
- Zweryfikowano poprawne renderowanie i skalowanie zasobów.

## Standaryzacja stylów i optymalizacja — 2026-05-09
- **Unifikacja Pill Badges**: Zdefiniowano klasę `.usi-pill.info` oraz rozszerzono `.usi-pill.outline` o automatyczne dopasowanie koloru obramowania dla wariantów `success`, `danger` i `info`.
- **Eliminacja Inline Styles**: Usunięto style inline z widoków deweloperów i biblioteki modułów, zastępując je semantycznymi klasami pomocniczymi (`.usi-text-accent`, `.usi-weight-400`).
- **Poprawa Wyświetlania Sugestii**: Ujednolicono wygląd etykiet sugestii deweloperów, korzystając z nowego systemu klas CSS.
- **Standaryzacja DataGrid**: Migracja stylów inline (layout, wyrównanie) do `components.css` oraz wprowadzenie klas pomocniczych w `global.css`. Wykorzystano zmienne CSS dla dynamicznych parametrów siatki.
- **Standaryzacja RatingsPanel**: Wyeliminowano style inline z `RatingsPanel.jsx`, zastępując je klasami pomocniczymi marginesów i wagi tekstu. Wprowadzono semantyczne klasy dla statusu zapisu i punktacji wyróżników.
- **Optymalizacja Modułów Analitycznych**: Przeprowadzono audit i czyszczenie stylów w `analytics.jsx`, `modules-map.jsx` oraz `modules-charts.jsx`. Wdrożono zmienne CSS dla dynamicznych szerokości pasków postępu i wysokości map.

## Czyszczenie artefaktów kodu — 2026-05-09

- **Unifikacja ActionBar**: Przeniesiono akcje inwestycji (linki źródłowe, przełącznik trybów) z HeroBand do globalnego ActionBar, poprawiając spójność nawigacji.
- **Optymalizacja SlideShow**: Rozwiązano problem scrollowania w trybie Media poprzez uelastycznienie komponentu Gallery (className) i wymuszenie pełnej wysokości viewportu.
- **Integracja Modułowa**: Zarejestrowano brakujący moduł MiniMap w ModuleRegistry, udostępniając go w bibliotece modułów i systemie raportowym.
- **Naprawa Wyszukiwarki Deweloperów**: Wdrożono brakującą logikę filtrowania i wyszukiwania w widoku deweloperów zintegrowaną z DataBus.
- **Oczyszczenie Interfejsu**: Usunięto zbędne filtry miast z widoku deweloperów, upraszczając nawigację.
- **Stabilność Funkcji „Połącz”**: Naprawiono błąd 500 przy scalaniu deweloperów poprzez bezpieczniejszą obsługę plików i automatyczne tworzenie katalogu archiwum.


- **Architektura „Thin-Client”**: Zakończono migrację logiki skrapowania i adaptacji danych do zewnętrznej, wersjonowanej biblioteki `usi-scrapers` (v0.1.8).
- **Naprawa TabelaOfert (v0.1.8)**: Rozwiązano krytyczny błąd wycieku zdjęć z niepowiązanych etapów inwestycji poprzez wdrożenie „slicera” HTML (Area-Limited Extraction).
- **Czyszczenie Bazy Danych**: Przeprowadzono automatyczne usunięcie 40 „czystych” rekordów TabelaOfert, które posiadały błędy w strukturze zdjęć, w celu ich ponownej, poprawnej rejestracji.
- **Poprawki RynekPierwotny**: Wdrożono mechanizm „Stage Flattening” w bibliotece, poprawnie mapujący poszczególne etapy inwestycji na niezależne rekordy USI.
- **Stabilność Konfiguracji**: Naprawiono błędy składniowe w `config.py` i usprawniono mechanizm weryfikacji wersji biblioteki przy starcie systemu.
- **Unifikacja Danych**: Przygotowano fundamenty pod standaryzację pól `delivery_date`, identyfikując różnice w raportowaniu terminów między portalami.
- **Optymalizacja Środowiska**: Poprawiono proces instalacji biblioteki `usi-scrapers` poprzez patchowanie `pyproject.toml` (naprawa autodetekcji pakietów).

## Poprawki 2 — 2026-05-08
- **Audyt Stylów i CSS**: Wyeliminowano style inline w komponentach JSX, przenosząc je do semantycznych klas. Zoptymalizowano `views.css`, usuwając ponad 800 linii nieużywanego kodu.
- **Naprawa Modułu „W okolicy”**: Rozwiązano błąd logiczny w wyszukiwaniu pobliskich inwestycji, przywracając poprawne wyświetlanie sąsiedztwa.
- **Optymalizacja Układu DetailsA**: Wprowadzono elastyczny układ kolumn (50/25/25) i przeniesiono metadane do trzeciej kolumny dla lepszej czytelności.
- **Metadane Finansowe**: Dodano obsługę i wyświetlanie minimalnej/maksymalnej ceny za m2 we wszystkich adapterach i widoku szczegółowym.
- **Stabilność Siatki i Kart**: Naprawiono błędy overflow w DataGrid oraz poprawiono proporcje i obsługę błędów miniatur w kartach.
- **System Powiadomień**: Przebudowano NotificationCenter na minimalistyczny styl konsolowy z poprawnym globalnym pollingiem zadań.
- **Poprawki TabelaOfert**: Ulepszono TOAdapter o fallback dla brakujących cen m2 oraz uodporniono config.py na błędy uprawnień macOS.

## Poprawki — 2026-05-07
- **Błąd Discovery Otodom**: Naprawiono filtr „Tylko nowe” poprzez poprawną ekstrakcję ID ofert i usunięcie fałszywych dopasowań do pustych rekordów.
- **Tryb Ciemny i CSS**: Wprowadzono pełne wsparcie dla motywu ciemnego poprzez system zmiennych CSS i unifikację selektorów ([data-dark="1"]).
- **System Powiadomień**: Zaimplementowano NotificationConsole z historią zdarzeń oraz NotificationCenter w Navbarze, zastępując globalne spinnery.
- **Moduły Map**: Zaktualizowano MiniMapy o dynamiczne adresy HERE i naprawiono krytyczny błąd obsługi klastrów (BoundingBox).
- **Ekstrakcja TO**: Udoskonalono identyfikację deweloperów w scraper_to.py poprzez analizę tagów HTML (fallback dla JSON-LD).
- **Zarządzanie Deweloperami**: Zoptymalizowano merge_developers, eliminując ryzyko uszkodzenia ścieżek do zdjęć przy scalaniu rekordów.
- **Responsywność UI**: Wdrożono dynamiczny układ DataGrid (minCardWidth), optymalizując wyświetlanie na szerokich monitorach.

## Długoterminowe i QA — 2026-05-06
- Zaimplementowano mechanizm USI Storyboard do izolowanego testowania komponentów UI w czasie rzeczywistym.
- Wdrożono interaktywny panel Knobs w Storyboardzie, umożliwiający dynamiczną zmianę właściwości komponentów (mock data).
- Przeprowadzono dekompozycję i izolację kluczowych komponentów: DataGrid oraz MapModule (refaktoryzacja pod kątem wstrzykiwania zależności).
- Zaimplementowano system fixtures i mocków dla inwestycji, ułatwiający rozwój interfejsu bez połączenia z API.
- Wprowadzono instrumentację wydajnościową (useRenderTracker) do weryfikacji optymalizacji selektorów DataBus.

## Optymalizacja Logiki Frontendowej — 2026-05-06
- Wdrożono hook `useApi` z centralnym cache i obsługą błędów.
- Zunifikowano logikę ocen (`ocenaLog`, `avgRating`) w dedykowanym module `modules-ui.jsx`.
- Zoptymalizowano `DataBus` wprowadzając selektory (`useDataBusSelector`) i `shallowCompare`.
- Wdrożono framework testów jednostkowych JS (`TestSuite`) z integracją w interfejsie.
- Zredukowano liczbę zbędnych re-renderów w `DataGrid` i widokach głównych.

## System Modułów: Rozszerzenia — 2026-05-06
- **Rozbudowa Systemu Modułów**: Wdrożono zaawansowane moduły analityczne i wizualne, w tym `PriceTrendModule` (wykresy trendów cenowych Chart.js) oraz interaktywny `MapModule` z klastrowaniem punktów (HERE Maps API).
- **System Szablonów (Presets)**: Wprowadzono mechanizm `presets` w `ModuleRegistry`, pozwalający na definiowanie złożonych układów raportów (np. "Przegląd Dewelopera") za pomocą jednego identyfikatora.
- **Zaawansowana Konfiguracja (Knobs)**: Rozszerzono panele edycji modułów o nowe typy pól (`Select`, `Range`), umożliwiając precyzyjną personalizację wizualizacji bezpośrednio w UI.
- **Optymalizacja i Stabilność**: Przeprowadzono kompleksowe testy wydajnościowe i stabilności (`runStressTest`), potwierdzając brak wycieków pamięci i wysoką responsywność rejestru komponentów.
- **Architektura Biblioteki**: Stworzyłem dedykowany widok "Biblioteka", służący jako żywy katalog komponentów z interaktywnym podglądem i dokumentacją parametrów technicznych.

## Stabilność i UX — 2026-05-06
- **Scoped Namespaces**: Zweryfikowano izolację stanu dla wielu instancji tych samych modułów (np. dwóch map) w jednym raporcie.
- **Poprawka PriceTrendModule**: Rozwiązano krytyczny błąd destrukturyzacji `scopedBus`, przywracając interaktywność wykresów.
- **Diagnostyka Interakcji**: Wdrożono szczegółowe logowanie zdarzeń w `MapModule` i `PriceTrendModule` z uwzględnieniem identyfikatorów instancji.
- **Automatyczna Regresja Danych**: Rozszerzono zestaw testów o weryfikację struktury `bus.scopes` i poprawności zagnieżdżonych aktualizacji stanu.
- **Raport Diagnostyczny**: Dodano `test_namespaces.json` jako narzędzie do weryfikacji architektury Interact 2.0.

## DataBus: Zaawansowane funkcje — 2026-05-06
- **Scoped Namespaces**: Wprowadzono przestrzenie nazw `filters` oraz `download` w DataBus z obsługą notacji kropkowej w `setVariable`.
- **Asynchroniczne Dispatchery**: Rozszerzono szynę o obsługę async reducerów i Promises z monitorowaniem stanu `isDispatching`.
- **Debugowanie i DevTools**: Wdrożono logowanie zmian stanu do konsoli (diffy) oraz funkcję eksportu pełnego stanu szyny do JSON.
- **Rejestr Modułów**: Zaimplementowano `ModuleRegistry`, umożliwiając dynamiczne ładowanie komponentów i renderowanie raportów ze specyfikacji.
- **Hook useModuleContext**: Skonsolidowano logikę ekstrakcji danych i agregacji statystyk w uniwersalnym hooku dla modułów.
- **Zagnieżdżone Moduły**: Wprowadzono `LocalModuleContext` i `ContainerModule`, wspierające hierarchiczne wizualizacje (kaskadowy kontekst).
- **Specyfikacje Modułów**: Wdrożono formalną walidację parametrów wejściowych oraz automatyczny generator paneli edycyjnych (`ModuleKnobs`).

## SafeRender Pattern: Implementacja DataBoundary — 2026-05-05
- Wprowadzono wzorzec **SafeRender**, zapewniający odporność interfejsu na uszkodzone lub niekompletne dane z API.
- Zaimplementowano komponent `DataBoundary`, który automatycznie waliduje surowe obiekty JSON względem schematu `USI_INVESTMENT_SCHEMA`.
- Rozszerzono funkcję `safeRender` o inteligentną obsługę typów (string, number, array, object) oraz formatowanie walutowe (`currency`).
- Przeprowadzono refaktoryzację widoków `ViewList` i `DetailRightPanel`, eliminując bezpośrednie ryzyko crashy Reacta ("Objects are not valid as a React child").
- Dodano zestaw testów stabilności danych `runDataIntegrityTest` w `test-regression.js`, umożliwiający automatyczną weryfikację regresji w warstwie danych.
- Uproszczono kod komponentów prezentacyjnych (`ListCard`, `HeroBand`) poprzez usunięcie redundantnych, ręcznych sprawdzeń typów.

## Zaplecze — 2026-05-05
- Pełna dekompozycja `ui_server.py` na modułowe Blueprinty Flask (`jobs`, `investments`, `discovery`, `reports`).
- Ekstrakcja logiki zarządzania zadaniami do dedykowanego modułu `python_worker/jobs.py` (JobManager).
- Wdrożenie warstwy serwisowej (`InvestmentService`, `DiscoveryService`) separującej logikę biznesową od API.
- Refaktoryzacja adapterów do nowoczesnego pakietu `python_worker/adapters/` z wykorzystaniem wzorca Factory.
- Centralizacja pomocników i unifikacja logiczna między interfejsem CLI a webowym.

## Front sklepu: Atomizacja komponentów i "Window Registry" — 2026-05-04
- Ukończono dekompozycję widoku szczegółowego na niezależne komponenty (DetailsViewA, DetailsViewC).
- Zintegrowano wszystkie kluczowe widoki i komponenty z systemem `usiRegister`.
- Uproszczono `view-detail.jsx` do roli lekkiego orchestratora.
- Zlikwidowano race-conditions w środowisku Babel Standalone poprzez rejestr komponentów.

## Sprzatanie — 2026-05-04
- Naprawiono regresje funkcjonalne po wdrożeniu Shell Layout: przywrócono widok parametrów (Mode A) oraz system oceniania w widoku szczegółów.
- Zoptymalizowano tryb mediów (Mode C): wdrożono komponent `SlideShow` z dopasowaniem zdjęć do okna i wyeliminowano problem podwójnego przewijania.
- Przywrócono i ulepszono minimapy: dodano dynamiczną mapę do widoku dewelopera oraz przywrócono podgląd lokalizacji w nagłówku inwestycji.
- Ustabilizowano widok Pobieranie: przywrócono przyciski akcji (Szukaj, Pobierz) i zintegrowano je z systemem API oraz nowym systemem ActionBar.
- Skorygowano układ nagłówka: tytuł widoku został wyrównany do lewej strony (obok menu), poprawiając czytelność i nawigację.
- Rozwiązano krytyczny błąd `TypeError: handleRating is not a function` w trybie media poprzez poprawne przekazywanie propsów w gałęziach warunkowych.

## Bar Sushi — 2026-05-04
- Wdrożono stałą strukturę "Shell Layout" z ramowymi paskami nawigacji (Top) i akcji (Bottom) zarządzanymi centralnie w `App.jsx`.
- Zintegrowano system powiadomień `NotificationCenter` (zadania w tle) oraz `StatusMessenger` (systemowe toasty) w górnym pasku.
- Ujednoliceno system filtrowania i wyszukiwania, przenosząc wszystkie kontrolki widoków listy do ustandaryzowanego komponentu `ActionBar`.
- Przeprowadzono głęboką refaktoryzację widoków (`view-list`, `view-dashboard`, `view-dev-list`), usuwając redundantny kod i lokalne toolbary.
- Zoptymalizowano responsywność interfejsu poprzez media queries i dynamiczne zarządzanie widocznością slotów na urządzeniach mobilnych.
- Wzmocniono stabilność UI poprzez mechanizm **Dependency Guarding**, zapewniający pełną gotowość komponentów przed renderowaniem w Babel Standalone.
- Wprowadzono system raportowania błędów frontendu do serwera (`/api/ui-error`) z zapisem do `logs/ui_errors.log`.

## Sklepik szkolny — 2026-05-04
- Przeprowadzono głęboką dekompozycję monolitycznego pliku `components.jsx` na moduły: `core`, `ratings`, `modules` i `analytics`.
- Zmigrowano wszystkie style inline do zewnętrznych arkuszy CSS (`global.css`, `components.css`, `views.css`) z użyciem semantycznych klas.
- Wprowadzono system zmiennych CSS (`_variables.css`) dla kolorów, siatki 8px oraz pełną obsługę motywów Light/Dark bez wstrzykiwania JS.
- Zaimplementowano zautomatyzowane testy regresji wizualnej (`test-regression.js`) porównujące style obliczone z wzorcem baseline.
- **UI Stability & Recovery**: Rozwiązano krytyczne błędy race condition w środowisku Babel Standalone poprzez bezpieczną ekstrakcję globali wewnątrz komponentów.
- Wdrożono system **Diagnostic Overlay** (Czerwony Ekran Śmierci) do natychmiastowego przechwytywania i wyświetlania błędów runtime w UI.
- Dodano mechanizm **Dependency Waiter**, upewniający się o załadowaniu wszystkich modułów przed startem renderowania Reacta.

## Witryna sklepowa — 2026-05-03
- Zsynchronizowano `theme.jsx` mit Design Systemem, wprowadzając tokeny CSS i ujednolicając siatkę (8px/16px) we wszystkich widokach.
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
