# TODO

## Bieżący kamień milowy: Poprawki UI i stabilizacja biblioteki

### Krok B01 — Naprawa krytycznych błędów i optymalizacja logowania

Ten krok skupia się na usunięciu błędów runtime oraz uporządkowaniu wyjścia konsoli.

- [x] Naprawa crashu "Red Screen of Death" (TypeError w StandardCard)
- [x] Rozwiązanie problemu %20 w nazwach plików (normalizacja i fallback w API)
- [x] Wyciszenie logów pollingu (/api/jobs, /api/crawler) w konsoli
- [x] Implementacja kolejkowania zadań i opóźnień (delay) w JobManager (ochrona przed floodem/banami)
- [ ] karty deweloperow powinny pokazywac liczbe nowych inwestycji
- [ ] usi-library-health pokazuje ze jest zle
- [ ] skanowanie inwestycji sie popsulo. nie ma pokazywanych zadnych rezultatow

## Następny kamień milowy: Porządkowanie bazy deweloperów

### Krok N01 — Narzędzia do łączenia zdublowanych rekordów

- [ ] Opracowanie mechanizmu automatycznego wykrywania duplikatów po slugach (np. dom-development-sa vs dom-development-s-a)

## Przyszłe kamienie milowe

- **Historia cen** — Śledzenie zmian cen i terminów oddania na poziomie dewelopera
- **Eksport raportów** — Generowanie PDF/Excel z widoków analitycznych
