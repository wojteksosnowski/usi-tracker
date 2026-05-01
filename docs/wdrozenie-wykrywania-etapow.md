# Wykrywanie etapów RP i powiązań między portalami

## Problem

Inwestycje wieloetapowe w RynekPierwotny są zgrupowane przez `groups.id`, ale każdy etap
ma osobne `offer.id` (klucz API) i `stage.id` (klucz URL `?stage=`). Worker dotychczas
traktował każdy etap jak niezwiązaną inwestycję. Dodatkowo ta sama inwestycja może
istnieć równocześnie w RP, Otodom i TabelaOfert — bez automatycznego powiązania.

---

## Część 1: Etapy RynekPierwotny

### Struktura danych

```json
"groups": {
  "id": 587,
  "name": "Boska Ksawerowska 2",
  "stages": [
    {
      "id": 1582,                          ← używany w URL ?stage=1582
      "name": "Etap 1",
      "current": false,
      "primary": true,
      "sort": 1,
      "offer": {
        "id": 19011,                       ← klucz API /offer/19011/
        "slug": "boska-ksawerowska-2-pabianicki-ksawerow",
        "vendor": { "slug": "novisa-development-sp-z-oo-sp-j" }
      }
    }
  ]
}
```

URL etapu: `https://rynekpierwotny.pl/oferty/{vendor.slug}/{offer.slug}-{offer.id}/?show_sold_stage=true&stage={stage.id}`

### Nowe pola w `app_result_*.json`

| Pole | Opis |
|---|---|
| `groups_id` | Wspólny ID grupy etapów (null = jednoetapowa) |
| `groups_name` | Nazwa nadrzędna bez numeru etapu |
| `stage_sort` | Kolejność etapu (1, 2, 3…) |
| `stage_is_current` | bool: aktywny etap |
| `sibling_stages` | Lista wszystkich etapów z polami: `stage_id, offer_id, slug, name, sort, current, primary, url` |
| `sibling_stage_folders` | Ścieżki `{dev}/{inv}` do folderów pozostałych etapów |

### Moduł `stage_detector.py`

| Funkcja | Opis |
|---|---|
| `extract_stages(rp_details)` | Zwraca listę rekordów etapów z `groups.stages` |
| `extract_groups_id(rp_details)` | Zwraca `groups.id` lub None |
| `is_multistage(rp_details)` | True jeśli inwestycja ma etapy |
| `build_stage_url(vendor_slug, offer_slug, offer_id, stage_id)` | Buduje URL z `?show_sold_stage=true&stage=` |
| `run_stage_detection(data_dir)` | Skanuje USIdata, aktualizuje app_result, tworzy stuby |

### Komenda: `detect-stages`

```bash
python3 -m python_worker.main detect-stages
```

Dla każdej inwestycji RP z danymi `groups`:
1. Dodaje pola etapów do istniejącego `app_result_*.json`
2. Tworzy `usi_stage_stub.json` w folderze każdego brakującego etapu — minimal metadata,
   status `"stub"`, gotowy do pełnego scrapu komendą `main <url>`

---

## Część 2: Powiązania między portalami

### Algorytm dopasowania

| Sygnał | Metoda | Tolerancja |
|---|---|---|
| Współrzędne | Haversine | ≤ 150 m |
| Deweloper | `developer_slug` lub SequenceMatcher | ≥ 0.9 |
| Nazwa (bez etapu) | `normalize_name()` + SequenceMatcher | ≥ 0.82 |
| Liczba lokali | `abs(rp - oto) / rp` | ≤ 30% |
| Termin oddania | `construction_date_upper` vs `delivery_quarter/year` | ≤ 2 kwartały |

**Ważne:** jeśli obie inwestycje mają współrzędne ale są > 150 m od siebie,
sugestia `low` jest odrzucana mimo pasującego dewelopera i nazwy.

### Poziomy pewności

| Poziom | Warunki |
|---|---|
| `exact` | coords ≤ 50 m + ten sam deweloper |
| `high` | coords ≤ 150 m + deweloper + podobna nazwa |
| `medium` | coords ≤ 150 m + deweloper |
| `low` | deweloper + podobna nazwa (brak sprzecznych coords) |

Różnica terminu > 2 kwartały obniża `exact` → `high`, `high` → `medium`.

### Moduł `portal_matcher.py`

| Funkcja | Opis |
|---|---|
| `find_matches(results)` | Core — zwraca listę `MatchSuggestion` |
| `load_all_app_results(data_dir)` | Skanuje wszystkie `app_result_*.json` |
| `normalize_name(name)` | Usuwa "etap N/I/II/III", "faza N", normalizuje do ASCII |
| `haversine_m(lat1, lon1, lat2, lon2)` | Odległość w metrach |
| `run_matcher(data_dir, output_path, min_confidence)` | Entry point dla CLI |

### Komenda: `match-portals`

```bash
python3 -m python_worker.main match-portals
python3 -m python_worker.main match-portals --min-confidence high
```

Wynik: `Public/USIdata/usi_match_suggestions.json`

```json
[
  {
    "rp_folder": "invest-komfort/nowe-kolibki-etap-4-gdynia-orlowo",
    "other_portal": "otodom",
    "other_folder": "otodom/nowe-kolibki-IDXXX",
    "confidence": "high",
    "signals": ["coords_38m", "same_dev", "name_0.94", "delivery_q4_2027"],
    "rp_name": "Nowe Kolibki etap 4",
    "other_name": "Nowe Kolibki",
    "distance_m": 38.2
  }
]
```

Sugestie przeglądane w interfejsie webowym — endpoint `/match-review` (faza następna).

---

## Zmodyfikowane pliki

| Plik | Zmiana |
|---|---|
| `scraper_rp.py` | Dodaje `groups_id`, `sibling_stages`, `sibling_stage_folders` do wyniku |
| `csv_importer.py` | `build_rp_result()` wywołuje `extract_stages()` |
| `url_parser.py` | Parsuje `?stage=` i `?show_sold_stage=` |
| `main.py` | Dodane case `detect-stages` i `match-portals` |

## Nowe pliki

```
python_worker/stage_detector.py
python_worker/portal_matcher.py
python_worker/test_stage_detector.py    (14 testów)
python_worker/test_portal_matcher.py    (23 testy)
```

## Testy

```bash
pytest python_worker/test_stage_detector.py python_worker/test_portal_matcher.py -v
```
