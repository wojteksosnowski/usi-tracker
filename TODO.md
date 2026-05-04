# TODO

## Bieżący kamień milowy: Zaplecze
Separacja warstw (API / Business Logic / Infrastructure). Celem jest odchudzenie `ui_server.py` i stworzenie modularnej architektury backendowej.

### Krok Z01: Ekstrakcja JobManagera i Infrastruktury
Wydzielenie logiki zarządzania zadaniami do dedykowanego modułu.
- [ ] Stworzenie `python_worker/jobs.py` i przeniesienie tam klasy `JobManager`.
- [ ] Refaktoryzacja `ui_server.py` na użycie zewnętrznego modułu jobs.
- [ ] Przeniesienie generycznych pomocników (np. `log_ui_error`, `get_config`) do `python_worker/api/common.py`.
- [ ] Test: Weryfikacja działania paska postępu w UI po zmianach strukturalnych.

### Krok Z02: Modularne API (Flask Blueprints)
Podział monitu `ui_server.py` na mniejsze, tematyczne kontrolery.
- [ ] Implementacja Blueprinta `/api/investments` (obsługa listy, detali, rejestracji).
- [ ] Implementacja Blueprinta `/api/jobs` (statusy i progres zadań).
- [ ] Implementacja Blueprinta `/api/reports` (generowanie i odczyt raportów).
- [ ] Implementacja Blueprinta `/api/discovery` (skanowanie portali).
- [ ] Test: Pełny audyt endpointów i weryfikacja komunikacji z frontendem.

### Krok Z03: Refaktoryzacja Adapterów (Adapter Package)
Przekształcenie `adapters.py` w nowoczesny pakiet z jasną strukturą.
- [ ] Stworzenie katalogu `python_worker/adapters/` z plikiem `__init__.py`.
- [ ] Implementacja `BaseAdapter` definiującego kontrakt (schema validation).
- [ ] Wydzielenie adapterów `rp.py`, `otodom.py`, `to.py` do osobnych plików.
- [ ] Implementacja automatycznej rejestracji adapterów (Factory Pattern).
- [ ] Test: Weryfikacja unifikacji danych dla każdego z portali przy użyciu nowych adapterów.

### Krok Z04: Separacja logiki biznesowej (Service Layer)
Wydzielenie "mózgu" operacyjnego z kontrolerów Flask do warstwy serwisowej.
- [ ] Stworzenie `python_worker/services/investment_service.py` (logika rejestracji, aktualizacji, unifikacji).
- [ ] Stworzenie `python_worker/services/discovery_service.py` (logika skanowania i filtrowania).
- [ ] Test: Weryfikacja czy kontrolery API are teraz wyłącznie "cienkim" pośrednikiem (routing + walidacja).

---

## Przyszłe kamienie milowe

- **Remanent:** - Stabilizacja i Design System
   * Dynamic CSS Extraction: Komponenty takie jak DesignCanvas wstrzykują style JS-em. Przy tej skali warto przenieść to do dedykowanych plików .css w ui/styles/.
   * SafeRender Pattern: Rozszerz wzorzec safeRender o scentralizowany DataBoundary dla danych z API.

- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.
- **Wikipednia:** — Dodawanie kontekstu do rekordów inwestycji.

---

## Zakończone kamienie milowe

### [DONE] Kamień milowy: Pobieranie (Expert UI & Smart Ingestion)
- **Goal:** Ukończenie migracji do Shell Layout, wprowadzenie asynchronicznych zadań (JobManager), automatyczne mapowanie deweloperów oraz responsywny grid o wysokiej gęstości.
- [x] B01-B11: Shell Layout (ActionBar centralization).
- [x] B12-B13: Async Jobs & UI Interactivity.
- [x] B14-B15: Smart Ingestion & Portal Normalization.
- [x] B16: RP Gallery & Developer Discovery Fix.

### [DONE] Front sklepu: Atomizacja komponentów i "Window Registry"
- [x] C01: Implementacja Registry Helpera (`usiRegister`).
- [x] C02: Atomizacja Core Components (`Icon`, `Spinner`, `DataGrid`).
- [x] C03: Dekompozycja widoku szczegółów (`DetailViewA`, `DetailViewC`).

### [DONE] Improve DataBus Readership
- [x] B01: Centralizacja stanu filtrowania.
- [x] B02: Subskrypcja widoków na DataBus.
- [x] B03: Asynchroniczne akcje w DataBus.
