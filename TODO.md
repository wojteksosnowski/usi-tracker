# TODO

## Bieżący kamień milowy: Wydzielnie usi-scrapers

To jest trudny kamień milowy składający się z planowania, działania i rozległych testów.

Wydziel scraper/Fetcher/adaptery (RP/OTO/TO + helpery do pobierania obrazów) do osobnego, wersjonowanego pakietu Python (np. github.com/yourorg/usi-scrapers). Zachowaj w nim jasno zdefiniowane, małe API (funkcje/klasy do: listowania inwestycji, pobrania pojedynczej inwestycji, opcjonalnie zapis/zwrot surowego JSONu i obrazów). W głównym repo zostaw jedynie lekki „shim” który importuje ten pakiet i wywołuje jego API. To daje wersjonowanie, niezależne CI i minimalizuje przypadkowe modyfikacje scraperów przez LLM/PR.

Przygotowane puste repo: https://github.com/wojteksosnowski/usi-scrapers

Przygotowany folder: /Volumes/Samsam/claude-py/usi-scrapers

### Krok B01: Inicjalizacja repozytorium usi-scrapers
Skonfiguruj nowe repozytorium na podstawie przygotowanego folderu.
- [ ] Przejdź do `/Volumes/Samsam/claude-py/usi-scrapers`
- [ ] Zainicjuj plik `pyproject.toml` z podstawowymi zależnościami (np. curl_cffi)
- [ ] Stwórz docelową strukturę pakietu: katalogi `usi_scrapers/`, `tests/`
- [ ] Utwórz publiczny interfejs pakietu w pliku `api.py`
- [ ] Zaktualizuj i wyślij pierwsze zmiany do repozytorium na GitHubie

### Krok B02: Ekstrakcja warstwy pobierania (Fetcher)
- [ ] Przenieś logikę sieciową (`fetcher.py` i związane z nim mechanizmy jak `fetch_html`/`fetch_json`)
- [ ] Przenieś pomocnicze skrypty obrazkowe (pobieranie/serializacja zdjęć)
- [ ] Przetestuj działanie warstwy sieciowej (Rate Limiting) w nowym, izolowanym środowisku

### Krok B03: Ekstrakcja Scraperów i Adapterów
- [ ] Migracja logiki scraperów z plików `scraper_rp.py`, `scraper_oto.py`, `scraper_to.py` do nowego pakietu
- [ ] Przeniesienie całego katalogu i logiki z `python_worker/adapters/` do `usi_scrapers/adapters/`
- [ ] Skopiowanie niezbędnych schematów (`schemas/raw_*`) używanych do walidacji danych (np. przez Pydantic)
- [ ] Utrzymanie w głównym repozytorium `developer_manager.py` (jako konsument pakietu do zapisu na Dropbox)

### Krok B04: Definicja API, Typów i Testów (Kontrakt)
Zabezpieczenie logiki przed przypadkowymi modyfikacjami.
- [ ] Opracowanie funkcji publicznego API: listowanie, pobranie inwestycji i standaryzacja surowego JSONu
- [ ] Zastosowanie rygorystycznych type hints (ABC/Protocol) określających wejścia i wyjścia
- [ ] Migracja danych z `reference-data/` i zaimplementowanie testów typu snapshot
- [ ] Przygotowanie dokumentacji technicznej punktów integracji w pliku `README.md`

### Krok B05: Integracja pakietu w usi-tracker ("Shim")
- [ ] Podpięcie wyizolowanego pakietu `usi-scrapers` jako zewnętrznej instalacji wewnątrz `usi-tracker`
- [ ] Aktualizacja procesów `CLI`, `Merger` i `python_worker` aby korzystały ze scentralizowanego API z `usi-scrapers`
- [ ] Weryfikacja e2e (komendy `discover`, `update-inv`) bez zmian w logice przechowywania lokalnego i Dropbox
- [ ] Sprzątnięcie usuniętych plików wewnątrz macierzystego projektu

## Następny kamień milowy: Czyszczenie artefaktów kodu

- W kodzie plączą się `<path d="M22.85` to są pewnie pozostałości. Nalezy sprawdzić czy to nie są nasze usi-star- i usi-zero-. Jezeli `<path d="M22.85` nie nalezy do usi-star- lub usi-zero- uwzpolnic z innymi odwołaniami do usi-star-

## Przyszłe kamienie milowe

- `<div className="usi-pill outline usi-mono usi-tiny" style={{borderColor: 'var(--usi-accent)', color: 'var(--usi-accent)' }}>` wciaz jest przykladem inline style. czy nie mozna zrealizowac tego inaczej jezeli nie - nalezy pozostawic.