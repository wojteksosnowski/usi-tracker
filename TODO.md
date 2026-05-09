# TODO

## Bieżący kamień milowy: Czyszczenie artefaktów SVG

### Krok B01
Weryfikacja i ujednolicenie pozostałości SVG w kodzie.
- [ ] Znaleźć i skatalogować wszystkie wystąpienia `<path d="M22.85..." />`.
- [ ] Sprawdzić czy odwołują się do `usi-star-` lub `usi-zero-`.
- [ ] Ujednolicić użycie z poprawnymi zasobami projektowymi.

## Następny kamień milowy: Odświeżanie rekordów

### Krok N01
Dodanie funkcji odświeżania surowych danych i zdjęć w widoku szczegółowym.
- [ ] Dodać przycisk "Odśwież dane" w widoku DetailsViewA.
- [ ] Zintegrować przycisk z backendem (wywołanie JobManager dla danego slug).
- [ ] Obsłużyć powiadomienie o sukcesie/błędzie aktualizacji.

## Przyszłe kamienie milowe

- Zmiana statusu w widoku A z "AI" na "Wstępna" nie zmieniła wyswietlanego statusu w metadanych. Przykład do weryfikacji: "/Public/USIdata/2e-sp-z-oo/osiedle-kedzierskiego-radom"