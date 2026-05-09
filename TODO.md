# TODO

## Bieżący kamień milowy: Czyszczenie artefaktów kodu

### Krok N01
Widok A - Przenieść hero-band-actions-row do ActionBar

### Krok N02
Widok C - SlideShow powinien pokazywać cały obraz bez scrollowania

### Krok N03
W bibliotece modulow nie ma MiniMap. Przeoczenie lub MiniMap nie jest zbudowana jako moduł?

### Krok N04
Strona Deweloperzy - pole wyszukiwania nie działa.

### Krok N05
Strona Deweloperzy - filtrowanie po miastach jest zbedne na stronie deweloperzy.

### Krok N06
Strona Deweloperzy - klikniecie połącz wydaje się nic nie robic. Drugie klikniecie powoduje pojawienie sie ERROR 500 w popup.

## Ukończone kamienie milowe

### Wydzielnie usi-scrapers (2026-05-09)
Wydzielono scrapery, Fetcher i adaptery do osobnego, wersjonowanego pakietu Python.
- [x] Inicjalizacja repozytorium usi-scrapers
- [x] Ekstrakcja warstwy pobierania (Fetcher)
- [x] Ekstrakcja Scraperów i Adapterów
- [x] Definicja API, Typów i Testów (Kontrakt)
- [x] Integracja pakietu w usi-tracker ("Shim")
- [x] Naprawa TabelaOfert v0.1.8 i czyszczenie bazy danych (40 rekordów)


## Przyszłe kamienie milowe

- `<div className="usi-pill outline usi-mono usi-tiny" style={{borderColor: 'var(--usi-accent)', color: 'var(--usi-accent)' }}>` wciaz jest przykladem inline style. czy nie mozna zrealizowac tego inaczej jezeli nie - nalezy pozostawic. Doglebna naliza wykonalnosci.

- W kodzie plączą się `<path d="M22.85` to są pewnie pozostałości. Nalezy sprawdzić czy to nie są nasze usi-star- i usi-zero-. Jezeli `<path d="M22.85` nie nalezy do usi-star- lub usi-zero- uwzpolnic z innymi odwołaniami do usi-star-