# Raport z Audytu: Zależności usi-tracker a usi-scrapers

## 1. python_worker/adapters/__init__.py
Warstwa adapterów łamie zasadę Thin-Adapters (określoną w założeniach architektonicznych). Adaptery w wielu miejscach samodzielnie transformują dane i sterują logiką biznesową na podstawie surowych odpowiedzi z portali.
* **Linie 78-94** (`RPAdapter._from_result`): Ręczne rozdzielanie logiki w zależności od `is_rental` oraz wpisywanie stałych kluczy finansowych zamiast polegania na ustandaryzowanym słowniku zwracanym z biblioteki.
* **Linie 176-208** (`OtodomAdapter._from_result`): Składanie formatowania dat w stylu: `f"{dy}-Q{dq}" if dy and dq else None`, a także jawne rzutowanie zmiennych na `float(price)`. Tego typu przekształcenia powinny być zaimplementowane jako funkcja w `transformers.py` (np. przez `@register_transformer("oto_delivery_date")`).
* **Linie 230-246** (`OtodomAdapter._from_raw`): Powielanie bloków try-except podczas obróbki cen i metraży.

## 2. python_worker/services/investment_sync.py
Plik samodzielnie zarządza ścieżkami oraz plikami, nie delegując operacji do specjalistycznej klasy `TechnicalDataManager` oferowanej przez `usi-scrapers`.
* **Linie 171-178**: Samodzielne budowanie struktury plików `f"usi_{portal}_{item_id}.json"` oraz ścieżek dostępu. Złamanie delegacji I/O.
* **Linie 255, 494, 716**: Skrypty używają bezpośredniego wbudowanego skanowania dysku `inv_dir.glob(f"raw_{raw_prefix}_*.json")` i `inv_dir.glob(f"meta_{p}_*.json")`. Wszelkie zapytania o pliki z surowymi logami z poszczególnych API (stanowiącymi zasoby techniczne), powinny być ujednolicone w ramach biblioteki.

## Wnioski i Rekomendacje
Lokalne pliki należy zrefaktoryzować, a część logiki związanej ze standaryzacją danych przekazać do paczki zewnętrznej jako poprawki pod nowe transformatory i rozszerzenia w silniku mapującym.
