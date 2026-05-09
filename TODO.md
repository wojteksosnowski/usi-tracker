# TODO

## ✅ Zamknięty kamień milowy: Naprawa przycisku Odśwież i stabilizacja
## ✅ Zamknięty kamień milowy: MiniMap — dynamiczne proporcje i dark mode

---

## ✅ Zamknięty kamień milowy: UI — Naprawki Inwestycji, Deweloperów i Powiadomień

---

## ✅ Zamknięty kamień milowy: Strona Pobieranie — UX i bulk download

---

## ✅ Zamknięty kamień milowy: MiniMapa — jakość i rozdzielczość

### Krok M01 — Retina / 2× rozdzielczość

- [x] `_buildHereUrl` mnoży CSS pixels przez `devicePixelRatio` (max 2×), ogranicza do 2048px
- [x] CSS `width/height: 100%` + `object-fit: cover` — przeglądarka skaluje w dół automatycznie

### Krok M02 — Styl mapowy (nie satelita)

- [x] Zmieniono z `explore.satellite.day/night` na `explore.day` / `explore.night` (wektorowy styl HERE)

### Krok M03 — Weryfikacja

- [ ] Otworzyć widok szczegółów i sprawdzić ostrość mapy na ekranie Retina
- [ ] Zweryfikować dark mode — mapa nocna vs dzienna
- [x] Pinezka: HERE v3 API nie obsługuje stylowania przez query params; nakładamy własny SVG marker (różowy teardrop z białym kółkiem) przez `position:absolute; left:50%; top:50%; transform:translate(-50%,-100%)` — mapa zawsze wycentrowana na punkcie

### Krok D01 — Feedback i usunięcie karty po pobraniu

- [x] Po udanym `/api/register` karta natychmiast znika z listy (`filter` zamiast `map(registered: true)`)
- [x] Spinner na przycisku podczas HTTP request (był już, teraz + karta znika po sukcesie)

### Krok D02 — Przycisk "Pobierz wszystkie nowe"

- [x] Pasek `usi-download-bulk-bar` pojawia się gdy są nowe inwestycje — liczba + przycisk "Pobierz wszystkie nowe (N)"
- [x] `handleRegisterAll` iteruje po `visibleResults.filter(is_new)` i rejestruje sekwencyjnie; błędy pojedynczych nie przerywają batcha

### Krok I01 — Widok listy inwestycji: miniaturki i scrollowanie

- [x] Naprawić CSS `list-table-thumb` — brakuje constraintu rozmiaru; miniaturki w `rowHeight=56` wypełniają całą komórkę
- [ ] Zbadać i naprawić migotanie listy przy scrollowaniu (DataGrid wirtualizowany — podejrzenie o race condition `setScrollTop` vs ResizeObserver)

### Krok I02 — Nawigacja klawiaturą w widoku inwestycji

- [x] Strzałki ← → przełączają inwestycję (poprzednia/następna z `visibleInvestments`) — `useEffect` w `app.jsx`
- [x] `[` i `]` przełączają zdjęcia w galerii — `SlideShow` i `Lightbox` zmienione z ArrowLeft/ArrowRight na `[`/`]`

### Krok I03 — Naprawki Strony Deweloperzy

- [x] Przycisk "Powrót" z widoku detail inwestycji wraca do poprzedniego widoku — `prevView` state w `app.jsx`
- [x] Filtr "Aktywni" w widoku deweloperów — backend dodaje `last_updated` (mtime usi_*.json); frontend filtruje po 12 miesiącach

### Krok I04 — Obszar powiadomień

- [x] `StatusMessenger` — styl monospace tekst, bez pill/badge
- [x] `NotificationConsole` — klawisz `§` toggle; wysuwa się zza górnego brzegu (CSS `transform: translateY`)
- [x] `NotificationCenter` w navbarze — wyświetla `> NAME: message [%]` w monosopace; ukryty gdy brak aktywnych jobów

---

## Przyszłe kamienie milowe

### Strona Pobieranie
- przycisk "pobierz nowe" — pobiera wszystkie zeskanowane nowe inwestycje (batch job)
- przycisk "pobierz" na karcie — brak feedbacku (dodać spinner/job polling)
- pobranie zeskanowanej inwestycji usuwa ją z listy zeskanowanych natychmiast po sukcesie


### Punkty zainteresowania (nowy moduł widget)
- na podstawie lokalizacji zbiera POI z HERE Maps w okolicy 2 km
- na podstawie lokalizacji zbiera POI z Wikipedii w okolicy 2 km
- zakres: kultura, edukacja, rekreacja
- zapisuje listę (nazwa, opis, geopoint, link) do JSON w folderze inwestycji

### Strona Deweloperzy — crawler w tle
- crawler z random delay przeglądający podstrony deweloperów pod kątem nowych inwestycji
- log ostatniej wizyty + konfigurowalny cooldown (default 1 miesiąc)

### Widok C — lista kategorii z ocenami w pasku na dole
