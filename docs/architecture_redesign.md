# USI Tracker: Universal Data Architecture & Migration Plan

## 1. Wizja Architektury
Celem jest odejście od zależności od `Coda.io` oraz `USImaster.csv` na rzecz autonomicznego systemu opartego na zunifikowanych danych JSON. Dropbox staje się jedynie warstwą backupu, a nie interfejsem komunikacyjnym.

### Główne Założenia:
- **Single Source of Truth**: Plik `usi_{source}_{id}.json` jako jedyne źródło danych dla UI i procesów analitycznych.
- **Raw Archiving**: Zachowanie nienaruszonych danych źródłowych (`raw_{source}_{id}.json`) do celów porównawczych i aktualizacji.
- **ID-Only Mandate**: Wszystkie operacje, rezolucja ścieżek i identyfikacja obiektów odbywają się wyłącznie po technicznych identyfikatorach portalowych. Slugi są atrybutem informacyjnym, a nie kluczem tożsamości.

---

## 2. Standard Nazewnictwa Plików (Mandat ID-Only)
Wszystkie pliki w folderze inwestycji (`/Public/USIdata/{dev}/{slug}/`) oraz deweloperów (`/Public/USIdev/{dev-slug}/`) muszą bazować na technicznych identyfikatorach portalowych. Używanie slugów jako kluczy tożsamości jest zabronione.

| Typ Pliku | Format Nazwy | Opis |
| :--- | :--- | :--- |
| **Zunifikowany** | `usi_{source}_{id}.json` | Kluczowe dane w formacie USI (np. `usi_rp_12345.json`). |
| **Deweloper (L2)** | `usi_dev_{source}_{id}.json` | Rekord Level 2 dewelopera (1:1 z plikiem RAW). |
| **Deweloper (Master)** | `dev_master_{DM-ID}.json` | Rekord Level 3 (Master) łączący wiele profili portalowych. |
| **Surowy (Raw)** | `raw_{portal}_{id}.json` | Nienaruszony zrzut danych z portalu. |

---

## 3. Warstwa Transformacji (Adapters & Gateway)
Zamiast rozproszonej logiki parsującej, system wprowadza jawne warstwy:

1. **ScraperGateway**: Centralna brama komunikacyjna z biblioteką `usi-scrapers`. Jedyny punkt styku dla operacji sieciowych.
2. **Adapter (np. `RPAdapter`)**: Czyta `raw_`, tłumaczy specyficzne pola na standard USI, korzystając z deklaratywnych mapowań w `portal_data_mapping.json`.
3. **Merger**: Jeśli inwestycja ma dane z wielu portali, merger łączy je w głównym rekordzie według ustalonych wag.

---

## 4. Zarządzanie Deweloperami (ID-Only)
Deweloperzy posiadają stabilną tożsamość opartą na unikalnych identyfikatorach `usi_dev_id` (format `DEV-NNNNN`) oraz `dm_id` (format `DM-NNNNN`) dla rekordów złączonych.

### Kluczowe Założenia:
- **ID-Only Priority**: Tożsamość, porównywanie i de-duplikacja odbywa się wyłącznie po identyfikatorach technicznych (np. `brand.id` dla TO, `vendor.id` dla RP).
- **Stabilność Resolution**: Wszystkie operacje I/O muszą korzystać z `IdentityResolver`, który wyznacza ścieżki fizyczne na podstawie ID, ignorując zmiany slugów w URL-ach portali.
- **Współdzielone Folder Slugi**: Folder o nazwie slugowej (np. `022-investments`) może zawierać wiele plików `usi_dev_*.json` jeśli różne podmioty portalowe dzielą tę samą nazwę tekstową. System musi obsługiwać listy rekordów dla danego folderu.

---

## 5. Plan Migracji i Utrzymania
Proces utrzymania bazy danych:

1. **Rebuild Index**: Cykliczne odświeżanie indeksu O(1) w pamięci na podstawie skanowania plików JSON (nie nazw folderów).
2. **Clean Portal Mappings**: Usuwanie osieroconych rekordów i naprawa powiązań ID po zmianach w strukturach portali.
3. **Audit Workflow**: Flagowanie rekordów wymagających manualnej weryfikacji przez analityków.

---

## 6. Zmiany w Kodzie (Implementacja ID-Only)
- **Identity Resolver**: Usługa `InvestmentService.get_investment_resources` jako jedyny punkt rezolucji ścieżek.
- **Hot Indexing**: Przechowywanie mapowań ID -> Path w pamięci serwera dla natychmiastowego dostępu.
- **API Blueprints**: Wszystkie endpointy przyjmują `system_id` lub `portal_id` zamiast slugów.
