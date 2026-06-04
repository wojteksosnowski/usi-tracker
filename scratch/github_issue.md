W wyniku dogłębnego audytu kodu klienta (`usi-tracker`) oraz paczki bibliotecznej `usi-scrapers`, zidentyfikowano dwa główne problemy architektoniczne, które wymagają natychmiastowej refaktoryzacji, aby zapobiec wyciekom logiki biznesowej i utrzymać zgodność z regułą **ID-only**.

### 1. Rozszerzenie Transformatorów (Naruszenie Thin-Adapters)
Obecnie w repozytorium `usi-tracker` adaptery samodzielnie i "ręcznie" transformują specyficzne pola z surowych danych (np. obróbka dat `delivery_date` polegająca na sklejaniu roku i kwartału, rzutowanie cen czy wyliczanie statusów na bazie `is_rental`). Zgodnie z architekturą, adaptery powinny być jak najlżejsze (wyłącznie kompletować ustrukturyzowany słownik na podstawie pre-transformowanych surowych pól).

**Wymagane kroki:**
* Dodanie nowych funkcji w `transformers.py` pod konkretne typy danych, by `portal_data_mapping.json` automatycznie je czyścił.

### 2. Ścisłe ID-only w TechnicalDataManager i API (Naruszenie Path-Drift)
Funkcje takie jak `api.download_raw` czy `api.process_batch` zmuszają klienta do przekazywania `dev_slug` i `inv_slug`. Następnie biblioteka samodzielnie skleja z nich docelową strukturę katalogów (np. `Public/USIdata/...`). To drastycznie łamie wzorzec **ID-only** i system *IdentityResolver*, który został zaimplementowany po stronie trackera (tylko resolver wie, gdzie naprawdę leży inwestycja dla danego `usi_inv_id`).

**Wymagane kroki:**
* Całkowite pozbycie się logiki sklejania ścieżek z użyciem slugów w `utils/io.py` i `manager.py`.
* Zamiast `dev_slug` i `inv_slug`, metody API oraz klasa `TechnicalDataManager` powinny przyjmować od trackera instancje `pathlib.Path` np. `target_dir` i `images_dir` lub działać w trybie callbacku.
