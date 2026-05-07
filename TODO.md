# TODO

## Bieżący kamień milowy: Poprawki 2

### Krok B05
Przeprowadź audyt stosowania inline styles w plikach .js i .jsx. Cały style ma być osadzony w plikach CSS. Popraw i przeprowadź test miedzy innymi stylelint.
- [x] Przeszukaj pliki .jsx i .js w poszukiwaniu `style={{`
- [x] Przenieś style do `components.css` lub `views.css` tworząc semantyczne klasy
- [x] Zastąp inline styles klasami w komponentach
- [x] Uruchom `lint-styles.sh` i zweryfikuj wizualnie

**Podsumowanie:** Przeniesiono większość statycznych stylów inline do `components.css` i `global.css`. Zastąpiono je semantycznymi klasami i utility classes. Wynik stylelint jest pomyślny.

### Krok B06
Sprawdzic czy views.css nie jest zbyt "tłusty". Czy wystepuja elementy ktore nie sa juz nigdzie uzywane? 
- [x] Przeanalizuj `views.css` pod kątem martwych selektorów (używając `grep` po kodzie JSX)
- [x] Usuń nieużywane klasy CSS
- [x] Wykonaj test regresji wizualnej widoków
- [x] Uruchom `lint-styles.sh`

**Podsumowanie:** Przeanalizowano `views.css` i usunięto ponad 800 linii nieużywanego kodu CSS (zredukowano z 1261 do 405 linii). Pozostałe klasy są aktywnie używane w komponentach UI. Wynik stylelint jest pomyślny.
### Krok B07
"W okolicy
Brak innych inwestycji w promieniu 5km." - tak wysiwetla sie w inwestycji "Pas Startowy bud. A i B". Moze modul tej karty nie dziala? Moze nie odbiera lokalizacji inwestycji z bus?
- [ ] Zdebuguj `DataBus` w `data.jsx` pod kątem wyliczania `nearbyInvestments`
- [ ] Sprawdź poprawność współrzędnych inwestycji "Pas Startowy" w JSON
- [ ] Napraw logikę filtrowania dystansu lub subskrypcję busa
- [ ] Zweryfikuj wyświetlanie listy w widoku `DetailsA`

### Krok B08
DetailsA powinien miec pierwsza kolumne ok. 50% szerokosci, a druga i trzecia kolumna po ok. 25% szerokości. 
- [ ] Zidentyfikuj selektory `.detail-grid` i kolumny w `views.css`
- [ ] Zmień `grid-template-columns` na `2fr 1fr 1fr` (50%/25%/25%)
- [ ] Sprawdź responsywność widoku szczegółowego (breakpointy)
- [ ] Wykonaj test wizualny
### Krok B09
W widoku rekordu inwestycji Metadane przeniesc z pierwszej kolumny do trzeciej kolumny. 
- [ ] Przenieś komponent `MetadataPanel` z pierwszej kolumny do trzeciej w `DetailViewA.jsx`
- [ ] Dostosuj odstępy (gap/padding) w kolumnach po przesunięciu
- [ ] Sprawdź spójność układu w innych wariantach widoku Detail (jeśli istnieją)
- [ ] Zweryfikuj wizualnie

### Krok B10
W metadanych pokazywać maksymalną i minimalną cenę za 1 m2 mieszkania.
- [ ] Sprawdź obecność pól `price_m2_min` / `price_m2_max` w zunifikowanym JSON
- [ ] Zaktualizuj komponent wyświetlający metadane o te dwa parametry
- [ ] Jeśli brak danych, zaktualizuj adaptery (`python_worker/adapters/`) aby wyliczały/pobierały te ceny
- [ ] Zweryfikuj wyświetlanie w UI dla różnych portali

### Krok B11
Nadal wystepuje problem z DataGrid i Standardcard. Siatka nie jest skalowana do szerokosci okna i wycieka za prawą krawędź w przypadku pobrania rekordow z tabela ofert. Sposob wyswietlenia miniatur i jak one wypełniają zarezerwowana przestrzen w karcie wymaga poprawy.
- [ ] Przeanalizuj logikę `columnCount` i `minCardWidth` w `DataGrid.jsx`
- [ ] Napraw błąd wyciekania siatki poza krawędź kontenera (flex/grid overflow)
- [ ] Popraw proporcje i wypełnienie miniatur w `StandardCard` / `ListCard`
- [ ] Przetestuj na danych z `tabelaofert` (wysoka gęstość danych)

### Krok B12
Powidomienia w obszarze powiadomień wciąz nie działają. Wciaz widać spinnery, nie ma tekstu powiającego się w NavbarShell. Obszar powiadomien opisany jest w docs/obszar-powiadomien.md
- [ ] Sprawdź logikę odświeżania `/api/jobs` w `app.jsx`
- [ ] Napraw błąd w `NotificationCenter` (brak renderowania tekstu, wieczny spinner)
- [ ] Sprawdź spójność z implementacją w `python_worker/api/blueprints/jobs.py`
- [ ] Przeprowadź test E2E z długim zadaniem (np. `discover`)

### Krok B13
Pobrany rekord z tabelaofert: "/Public/USIdata/jhm-development-s-a/nove-diamentowe-topazowa-28-konin-osiedle-wladyslawa-sikorskiego-mieszkania-na-sprzedaz" nie posiada metadanych.
- [ ] Przeanalizuj plik `raw_to.json` dla rekordu "nove-diamentowe..."
- [ ] Sprawdź `TOAdapter` pod kątem mapowania parametrów (rok budowy, liczba pięter itp.)
- [ ] Napraw błąd w ekstrakcji danych z payloada TabelaOfert
- [ ] Przeprowadź `update-inv` dla tego rekordu i zweryfikuj zunifikowany JSON

## Następny kamień milowy: Poprawki 3

### Krok N01
W kodzie plączą się ```<path d="M22.85``` to są pewnie pozostałości. Nalezy sprawdzić czy to nie są nasze usi-star- i usi-zero-. Jezeli ```<path d="M22.85``` nie nalezy do usi-star- lub usi-zero- uwzpolnic z innymi odwołaniami do usi-star-

### Krok N02
```<div className="usi-pill outline usi-mono usi-tiny" style={{borderColor: 'var(--usi-accent)', color: 'var(--usi-accent)' }}>``` wciaz jest przykladem inline style. czy nie mozna zrealizowac tego inaczej jezeli nie - nalezy pozostawic.

### Krok N0


### Krok N0

### Krok N0

### Krok N0

### Krok N0

### Krok N0

### Krok N0






## Przyszłe kamienie milowe

