# Raport: Niezgodności z architekturą ID-only

## 1. Wyciek slugów w `investment_sync.py` i `developer_service.py`
Serwisy synchronizujące w głównym systemie tracker'a nadal przekazują `dev_slug` oraz `inv_slug` jako argumenty wejściowe do metod zewnętrznego API:
* `investment_sync.py`: `scraper_api.download_raw(..., dev_slug, inv_slug)`
* `developer_service.py`: `scraper_api.download_dev_raw(..., dev_slug)` oraz `download_dev_logo`

To drastyczne złamanie architektury ID-only. Metody zewnętrzne nie powinny używać slugów, gdyż tracker wdrożył scentralizowany `IdentityResolver` mapujący unikalne `usi_inv_id` na stabilne ścieżki (nawet jeśli slug ulegnie zmianie u dewelopera). Przekazując slugi, omijamy ten resolver, ryzykując tzw. "path drift".

## 2. Hardkodowane rozwiązywanie ścieżek w `TechnicalDataManager` (usi-scrapers)
Biblioteka `usi-scrapers` w plikach takich jak `manager.py` oraz `utils/io.py` (`get_investment_dir`) opiera generowanie końcowych ścieżek zapisu na otrzymanych slugach.
Biblioteka "zakłada" strukturę `Public/USIdata/{dev_slug}/{inv_slug}`.

## Proponowany kierunek refaktoryzacji
1. Zewnętrzna paczka `usi-scrapers` powinna zostać pozbawiona wiedzy o "slugach" w kontekście zapisywania na dysk.
2. Zamiast `dev_slug` i `inv_slug`, metody API takie jak `process_batch` czy `download_raw` (oraz inicjalizator `TechnicalDataManager`) powinny przyjmować od trackera gotowe ścieżki absolutne: `target_dir: Path` oraz `images_dir: Path`.
3. Jedyną instancją wiedzącą, pod jaką ścieżką fizycznie znajdują się zasoby danej inwestycji, ma pozostać `InvestmentService.get_investment_resources()` (oparty w 100% o systemowy `usi_inv_id`).
