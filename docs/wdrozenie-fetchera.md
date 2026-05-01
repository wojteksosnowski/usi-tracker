# Plan wdrożenia lekkiego silnika fetchowania (curl_cffi)

## Cel
Zapewnienie stabilnego mechanizmu omijania blokad Cloudflare (np. na TabelaOfert.pl) bez zasobożernego Playwrighta i bez otwierania okien przeglądarki. Wykorzystamy `curl_cffi` (impersonate), który udaje sygnatury TLS i nagłówki prawdziwych przeglądarek na poziomie binarnym.

## Architektura (Modularność)
Zgodnie z zasadą modularności `usi-tracker`, wprowadzamy centralny moduł `python_worker/fetcher.py`. Żaden scraper nie powinien bezpośrednio używać `requests` ani `curl_cffi`. Wszystkie wywołania sieciowe przechodzą przez inteligentny dispatcher.

## Kroki wdrożenia

### 1. Nowy moduł: `python_worker/fetcher.py`
Stworzenie klasy `Fetcher`, która zarządza strategiami pobierania:
- **Strategia "Impersonate"**: Domyślna, używa `curl_cffi` z parametrem `impersonate="chrome"`.
- **Strategia "Direct"**: Standardowe `requests` dla zaufanych API (np. RynekPierwotny).
- **Strategia "Proxy"**: Wykorzystanie ScraperAPI jako ostateczny fallback.

### 2. Refaktoryzacja Scraperów
Aktualizacja istniejących scraperów do korzystania z `fetcher.py`:
- `scraper_to.py`: Zmiana `fetch_to_html` na `Fetcher().fetch(url)`.
- `scraper_otodom.py`: Zmiana logiki pobierania `__NEXT_DATA__`.
- `scraper_rp.py`: (Opcjonalnie) Użycie `fetcher.py` dla zachowania spójności.

### 3. Konfiguracja i Sekrety
- Przeniesienie klucza `SCRAPERAPI_KEY` do centralnego managera w `fetcher.py`.
- Dodanie flagi `FETCH_STRATEGY` do `.env` pozwalającej wymusić konkretny silnik (np. do debugowania).

### 4. Weryfikacja
- Test na profilu ATAL (TabelaOfert), który wcześniej zwracał 403.
- Test regresyjny dla RynekPierwotny (czy nowe nagłówki nie psują API).

## Zalety rozwiązania
- **Lekkość**: Zużycie zasobów na poziomie biblioteki `requests`.
- **Niewidzialność**: Brak wyskakujących okien (headless by design).
- **Stabilność**: Wysoka skuteczność przeciwko Cloudflare (WAF/JA3 fingerprinting).
