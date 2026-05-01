# USI Tracker: Universal Data Architecture & Migration Plan

## 1. Wizja Architektury
Celem jest odejście od zależności od `Coda.io` oraz `USImaster.csv` na rzecz autonomicznego systemu opartego na zunifikowanych danych JSON. Dropbox staje się jedynie warstwą backupu, a nie interfejsem komunikacyjnym.

### Główne Założenia:
- **Single Source of Truth**: Plik `usi_{slug}.json` jako jedyne źródło danych dla UI i procesów analitycznych.
- **Raw Archiving**: Zachowanie nienaruszonych danych źródłowych do celów porównawczych i aktualizacji.
- **Translation Layer**: Dedukowane adaptery dla każdego dostawcy (RynekPierwotny, Otodom, TabelaOfert).

---

## 2. Standard Nazewnictwa Plików
Wszystkie pliki w folderze inwestycji (`/Public/USIdata/{dev}/{slug}/`) muszą zawierać slug w nazwie i posiadać jasny prefix określający ich rolę.

| Typ Pliku | Format Nazwy | Opis |
| :--- | :--- | :--- |
| **Zunifikowany** | `usi_{slug}.json` | Kluczowe dane w ustandaryzowanym formacie USI. |
| **Deweloper** | `usi_dev_{dev-slug}.json` | Stabilne dane dewelopera (nazwa, NIP, portal_ids). |
| **Surowy (Aktualny)** | `raw_{portal}_{slug}.json` | Ostatnio pobrany, pełny zrzut danych z portalu. |
| **Surowy (Archiwum)** | `raw_{portal}_{slug}_{YYYYMMDD}.json` | Historyczne kopie danych do porównań. |
| **Metadane** | `meta_{slug}_{type}.json` | Dodatkowe informacje (oceny, etapy, logi). |

---

## 3. Warstwa Transformacji (Adapters)
Zamiast rozproszonej logiki parsującej, system wprowadza jawne adaptery:

1. **Scraper**: Pobiera dane i zapisuje plik `raw_`.
2. **Adapter (np. `RPToUSI`)**: Czyta `raw_`, tłumaczy specyficzne pola (np. `geo_point` -> `coords`, `facilities` -> `amenities`) na standard USI.
3. **Merger**: Jeśli inwestycja ma dane z wielu portali, merger łączy je w jednym pliku `usi_{slug}.json` według ustalonych wag (np. RP ma priorytet dla danych technicznych, Otodom dla opisów).

---

## 4. Zarządzanie Deweloperami (Podmioty)
Deweloperzy muszą posiadać stabilną tożsamość niezależną od kaprysów portali.

### Słownik Mapujący (Konkurenci.csv):
Plik `reference-data/coda/Konkurenci.csv` stanowi **Master Dictionary** dla całego systemu. Zawiera on ręcznie zweryfikowane mapowania między stabilnym `usiFolder` (nasz `developer_slug`) a identyfikatorami portalowymi.

### Kluczowe Założenia:
- **Inicjalizacja**: Baza deweloperów jest seedowana z `Konkurenci.csv` przed migracją inwestycji.
- **Stabilny Developer Slug**: Raz nadany slug (np. `dom-development`) pozostaje niezmienny.
- **Portal ID & Discovery**: Plik `usi_dev_{slug}.json` zawiera dane wyciągnięte z `Konkurenci.csv`:
  - `rp_id` i `rp_slug` (z kolumn `rpID`, `rpSlug`)
  - `oto_agency_ids` (wyciągnięte z kolumny `otoID`, np. `ID8495786` -> `8495786`)
  - `to_dev_slug` (do uzupełnienia)
- **Developer Scan Workflow**: System wykorzystuje te ID do automatycznego odpytywania API portali w poszukiwaniu nowych inwestycji.

### Lokalizacja Pliku:
Folder nadrzędny inwestycji: `/Public/USIdata/{dev-slug}/usi_dev_{dev-slug}.json`.

---

## 5. Plan Migracji z USImaster.csv & Konkurenci.csv
Proces wyodrębnienia danych:

1. **Inicjalizacja Deweloperów**: Uruchomienie `python3 -m python_worker.init_developers` w celu utworzenia bazy `usi_dev_{slug}.json` na podstawie `Konkurenci.csv`.
2. **Detekcja Sluga Inwestycji**: Mapowanie inwestycji do folderów deweloperów przy użyciu ID zawartych w nowej bazie deweloperów.
3. **Ekstrakcja Raw**: Przeniesienie `rpJSON` i `otoJSON` z `USImaster.csv` do plików `raw_`.
4. **Adaptery & Unifikacja**: Utworzenie plików `usi_{slug}.json`.

---

## 6. Zmiany w Kodzie (Do Wykonania)
- **UI Server**: Usunięcie funkcji `_normalize_investment`. UI serwuje `usi_{slug}.json`. Dodanie widoku profilu dewelopera.
- **Main CLI**: Nowe komendy:
  - `python -m python_worker.main update-dev {dev-slug}` (skanuje portale w poszukiwaniu nowych inwestycji dewelopera).
  - `python -m python_worker.main update {slug}` (aktualizuje konkretną inwestycję).
- **Developer Resolver**: Moduł mapujący portalowe ID na stabilne foldery deweloperów podczas scrapingu.
