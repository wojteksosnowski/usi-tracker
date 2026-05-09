# TODO

## Bieżący kamień milowy: Czyszczenie artefaktów SVG

### Krok B01
Weryfikacja i ujednolicenie pozostałości SVG w kodzie.
**Plan:** 2026-05-09
- [x] Znaleźć i skatalogować wszystkie wystąpienia `<path d="M22.85..." />`.
- [x] Sprawdzić czy odwołują się do `usi-star-` lub `usi-zero-`.
- [x] Ujednolicić użycie z poprawnymi zasobami projektowymi.

**Podsumowanie:** Zidentyfikowano wszystkie wystąpienia surowej ścieżki SVG i potwierdzono ich powiązanie z brandingiem USI. Zunifikowano kod poprzez dodanie ikon usiLogo, usiStar i usiZero do komponentu Icon.jsx oraz podmienienie surowych ścieżek i obrazów .svg w komponentach app.jsx, core.jsx i ratings.jsx.

## Następny kamień milowy: Odświeżanie rekordów

### Krok N01
Dodanie funkcji odświeżania surowych danych i zdjęć w widoku szczegółowym.
- [ ] Dodać przycisk "Odśwież dane" w widoku DetailsViewA.
- [ ] Zintegrować przycisk z backendem (wywołanie JobManager dla danego slug).
- [ ] Obsłużyć powiadomienie o sukcesie/błędzie aktualizacji.

## Przyszłe kamienie milowe

- Zmiana statusu w widoku A z "AI" na "Wstępna" nie zmieniła wyswietlanego statusu w metadanych. Przykład do weryfikacji: "/Public/USIdata/2e-sp-z-oo/osiedle-kedzierskiego-radom"