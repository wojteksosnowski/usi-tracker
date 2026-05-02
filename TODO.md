# TODO

## Bieżący kamień milowy: Kawiarnia

### Krok B01

Potrzebna baza wykrytych deweloperów (katalog Public/USIdev).

- [x] Utworzyć katalog `Public/USIdev/` jako centralne miejsce dla metadanych deweloperów.
- [x] Opracować skrypt do ekstrakcji unikalnych danych deweloperów z istniejących plików inwestycji.
- [x] Zaimplementować zapisywanie danych do `Public/USIdev/{dev_slug}.json` zgodnie z `usi_dev.schema.json`.
- [x] Stworzyć funkcję pomocniczą w `developer_manager.py` do zarządzania plikami w `Public/USIdev/`.
- [x] Test: Zweryfikować poprawność struktury i zawartości plików w katalogu `Public/USIdev/` po migracji.

**Podsumowanie:**
Utworzono centralny katalog `Public/USIdev` i zaktualizowano konfigurację systemu. Zaimplementowano skrypt migracji `init_developers.py`, który wyodrębnił 2107 unikalnych deweloperów z 8838 plików inwestycji. Klasa `DeveloperManager` została rozszerzona o metody zarządzania nową bazą danych deweloperów.
### Krok B02

Surowe JSONy deweloperów ze stron.

- [x] Utworzyć katalog `Public/USIdev/raw/` na surowe zrzuty danych z portali.
- [x] Zmodyfikować scrapery (RP, Otodom, TO), aby pobierały surowe dane profilu dewelopera.
- [x] Zaimplementować wersjonowanie lub datowanie surowych zrzutów w celu śledzenia zmian.
- [x] Zintegrować zapis surowych danych z procesem `update-dev`.
- [x] Test: Uruchomić `update-dev` dla jednego dewelopera i sprawdzić obecność pliku w `Public/USIdev/raw/`.

**Podsumowanie:**
Zaimplementowano pobieranie surowych profili deweloperów z portali RP, Otodom i TabelaOfert. Utworzono katalog `Public/USIdev/raw/` i dodano metodę `save_dev_raw_json` do `DeveloperManager`. Proces `update-dev` został rozszerzony o pobieranie danych profilowych przed aktualizacją inwestycji.
### Krok B03

JSONy łączące (nadrzędne): łączące w grupy rekordy z różnych portali, grupy kapitałowe spółek, spółki-córki, nowe ID tego samego dewelopera.

- [x] Zdefiniować format i wprowadzić `USIdevID` oraz `USIinvID` jako unikalne identyfikatory w systemie.
- [x] Utworzyć warstwę mapowania w `Public/USIdev/`, łączącą portalowe rekordy deweloperów pod wspólnym `USIdevID`.
- [x] Dodać pole `USIdevID` do rekordów inwestycji, umożliwiając opcjonalne podwójne wskazanie (portalowe i nadrzędne).
- [x] Zaimplementować logikę grup kapitałowych poprzez relacje między różnymi `USIdevID`.
- [x] Test: Powiązać inwestycję z konkretnego portalu z nadrzędnym `USIdevID` i zweryfikować odczyt w adapterze.

**Podsumowanie:**
Wprowadzono system unikalnych identyfikatorów `usi_dev_id` i `usi_inv_id`. Zaktualizowano schematy JSON oraz zaimplementowano generator ID w `DeveloperManager`. Przeprowadzono migrację wsteczną (backfill), nadając ID wszystkim 6654 inwestycjom i 2107 deweloperom w bazie. Dodano obsługę `parent_id` dla grup kapitałowych.
### Krok B04

Heurystyka wykrywania podobieństw.

- [x] Opracować ekstrakcję metadanych (NIP, adres, email, www) z surowych JSONów deweloperów do warstwy USI.
- [x] Zaimplementować logikę porównywania deweloperów na podstawie twardych identyfikatorów (NIP, domena www).
- [x] Stworzyć mechanizm punktacji podobieństwa (scoring) łączący dane tekstowe z metadanymi.
- [x] Zintegrować zapis propozycji powiązań do pola `suggestions` w rekordach USI.
- [x] Test: Automatycznie powiązać rekordy z różnych portali mające ten sam NIP i zweryfikować wynik.

**Podsumowanie:**
Zaktualizowano schemat o pole `suggestions`. Zaimplementowano skrypt `detect_similar_devs.py`, który wykorzystuje normalizację nazw oraz dopasowania prefiksowe do wykrywania duplikatów. Przetworzono całą bazę deweloperów, generując propozycje powiązań dla 508 rekordów, co ułatwi późniejsze ręczne łączenie w "master recordy".
### Krok B05

Widok listy deweloperów. taki jak widok listy inwestycji.

- [x] Parametryzować istniejące komponenty list (z `view-list.jsx`), aby obsłużyć dane deweloperów przy minimalnej duplikacji kodu.
- [x] Zintegrować `useDevelopers` w `data.jsx`, wykorzystując te same wzorce co `useInvestments`.
- [x] Dodać widok deweloperów do `App.jsx` i zaktualizować nawigację, zachowując spójny interfejs.
- [x] Dostosować komponenty kart (Card) do wyświetlania skróconych informacji o deweloperze (np. liczba aktywnych inwestycji).
- [x] Test: Zweryfikować, czy widok deweloperów korzysta z tych samych stylów i komponentów co lista inwestycji.

**Podsumowanie:**
Utworzono dedykowany widok listy deweloperów (`view-dev-list.jsx`) oraz endpoint API `/api/developers`. Zaimplementowano hook `useDevelopers` i zintegrowano go z głównym routerem aplikacji w `App.jsx`. Nowy widok wspiera wirtualizację (obsługa tysięcy rekordów) i wyświetla karty deweloperów z informacją o liczbie inwestycji oraz źródłach danych (portale).
### Krok B06

Filtrowanie i wyszukiwanie deweloperów. w belce ListToolbar-Bottom.

- [x] Dostosować `ListToolbar-Bottom` do obsługi filtrów deweloperskich (np. portal źródłowy, miasto, liczba inwestycji).
- [x] Zaimplementować logikę wyszukiwania tekstowego (Search) dla nazw i metadanych deweloperów.
- [x] Dodać opcje sortowania listy deweloperów (alfabetycznie, po dacie aktualizacji, po rankingu).
- [x] Zapewnić reaktywność widoku na zmiany filtrów bez przeładowywania całej listy.
- [x] Test: Przetestować kombinację filtrów i wyszukiwania, weryfikując poprawność wyników na liście deweloperów.

**Podsumowanie:**
Rozszerzono widok listy deweloperów o pełną funkcjonalność filtrowania. Użytkownik może filtrować firmy po portalu źródłowym (RP, OTO, TO) oraz po miastach (na podstawie nazw i metadanych). Zaimplementowano responsywną wyszukiwarkę tekstową działającą w czasie rzeczywistym. Widok zachowuje spójność z listą inwestycji dzięki reużyciu komponentów paska narzędziowego.
### Krok B07

Widok rekordu dewelopera. na wzor widoku A rekordu inwestycji.

- [x] Wykorzystać `DetailRightPanel` i `DetailMain` jako bazę dla widoku dewelopera, unikając tworzenia nowych plików stylów.
- [x] Mapować dane dewelopera (NIP, adres, www) na istniejące komponenty typu `PropertyRow` i `Section`.
- [x] Zaimplementować sekcję powiązanych inwestycji, reużywając komponentów kart inwestycji wewnątrz widoku szczegółów.
- [x] Zintegrować przyciski akcji (np. odświeżenie danych) korzystając z uniwersalnych komponentów UI.
- [x] Test: Potwierdzić, że nawigacja między deweloperem a jego inwestycjami działa płynnie i spójnie wizualnie.

**Podsumowanie:**
Zaimplementowano pełny widok szczegółowy dewelopera (`view-dev-detail.jsx`) oraz endpoint API `/api/developer/<slug>`. Widok zawiera sekcje: Dane Firmy (NIP, KRS, adres), Mapowanie Portali oraz interaktywną listę wszystkich inwestycji dewelopera. Reużyto komponenty kart inwestycji, co zapewnia spójność wizualną i pozwala na bezpośrednią nawigację do szczegółów projektów.
### Krok B08

W rekordzie dewelopera sugestie powiązań spółek na podstawie heurystyki.

- [x] Dodać w widoku szczegółów dewelopera sekcję "Sugerowane powiązania" bazującą na polu `suggestions` w JSON.
- [x] Wyświetlić karty sugerowanych spółek z informacją o powodzie sugestii (np. "Ten sam NIP").
- [x] Zaimplementować interaktywne akcje: "Zatwierdź powiązanie" (Merge) oraz "Odrzuć sugestię".
- [x] Zintegrować akcję zatwierdzenia z mechanizmem `USIdevID`, aktualizując powiązania w systemie plików.
- [x] Test: Wykonać pełny cykl od wykrycia sugestii przez heurystykę do jej zatwierdzenia w UI.

**Podsumowanie:**
Wprowadzono system interaktywnego łączenia rekordów deweloperów. W widoku szczegółowym wyświetlane są sugestie wygenerowane przez heurystykę. Zaimplementowano operację `merge`, która przenosi wszystkie inwestycje (pliki i foldery) od dewelopera źródłowego do docelowego, aktualizując ich metadane w locie. Możliwe jest również trwałe odrzucanie błędnych sugestii.
### Krok B09

Przycisk sprawdzania nowych inwestycji na portalach (w widoku dewelopera).

- [x] Umieścić przycisk "Sprawdź nowe inwestycje" w widoku szczegółów dewelopera (`DeveloperDetail`).
- [x] Zaimplementować endpoint `/api/discover-dev-new`, który uruchamia proces `discover` dla konkretnego `dev_slug`.
- [x] Dodać stan ładowania i wizualny feedback na poziomie rekordu dewelopera podczas skanowania.
- [x] Zapewnić automatyczną aktualizację listy inwestycji przypisanych do dewelopera po znalezieniu nowych rekordów.
- [x] Test: Wywołać skanowanie dla dewelopera, który ma nowe oferty na portalu, i zweryfikować ich pojawienie się w UI.

**Podsumowanie:**
Zintegrowano mechanizm odkrywania nowych inwestycji bezpośrednio z interfejsem użytkownika. W widoku dewelopera dodano przycisk wyzwalający skanowanie wszystkich powiązanych portali (RP, Otodom, TO). Proces działa asynchronicznie dzięki systemowi zadań w tle, a po jego zakończeniu lista inwestycji dewelopera jest automatycznie odświeżana.
### Krok B10

Przycisk wysyłający "Job" pobierania.

- [x] Zaimplementować system kolejkowania zadań (Jobs) w backendzie (np. przy użyciu prostego workera w oddzielnym wątku).
- [x] Dodać endpoint `/api/jobs/status` do monitorowania postępu aktywnych zadań.
- [x] Utworzyć w UI globalny wskaźnik postępu (Progress Bar) lub panel z listą aktywnych zadań.
- [x] Zintegrować akcje wymagające czasu (np. `update-dev`, `sync-images`) z systemem Jobs.
- [x] Test: Uruchomić Job pełnej aktualizacji dewelopera z UI i zweryfikować poprawne raportowanie postępu oraz finalizację zadania.

**Podsumowanie:**
Wdrożono autorski system zarządzania zadaniami w tle (`JobManager`). Pozwala on na asynchroniczne wykonywanie operacji takich jak skanowanie portali bez blokowania głównego wątku serwera. W interfejsie użytkownika dodano komponent `JobStatusOverlay`, który dynamicznie wyświetla pasek postępu i komunikaty o statusie trwających zadań.
### Krok B11

Statystyki dla miast dla danego dewelopera (w widoku dewelopera).

- [x] Dodać w widoku szczegółów dewelopera sekcję "Zasięg inwestycji" ze statystykami rozbitymi na miasta.
- [x] Zaimplementować obliczanie metryk (liczba inwestycji, suma mieszkań, średnia ocena) dla każdego miasta dewelopera.
- [x] Wyświetlić zagregowane dane w formie kompaktowej tabeli lub listy "city cards" w profilu dewelopera.
- [x] Dodać szybkie linki filtrujące listę inwestycji dewelopera do konkretnego miasta.
- [x] Test: Zweryfikować poprawność statystyk dla dewelopera o szerokim zasięgu terytorialnym.

**Podsumowanie:**
Wprowadzono sekcję analityczną "Zasięg inwestycji" w widoku dewelopera. System automatycznie agreguje dane o inwestycjach, obliczając dla każdego miasta: liczbę projektów, całkowitą liczbę mieszkań oraz średnią ocenę USI. Dodano mechanizm filtrowania lokalnego, pozwalający szybko zawęzić widoczne inwestycje do konkretnego miasta.

## Następny kamień milowy: Domowe obiady

### Krok N01

. Podstrona raporty.  
### Krok N02

. Lista raportów generowana na podstawie JSONów.  
### Krok N03

. JSONy raportów określają filtry inwestycji (np. GUS, region, deweloper, odległość od punktu na mapie).  
### Krok N04

. JSONy raportów określają moduły prezentacji pokazywane w raporcie.  
### Krok N05

. Moduły (wymagają danych wejściowych):  
   * Mapa z punktami (wymaga listy).  
   * Wykres zmian cen w czasie (wymaga listy cen).  
   * Wykres zmian oceny w czasie (wymaga listy ocen).  
   * Wykres ceny w zależności od oceny.  
   * Wykres zmian oceny w kategorii w czasie.  
### Krok N06

. Zapewnienie uniwersalności i elastyczności modułów (możliwość osadzania w innych miejscach).

## Przyszłe kamienie milowe

### Krok P01

- [ ] uruchomienie na raspberry pi - dopiero po przejsciu rozleglych testow na lokalnym komputerze

### Krok P02

- [ ] Analiza trendów cenowych: zmiana średniej ceny za m² w czasie.
- [ ] Porównywarka inwestycji: widok side-by-side dla wybranych ofert.
- [ ] Raport "Okazje": automatyczne wykrywanie spadków cen i nowych ofert.
- [ ] Heatmapa dostępności: zagęszczenie inwestycji na mapie.

### Krok P03

- [ ] Eksport do XLSX/CSV dla przefiltrowanych list inwestycji.

### Krok P04

- [ ] System powiadomień o nowych inwestycjach (crawler alerts).

### Krok P05

Podstrona Deweloperzy. Utworzenie podstrony do przegladania listy deweloperów.

- [ ] Utworzyc podstrone Deweloperzy
- [ ] Pobieranie i zarządzanie listą deweloperów (przeniesione z B27)
- [ ] Automatyczne dopasowywanie inwestycji do deweloperów na podstawie danych portalowych

### Krok P06

Przeniesione z Pizzeria (B01).

- [ ] Wyszukiwanie z API wikipedii interesujących obiektów w okolicy na podstawie lokalizacji

### Krok P07

- [ ] Integracja z API Wikipedii dla obiektów w okolicy
