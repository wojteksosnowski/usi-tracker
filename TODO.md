# TODO

## Kamień 05
### Krok 05.01
Przebudowa architektury stanu inwestycji na model statyczny: przeniesienie ciężaru obliczania i rozwiązywania danych (takich jak `images`, `amenities_score`, dołączenia ratings) z loadera generującego stan w locie (odczyt) do momentu zapisu i zrzut tych danych bezpośrednio do bazowego `usi_*.json`. Zmiana `investment_loader.py` na czysty "odczytywacz" tego pliku.

- [x] Utworzenie i uruchomienie skryptu np. `scripts/backfill_usi_data.py`, wykorzystującego istniejący kod `load_investment` do pobrania w locie wygenerowanych danych (`photos`, `amenities_score`, `suggested_udogodnienia`, `ratings_data`) i trwałego zapisania ich wewnątrz wszystkich plików `usi_*.json`.
- [x] Przebudowa modułu scalającego w `python_worker/adapters/merger.py` (i `InvestmentSyncService`), aby podczas każdej nowej synchronizacji wyliczał te same pola i utrwalał je w końcowym JSON-ie `usi_*.json`.
- [x] Całkowite odchudzenie pliku `python_worker/services/investment_loader.py` poprzez usunięcie dynamicznego wczytywania plików pobocznych (`ratings.json`, `deletion_list.json`), usuwanie `resolve_images()` i kalkulacji score'ów. Loader ma jedynie wczytywać gotowy payload.
- [x] Weryfikacja działania i uruchomienie testów potwierdzających zmianę architektury.

**Podsumowanie:** Napisano i poprawnie zrealizowano backfill wszystkich plików JSON w publicznej bazie `usi_*.json`. Dokonano migracji generacji stanu (score'y udogodnień, podpowiedzi, rozwiązywanie obrazów, łączenie komentarzy ratings) ze statycznego loadera z powrotem do funkcji odpowiedzialnych za zapis (m.in. po stronie klasy `InvestmentSyncService`). Loader w `investment_loader.py` służy już tylko jako interfejs odczytujący utrwalone dane. Testy uruchomiono. Zlikwidowano duży narzut opóźnienia, jaki powstawał na widoku głównym.

## Kamień 06 Naprawy
### Krok 06.01
Zbadaj uzycie metody `getDistance()` podczas przegladania inwestycji. Sprawdz czy jest wywolywana przy kazdej okazji. Liczenie odleglosci powinno byc ostatecznoscia i dotyczyc tylko tych inwestycji ktore sa w zasiegu lat i lon. Odleglosci powinny byc zapisywane raz na zawsze poniewaz inwestycje nie przesuwaja sie. W rzadkich sytuacjach moze dojsc do korekty lokalizacji (np. zle dane wejsciowe) ale wtedy obliczenie odleglosci bedzie wymuszone i tylko w takim przypadku.

- [x] (06.01.01) Aktualizacja `python_worker/schemas/usi_unified.schema.json` o pole `nearby_investments` (lista ID + dystans).
- [x] (06.01.02) Implementacja mechanizmu detekcji zmiany lokalizacji w `Merger._detect_changes` oraz logiki wyliczania `nearby_investments` w `InvestmentSyncService`.
- [x] (06.01.03) Utworzenie skryptu `scripts/backfill_distances.py` do jednorazowego przeliczenia odległości dla wszystkich 7500+ rekordów i aktualizacji plików `usi_*.json`.
- [x] (06.01.04) Refaktoryzacja `python_worker/ui/view-detail.jsx` - usunięcie kosztownego przeliczania O(N) na froncie na rzecz korzystania z danych pre-kalkulowanych w obiekcie inwestycji.
- [x] (06.01.05) Weryfikacja wydajności UI przy przełączaniu inwestycji oraz testy regresyjne poprawnego zapisu odległości.
- [x] (06.01.06) Modyfikacja `InvestmentSyncService` – lazy initialization komponentów scrapujących w celu redukcji obciążenia CPU.
- [x] (06.01.07) Aktualizacja `InvestmentLoader` – dodanie flagi `fast_index` dla zdjęć (pomijanie rekonstrukcji pełnej listy przy budowaniu indeksu).
- [x] (06.01.08) Aktualizacja `InvestmentIndex` – usunięcie nadmiarowych danych z `_index.json` (pełne photos, nearby_investments).
- [x] (06.01.09) Przebudowa indeksu (`rebuild-index.sh`).

**Podsumowanie:**
Zrealizowano optymalizację wyliczania odległości. Przeniesiono ciężar obliczeń z frontendu (O(N)) na backend/warstwę danych. Odległości są teraz pre-kalkulowane podczas synchronizacji (jeśli współrzędne uległy zmianie) i trwale zapisywane w plikach `usi_*.json` w nowym polu `nearby_investments`. Wykonano pełny backfill dla ponad 6900 rekordów. Frontend został odchudzony i korzysta z gotowych danych, co eliminuje lag przy przeglądaniu inwestycji.
### Krok 06.02
problem ze zle wystwietlajacymi sie zdjeciami pozostal. wprawdzie lag jest
  teraz krotszy ale jest widoczny. to znaczy ze UI wyswietla wszystkie
  informacje natychmiast (adres, minimapa, metadane) ale na zdjecia czeka. po
  kilku przejsciach pomiedzy inwestycjami UI zaczyna pokazywac niewlasciwe
  zdjecie hero. po kilku nastepnych przejsciach przestaje pokazywac zdjecia
  tylko puste placeholdery. tymczasem obciazenie procesora rosnie i rosnie,
  chociaz nic sie nie dzieje. przeanalizuj na jakiej petli zacina sie serwer;
  dlaczego zmieniaja sie zdjecia ale hero jest wyswietlane stare; dlaczego mam
  lag dla zdjec ale nie dla metadanych.

- [x] (06.02.01) Implementacja `AbortController` w `view-detail.jsx` dla zapytań o dane inwestycji.
- [x] (06.02.02) Wprowadzenie "Sync Guard" w `view-detail.jsx` – natychmiastowe czyszczenie stanu (zdjęć) przy zmianie inwestycji.
- [x] (06.02.03) Naprawa modułu "W okolicy" – synchronizacja `nearbyInvestments` z pełnego obiektu `fullInv`.

### Krok 06.03
w obszarze metadanych widoku inwestycji zanim pojawia sie zdjecia widac sciezke inwestycji. w momencie gdy pojawia sie zdjecia do sciezki dodawana jest /Volumes/Samsam/ moze frontend/backend nie wiedza gdzie sa zdjecia bo nie uzupelniaja sciezki i szukaja za kazdym razem w zlym miejscu??

- [x] (06.03.01) Weryfikacja i poprawka twardych ścieżek `/Volumes/Samsam/` w `investment_loader.py` oraz `image_resolver.py`.


## Kamień 07 Kaskada rglob wywołana przez nieatomowy zapis indeksu
### Krok 07.01
Weryfikacja i usunięcie użycia `rglob("usi_*.json")` jako fallbacku dla brakującego lub uszkodzonego indeksu `_index.json`.

- [x] Usunięto logikę fallbacku `rglob` w `InvestmentIdentityResolver`.
- [x] Zweryfikowano, że `rglob` jest używany wyłącznie w bezpiecznych operacjach (rebuild indeksu, CLI).
- [x] Zapewniono, że błąd odczytu indeksu nie wyzwala masowego skanowania plików w czasie rzeczywistym.

**Podsumowanie:** Całkowicie wyeliminowano ryzyko paraliżu serwera przez kaskadowe skanowanie `rglob` w resolverze tożsamości.

## Kamień 08 Brak blokady (Lock) na odczycie _index.json w pamięci
### Krok 08.01
Zapewnienie bezpiecznego dostępu do cache'u indeksu w środowisku wielowątkowym.

- [x] Wprowadzono `_index_lock` (threading.Lock) w `python_worker/investment_index.py`.
- [x] Odczyt pliku i aktualizacja zmiennych globalnych odbywa się teraz wewnątrz sekcji krytycznej.
- [x] Wyeliminowano sytuację, w której wiele wątków symultanicznie parsuje ten sam 20MB plik JSON.

**Podsumowanie:** Dostęp do indeksu w pamięci jest teraz bezpieczny wątkowo.

## Kamień 09 Kosztowna obsługa fallbacku 404 w endpointach obrazków
### Krok 09.01
Optymalizacja fallbacku dla brakujących obrazków.

- [x] Wprowadzono `_cdn_redirect_cache` i `_missing_images_cache`.
- [x] Zaimplementowano `_fallback_lock` w `serve_image`, aby zapobiec jednoczesnemu skanowaniu dysku dla tego samego brakującego zasobu.

**Podsumowanie:** Zoptymalizowano obsługę brakujących obrazów, drastycznie redukując I/O przy brakujących zasobach.

## Kamień 10 Błąd logiki pętli w funkcji serve_image
### Krok 10.01
Poprawa pętli przeszukującej ścieżki zdjęć w fallbacku.

- [x] Usunięto bezwarunkowy `break`, który przerywał przeszukiwanie po pierwszym pliku JSON.
- [x] Kod poprawnie przechodzi przez wszystkie dostępne pliki `usi_*.json` w folderze inwestycji.

**Podsumowanie:** Naprawiono błąd logiczny w endpoint'cie obrazków.

## Kamień 11 Brak kontroli nad współbieżną przebudową indeksu
### Krok 11.01
Zabezpieczenie przed lawinowym uruchamianiem wątków `rglob`.

- [x] Wprowadzono `_rebuild_lock` oraz flagę `_is_rebuilding` w `investment_index.py`.
- [x] Dodano sprawdzenie stanu przebudowy w endpointcie `/investments`, blokując duplikowanie ciężkich zadań tła.
- [x] Wyeliminowano skoki CPU spowodowane dziesiątkami równoległych skanów USIdata (25k+ plików).

**Podsumowanie:** System poprawnie kolejkuje zadania przebudowy indeksu, zapobiegając panice CPU przy dużym obciążeniu.

## Kamień 12 Optymalizacja dostępu O(1) do danych (Hot Index)
### Krok 12.01
Wprowadzenie mapowania słownikowego dla przyspieszenia wyszukiwania.

- [x] Zaimplementowano `_hot_index` (slugs/ids map) w pamięci.
- [x] Zrefaktoryzowano resolver tożsamości oraz fallback obrazków do korzystania z `get_entry_by_slug` i `get_entry_by_id`.
- [x] Wyeliminowano pętle O(N) po 7000+ elementach przy każdym żądaniu obrazka lub detali.

**Podsumowanie:** Drastycznie przyspieszono kojarzenie slugów z ID, co ostatecznie rozwiązało problem zawieszania się serwera podczas szybkiego przeglądania UI.
