# Analiza pokrycia pól: scrapery vs kolumny Coda

## Wniosek główny

Pokrywanie się pól to **podział ról, nie redundancja**:

- `rp_details.json` / `oto_details.json` — surowe dane API/scraper, używane przez formuły `.ParseJSON` w Coda
- Kolumny Coda — przetworzone pochodne: scoring, odległości, mapy, obliczone oceny

## Pola pokrywające się: RynekPierwotny ↔ Coda

| rp_details (JSON) | Kolumna Coda |
|---|---|
| `name` | `Inwestycja` |
| `geo_point.value.coordinates` [lon, lat] | `Latitude`, `Longitude` |
| `region` | `Region` |
| `properties` | `Liczba Mieszkań` |
| `construction_date_range.value.upper` | `Termin` |
| `facilities` (lista obiektów) | `RPfacilities`, `RPfacVal` |
| `website` | `strona_inwestycji` |
| `vendor.value.slug` | (część) `Deweloper` |
| `floors_above_ground_range` | `kondygnacje` |

## Pola pokrywające się: Otodom ↔ Coda

| oto_details (`ad`) | Kolumna Coda |
|---|---|
| `title` | `Inwestycja` |
| `location.mapDetails.lat/lon` | `Latitude`, `Longitude` |
| `target.Number_of_properties` | `Liczba Mieszkań` |
| `target.Price_per_m_from` | `cena min` / `cena maks` |
| `featuresByCategory` / `features` | `OTOfeatures`, `Udogodnienia` |
| `images` | `imgList` |

## Pola wyłącznie w Coda (obliczane przez formuły)

Nie mają odpowiedników w surowych JSON — są w 100% produkowane przez Codę:

- `Gwiazdki`, `Ocena`, `ocenaLOG`, `ocena_wazona`, `ocena_lista` — system oceniania
- `RPfacVal` — numeryczna wartość udogodnień RP
- `Odległość`, `OdProjektu`, `Qdystans`, `QTermin` — obliczane odległości i kwartyle
- `Mapa`, `google-maps`, `Pin`, `POIx2`, `POIx3`, `POIx4` — generowane URL-e map
- `dowody*` (dowodyBalkony, dowodyFasady, itd.) — evidencja scoringowa
- `Segment` — ręczna kategoryzacja
- `USIOjciec` — powiązanie z inwestycją nadrzędną
- `GeminiScore` — ocena AI

## Pola w scraperach nieobecne w Coda (potencjalnie cenne)

Dane dostępne w plikach szczegółów, ale nieeksponowane jako kolumny Coda:

**RynekPierwotny:**
- `description` — pełny opis inwestycji
- `stats` — histogram i przedziały cenowe
- `buildings` — szczegóły budynków
- `funds_protection`, `payment_description` — warunki płatności
- `slogan`, `location_description`, `poi_description`

**Otodom:**
- `description` — pełny opis HTML
- `characteristics` — dokładne zakresy metraży, liczby pokoi
- `additionalInformation` — dodatkowe cechy
- `topInformation` — kluczowe parametry (np. liczba pięter)
- `target.Area_from/to` — zakres metraży

## Ryzyko: drift danych

Gdy Coda oblicza kolumnę na podstawie `rp_details.json` i plik zostaje nadpisany importem ze starszych danych CSV, wartości w Coda mogą się rozjechać z plikiem. Mechanizm `last-row-wins` w `csv_importer.py` minimalizuje to ryzyko dla duplikatów w CSV.
