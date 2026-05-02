# Pobieranie danych z TabelaOfert.pl (TO)

Dokumentacja procesów pobierania, ekstrakcji danych oraz ujednolicania rekordów dla portalu TabelaOfert.pl.

## 1. Mechanizm Pozyskiwania Danych

TabelaOfert.pl jest portalem silnie chronionym przez systemy anty-botowe (Cloudflare). System USI Tracker stosuje dwustopniową strategię pozyskiwania danych:

### A. Ekstrakcja JSON-LD (Schema.org)
Większość danych technicznych (nazwa, deweloper, cena, opis) jest pobierana z ustrukturyzowanego bloku `application/ld+json` (typ `Product` lub `ItemList`).
*   **Zaleta**: Gwarantuje stabilność pól niezależnie od zmian w layoutcie strony.
*   **Wyzwanie**: Często brakuje tam współrzędnych geograficznych (GPS).

### B. Omijanie blokad (Impersonation & ScraperAPI)
Portal odrzuca standardowe zapytania `requests`.
- **Primary**: `Fetcher` używa biblioteki `curl_cffi` z parametrem `impersonate="chrome120"`, co pozwala na bezpośrednie pobieranie danych bez kosztów ScraperAPI.
- **Fallback**: W przypadku wykrycia blokady (403), system automatycznie przełącza się na **ScraperAPI**.

## 2. Zapytania i Discovery

System realizuje discovery poprzez skanowanie profili deweloperów na TO:

1.  **Discovery (Listing dewelopera)**:
    - URL: `https://tabelaofert.pl/deweloper/{developer-slug}`
    - Cel: Wyciągnięcie wszystkich aktywnych inwestycji dewelopera.
2.  **Scrape (Szczegóły)**:
    - URL: `https://tabelaofert.pl/inwestycja/{investment-slug}`
    - Cel: Pobranie pełnego JSON-LD oraz galerii zdjęć.

## 3. Specyficzne Wyzwania i Rozwiązania (Lessons Learned)

Podczas wdrożenia TabelaOfert rozwiązano kluczowe problemy techniczne:

### Inteligentna Skala Obrazów (CDN Scaling)
TO serwuje zdjęcia przez CDN z parametrami w URL (np. `quality_70,scale_500`).
- **Problem**: Ten sam obraz występuje w wielu rozdzielczościach.
- **Rozwiązanie**: Implementacja algorytmu w `TOAdapter`, który parsuje parametr `scale_N`, grupuje obrazy po unikalnej nazwie pliku i wybiera **najwyższą dostępną wartość** (zazwyczaj `scale_1584`).

### Fallback Geokodowania (HERE Maps)
Wiele ofert na TO nie posiada współrzędnych w kodzie strony.
- **Rozwiązanie**: Jeśli `TOAdapter` nie znajdzie lat/lng, automatycznie wykorzystuje `geocode_address` z modułu `here_maps.py`, aby wyznaczyć punkt na podstawie adresu tekstowego.

### Czyszczenie Nazewnictwa
TO często dodaje przyrostki do nazw (np. "Inwestycja X - TabelaOfert.pl").
- **Rozwiązanie**: Funkcja `extract_to_data` w scraperze usuwa zbędne frazy marketingowe, zapewniając czyste nazwy zgodne z USI Tracker.

## 4. Mapowanie Danych (TOAdapter)

| Pole USI | Źródło w TabelaOfert | Metoda |
| :--- | :--- | :--- |
| `name` | `JSON-LD -> name` | Czyszczenie przyrostków |
| `coords` | `JSON-LD -> geo` lub `_extracted_location` | Fallback: Geokodowanie HERE |
| `delivery_date` | `additionalProperty[Termin oddania]` | Parsowanie dat rzymskich (np. IV kw. 2024) |
| `image_urls` | `_raw_gallery_urls` | Wybór max(scale_N) |

## 5. Przykłady

### Fragment JSON-LD (Schema.org):
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Nowe Kolibki",
  "brand": { "name": "Invest Komfort" },
  "offers": {
    "@type": "AggregateOffer",
    "lowPrice": "15000",
    "offerCount": "24"
  }
}
```

### Podsumowanie Techniczne:
TabelaOfert jest najbardziej "nieprzewidywalnym" źródłem danych pod kątem struktury HTML, dlatego system polega na **hybrydowym pobieraniu** (JSON-LD + selektywny Regex) oraz zewnętrznym geokodowaniu. Scentralizowany `Fetcher` z rate-limitingiem (1.0s) zapewnia stabilność i brak blokad IP.
