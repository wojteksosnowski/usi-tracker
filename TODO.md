# TODO

## Bieżący kamień milowy: Remanent
Stabilizacja i Design System. Cel: Wydzielenie stylów CSS i wzmocnienie odporności renderowania.

### Krok B01: Ekstrakcja stylów z JS
Przeniesienie wstrzykiwanych stylów (DesignCanvas, etc.) do plików `.css`.
**Plan:** 2026-05-06

### Krok B02: DataBoundary & SafeRender
Wdrożenie scentralizowanego DataBoundary dla ochrony komponentów przed błędami danych z API.
**Plan:** 2026-05-06

---

## Przyszłe kamienie milowe

- **Raspbery:** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi).
- **Crawler:** — Powolne zaciąganie inwestycji w tle.
- **Wikipednia:** — Dodawanie kontekstu do rekordów inwestycji.

---

## Zakończone kamienie milowe

### [DONE] Kamień milowy: Zaplecze
- [x] Z01: Ekstrakcja JobManagera i Infrastruktury.
- [x] Z02: Modularne API (Flask Blueprints).
- [x] Z03: Refaktoryzacja Adapterów (Adapter Package).
- [x] Z04: Separacja logiki biznesowej (Service Layer).

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
