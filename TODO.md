# TODO

## Bieżący kamień milowy: Lodziarnia

Ten kamien milowy uporzadkuje importowanie z RP, OTO i TO. Podstrona Pobieranie.

### Krok B01

RP: używanie JSON query tak jak coda.io JSONMAIN RP.

- [ ] Implementacja JSON query dla RP

### Krok B02

OTO: używa predefiniowanej listy adresów, skąd zaciąga listę z HTML (zagnieżdżony JSON).

- [ ] Implementacja scrapowania listy OTO z HTML/JSON

### Krok B03

RP i OTO: zaciąga listę wskaźników inwestycji, którą najpierw odmiela z powtórzeń względem bazy usidata.

- [ ] Mechanizm deduplikacji wskaźników inwestycji

### Krok B04

Wskaźniki inwestycji są otwierane i system pobiera surowy JSON inwestycji.

- [ ] Pobieranie surowych JSONów inwestycji

### Krok B05

Z surowego JSONA system pobiera grafiki i metadane.

- [ ] Ekstrakcja grafik i metadanych z JSON

### Krok B06

Należy zawsze pobierać największy dostępny rozmiar grafik.

- [ ] Implementacja wyboru największego rozmiaru zdjęć

### Krok B07

Tabela ofert powinna naśladować mechanizm RP i OTO.

- [ ] Implementacja mechanizmu dla Tabeli Ofert

### Krok B08

1. Przycisk do zeskanowania nowości bez pobierania.

- [ ] Dodanie przycisku skanowania nowości

### Krok B09

2. Przycisk do pobierania. Przed przyciskiem toggle dla 3 stron RP, OTO, TO

- [ ] Dodanie przycisku pobierania z togglem portali

### Krok B10

4. Postęp w formie: napis informujący o aktualnym działaniu oraz tekstowa belka postępu.

- [ ] Implementacja wskaźnika postępu w UI

### Krok B11

5. Delay między zapytaniami, szczególnie dla Otodom (ryzyko blokowania).

- [ ] Dodanie opóźnień (rate limiting) dla scraperów

### Krok B12

6. Graficzna informacja o liczbie nowych ofert na inwestycji.

- [ ] Wyświetlanie licznika nowych ofert w UI

## Następny kamień milowy: TBD

### Krok N01

- [ ] Zdefiniuj zadania dla kolejnego etapu

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
