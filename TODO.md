# TODO

## Bieżący kamień milowy: Analiza Trendów

### Krok B01

Analiza trendów cenowych: zmiana średniej ceny za m² w czasie.

- [ ] Zaimplementować moduł `PriceHistoryModule` pobierający dane z historycznych plików USI.
- [ ] Dodać wykres liniowy trendu ceny średniej dla wybranych grup inwestycji.
- [ ] Stworzyć widżet "Zmiana ceny" na karcie inwestycji pokazujący % różnicy względem poprzedniego miesiąca.

### Krok B02

Porównywarka inwestycji: widok side-by-side dla wybranych ofert.

- [ ] Dodać mechanizm "Koszyka" do zaznaczania inwestycji do porównania.
- [ ] Stworzyć widok `ComparisonTable` zestawiający parametry techniczne i oceny w układzie kolumnowym.
- [ ] Dodać funkcję wyróżniania różnic (np. najniższa cena w grupie).

### Krok B03

Raport "Okazje": automatyczne wykrywanie spadków cen i nowych ofert.

- [ ] Zaimplementować algorytm wykrywający istotne (np. >3%) obniżki ceny m².
- [ ] Stworzyć dedykowany moduł raportowy prezentujący "Okazje tygodnia".
- [ ] Dodać oznaczenie "New" dla rekordów dodanych w ciągu ostatnich 7 dni.

### Krok B04

Heatmapa dostępności: zagęszczenie inwestycji na mapie.

- [ ] Zaimplementować moduł `HeatmapModule` wykorzystujący HERE Maps Layer API lub własną agregację punktów.
- [ ] Dodać przełącznik trybu mapy (punkty vs heatmapa) w Dashboardzie.

## Następny kamień milowy: Eksploracja okolicy

### Krok N01

- [ ] Integracja z API Wikipedii dla obiektów w okolicy (Wyszukiwanie interesujących obiektów).
- [ ] Wizualizacja punktów POI z Wikipedii na mapie sąsiedztwa inwestycji.

## Przyszłe kamienie milowe

### Krok P01

- [ ] uruchomienie na raspberry pi - dopiero po przejsciu rozleglych testow na lokalnym komputerze

### Krok P02

- [ ] Eksport do XLSX/CSV dla przefiltrowanych list inwestycji.

### Krok P03

- [ ] System powiadomień o nowych inwestycjach (crawler alerts).
