# Konfiguracja

## Zmienne środowiskowe (.env)

System wymaga pliku `.env` umieszczonego w katalogu `python_worker/`. Przykładowa zawartość:

```env
# Klucz do ScraperAPI (wymagany dla Otodom i stron deweloperów)
SCRAPERAPI_KEY=twoj_klucz

# Klucz HERE Maps API (wymagany dla miniatur map satelitarnych)
HERE_API_KEY=twoj_klucz

# Ścieżka do głównego katalogu projektu (root)
DROPBOX_PATH=/Volumes/Samsam/claude-py/usi-tracker
```

## Faza testów

W fazie testów katalogiem opracyjnym jest /Volumes/Samsam/claude-py/usi-tracker/Public

W tym katalogu znajduja się katalogi

- USI - zawierajacy pobrane do tej pory ze stron pliki graficzne do testów przez usi-tracker
- USIdata - zawierajacy pliki JSON z informacjami pobranymi z bazy danych coda.io z tabeli USImaster

## Faza wdrozenie

W fazie wdrozenia katalogiem opercjnym jest /Users/ws/Library/CloudStorage/Dropbox/Public

W tym katalogu znajduja się katalogi

- USI - zawierajacy pobrane do tej pory ze stron pliki graficzne
- USIdata - zawierajacy pliki JSON z informacjami pobranymi z bazy danych coda.io z tabeli USImaster przy pomocy przycisku "dumpJSONtoDB"