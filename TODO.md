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

---

## ✅ Zamknięty: Łączenie deweloperów — model parent_id + UX kart

### Krok D01 — Backend: model parent_id

- [x] `DeveloperManager.merge_developers()` — źródło dostaje `parent_id`, pliki NIE są archiwizowane
- [x] `list_developers()` filtruje `parent_id != null` (dzieci ukryte z głównej listy)
- [x] `get_developer()` fallback: USIdev/ → USIdata/{slug}/ (legacy location)
- [x] `merged_from[]` cache na target dewelopera (portal_mapping, investments_count)
- [x] `events[]` log na target (merge_in, dismiss_suggestion); max 100 wpisów
- [x] `dismiss_suggestion()` — usuwa sugestię i dopisuje zdarzenie

### Krok D02 — API

- [x] `GET /api/developer/<slug>` — enriches `merged_from[]` i `suggestions[]` (name, portal_mapping, investments_count)
- [x] `POST /api/developer/<slug>/merge` — obsługa błędów 422 vs 500
- [x] `POST /api/developer/<slug>/dismiss-suggestion`

### Krok D03 — Frontend: DevMiniCard + optimistic UI

- [x] Komponent `DevMiniCard` — nazwa, slug·ID·liczba inw., sugestia/data, odznaki portali, przyciski w footerze
- [x] `DeveloperSuggestions` — lista kart sugestii z przyciskami "Połącz" + odrzuć
- [x] `MergedMembersPanel` — lista kart połączonych deweloperów z animacją przybycia
- [x] Optimistic update: karta natychmiast przeskakuje do panelu "Połączeni", cofnięcie przy błędzie API
- [x] Animacja CSS `devCardArrive` na karcie w chwili pojawienia się w panelu
- [x] `DevEventsLog` — lista ostatnich zdarzeń (5 widoczne, zwijalne)
- [x] Usunięto `confirm()` — brak popup przy łączeniu
- [x] Naprawa `handleToggleTheme` → `onToggleTheme` (błąd ReferenceError)

### Krok D04 — Testy

- [x] `test_developer_manager.py` — 15 testów pokrywających get, list, merge, dismiss
- [x] `test_merge_source_raw_files_untouched` — weryfikuje byte-for-byte niezmienność raw_*.json

---

## Przyszłe kamienie milowe

