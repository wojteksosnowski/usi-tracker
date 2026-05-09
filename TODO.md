# TODO

## ✅ Zamknięty: Naprawa przycisku Odśwież i stabilizacja
## ✅ Zamknięty: MiniMap — dynamiczne proporcje i dark mode
## ✅ Zamknięty: UI — Naprawki Inwestycji, Deweloperów i Powiadomień
## ✅ Zamknięty: Strona Pobieranie — UX i bulk download
## ✅ Zamknięty: MiniMapa — retina, styl wektorowy, pinezka HERE

---

## ✅ Zamknięty: Widok C — pasek kategorii + naprawa migotania listy

### Krok C01 — Kompaktowy pasek kategorii w dolnej belce ModeC

- [x] Pasek kategorii stały (zawsze widoczny): 6 chipów — kolorowa kropka + skrót (BAL/FAS/…) + wartość (`—` jeśli brak)
- [x] Klik w chip ustawia `focusedCat` i otwiera RatingsPanel
- [x] Strzałka toggle otwiera/zamyka RatingsPanel (`max-height: 320px`, scroll)

### Krok C02 — Naprawa migotania listy przy scrollowaniu

- [x] Tryb `table`: wirtualizacja wyłączona — wszystkie wiersze renderowane bezpośrednio (brak `setScrollTop` na scroll)
- [x] Tryb `grid`: wirtualizacja zachowana, scroll throttled przez `requestAnimationFrame`

---

## ✅ Zamknięty: POI widget — punkty zainteresowania w okolicy inwestycji

### Krok P01 — Backend
- [x] Endpoint `GET /api/poi/<dev_slug>/<inv_slug>` — odczyt `poi_<inv_slug>.json`
- [x] Endpoint `POST /api/poi/<dev_slug>/<inv_slug>/fetch` — HERE Places + Wikimedia
- [x] HERE Places Browse API (radius 2000m): 7 kategorii (food/entertainment/outdoor/transport/shopping/education/health)
- [x] Wikimedia geosearch PL (radius 2000m), artykuły posortowane po odległości

### Krok P02 — Frontend
- [x] `PoiModule` w `modules-ui.jsx`: lista pogrupowana po kategorii, ikony, odległość
- [x] Sekcja Wikipedia z klikalnymi linkami
- [x] Stan "idle" → przycisk "Pobierz POI"; auto-load przy otwarciu

---

## ✅ Zamknięty: Developer Crawler — automatyczny discovery w tle

- [x] `crawler.py` — daemon thread, crawl spread over 2 tygodnie, revisit co 30±5 dni
- [x] Gap 10-20 min między wizytami; startup stagger 30-120s
- [x] Stan `crawler` w `usi_dev_*.json`: `last_visit`, `next_visit`, `new_since_review`
- [x] API: `GET /api/crawler/status`, `POST /api/crawler/pause/resume`
- [x] Badge "+N nowe" na karcie dewelopera; reset przy otwarciu widoku dewelopera

---

## Przyszłe kamienie milowe

### Widok listy — migotanie przy scrollowaniu
- (przeniesione do bieżącego kamienia C02)
