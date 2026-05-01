# Wdrożenie interfejsu przeglądania bazy USI

Punkt 6 z `do-zrobienia.md`: lokalny interfejs webowy do przeglądania zgromadzonych danych i zdjęć inwestycji deweloperskich.

---

## A. Opis interfejsu i stack technologiczny

### Założenia

- Narzędzie pracy dla jednego użytkownika, uruchamiane lokalnie na macOS
- Czyta dane z istniejącej struktury `DROPBOX_PATH/Public/USI/` i `DROPBOX_PATH/Public/USIdata/`
- **Nie modyfikuje** żadnych istniejących plików (`app_result_*.json`, `rp_details.json`, `oto_details.json`, `coda_request_*.json`) — interoperacyjność z Coda.io zachowana
- Własne pliki workera zapisywane w `USIdata/` z unikalnym prefiksem `usi_` i `deletion_`

### Stack

| Warstwa | Technologia | Uzasadnienie |
|---|---|---|
| Serwer | Flask 3.x + Jinja2 | Pasuje do istniejącego stosu Python; brak npm/build step |
| Frontend | Vanilla JS (ES6 modules) | Zero bundlera; działa bezpośrednio w przeglądarce |
| UI Components | Material Web (`@material/web`) via CDN | Material Design 3; ładowany przez importmap, bez instalacji |
| Fonty/ikony | Google Fonts (Roboto) + Material Icons Round | CDN; standardowy M3 |

### Nowy moduł: `python_worker/ui_server.py`

Endpointy Flask:

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/` | Lista wszystkich inwestycji (skan `USIdata/`) |
| `GET` | `/investment/<dev_slug>/<inv_slug>` | Widok inwestycji: galeria + formularz ocen |
| `GET` | `/api/image/<dev_slug>/<inv_slug>/<filename>` | Serwuje plik JPG z `Public/USI/` |
| `GET` | `/api/data/<dev_slug>/<inv_slug>` | JSON z metadanymi inwestycji + ocenami USI |
| `POST` | `/api/ratings/<dev_slug>/<inv_slug>` | Zapisuje `usi_ratings.json` |
| `POST` | `/api/mark-delete/<dev_slug>/<inv_slug>` | Zapisuje `deletion_list.json` |

### Uruchomienie

```bash
# Przez główny CLI
python3 -m python_worker.main ui

# Bezpośrednio
python3 -m python_worker.ui_server

# Domyślny port
open http://localhost:5000
```

### Nowe pliki JSON (tylko worker, Coda ich nie czyta ani nie modyfikuje)

**`Public/USIdata/{dev}/{inv}/usi_ratings.json`** — oceny USI:
```json
{
  "Balkony": 2,
  "Fasady": 3,
  "Wnętrza": 1,
  "Teren": 4,
  "Mieszkania": 2,
  "Udogodnienia": 1,
  "komentarz": "Dobra lokalizacja, słabe balkony",
  "updated_at": "2026-04-26T10:00:00"
}
```

**`Public/USIdata/{dev}/{inv}/deletion_list.json`** — lista zdjęć do usunięcia:
```json
{
  "paths": [
    "/Public/USI/dev-slug/inv-slug/image_001.jpg",
    "/Public/USI/dev-slug/inv-slug/image_003.jpg"
  ],
  "updated_at": "2026-04-26T10:05:00"
}
```

---

## B. Struktura widoków

### Widok 1: Lista inwestycji (`/`)

**Layout**: siatka kart `md-elevated-card`, 3–4 kolumny w zależności od szerokości ekranu.

**Każda karta zawiera**:
- Thumbnail pierwszego zdjęcia z `Public/USI/` (lub placeholder jeśli brak)
- Nazwa inwestycji (`md-typescale-headline-small`)
- Deweloper (`md-typescale-title-medium`, muted)
- Źródło: badge `RP` lub `OTO` lub `TO`
- Mini-pasek 6 kategorii USI: kolorowe kółka jeśli ocena zapisana (wypełnione = ocenione, puste = nie)
- Badge z liczbą zdjęć do usunięcia (czerwony, jeśli `deletion_list.json` istnieje)

**Filtry i sortowanie** (pasek nad siatką):
- `<md-filled-select>` — filtr dewelopera
- `<md-filled-select>` — filtr statusu: Wszystkie / Ocenione / Nieocenione
- `<md-filled-select>` — sortowanie: Nazwa A–Z / Deweloper / Liczba zdjęć / Ostatnio dodane

**Klawiatura**:
- `↑↓←→` — poruszanie po kartach
- `Enter` — otwiera zaznaczoną inwestycję

### Widok 2: Inwestycja (`/investment/<dev>/<inv>`)

**Layout dwukolumnowy**:
- **Lewa kolumna (30%)**: panel ocen USI
- **Prawa kolumna (70%)**: galeria zdjęć

#### Lewa kolumna — Panel ocen USI

Nagłówek: nazwa inwestycji + deweloper + link do źródła (RP/Otodom).

Formularz 6 kategorii:
```
Balkony      [0] [1] [2] [3] [4]
Fasady       [0] [1] [2] [3] [4]
Wnętrza      [0] [1] [2] [3] [4]
Teren        [0] [1] [2] [3] [4]
Mieszkania   [0] [1] [2] [3] [4]
Udogodnienia [0] [1] [2] [3] [4]
```

Każda linia: `<md-filter-chip>` (pojedynczy wybór per wiersz).
- Auto-save po każdej zmianie (debounce 500ms) + `<md-snackbar>` "Zapisano"
- `<md-outlined-text-field>` na komentarz (multiline)
- `<md-filled-button>` "Zapisz oceny" (fallback dla auto-save)

Metadane inwestycji pod formularzem: adres, termin oddania, liczba mieszkań, liczba zdjęć.

#### Prawa kolumna — Galeria

Siatka CSS Grid, `--gallery-columns: 3` (4 przy ekranie ≥ 1400px), gap 8px.

**Każde zdjęcie**:
- Proporcje 4:3, `object-fit: cover`
- **Klik lewym** → zaznacz/odznacz do usunięcia:
  - Zaznaczone: czerwony overlay `rgba(179,38,30,0.35)` + `<md-icon>delete</md-icon>` wycentrowane
- **Ctrl+klik** lub klik na ikonę lupki → lightbox (`<md-dialog>` fullscreen)

Pod galerią:
- Licznik: "Zaznaczono X z N zdjęć do usunięcia"
- `<md-outlined-button>` "Zapisz listę do usunięcia" (zapisuje `deletion_list.json`)
- `<md-text-button>` "Odznacz wszystkie"

#### Nawigacja klawiaturowa (widok inwestycji)

| Klawisz | Akcja |
|---|---|
| `←` | Poprzednia inwestycja |
| `→` | Następna inwestycja |
| `Escape` | Powrót do listy |
| `Tab` | Przeskok między kategoriami USI |
| `0`–`4` | Ustaw ocenę dla aktywnej kategorii USI |
| `Ctrl+S` | Zapisz oceny |

---

## C. Material Design 3 — wskazówki implementacji

### Ładowanie biblioteki (bez npm)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">

<script type="importmap">
{
  "imports": {
    "@material/web/": "https://esm.run/@material/web/"
  }
}
</script>
<script type="module">
  import '@material/web/all.js';
</script>
```

### Paleta kolorów (M3 light scheme)

| Token | Wartość | Użycie |
|---|---|---|
| `--md-sys-color-primary` | `#6750A4` | Aktywne chipy ocen, CTA |
| `--md-sys-color-surface` | `#FFFBFE` | Tło strony |
| `--md-sys-color-surface-variant` | `#E7E0EC` | Tło kart |
| `--md-sys-color-error` | `#B3261E` | Overlay "do usunięcia" |
| `--md-sys-color-on-surface` | `#1C1B1F` | Tekst główny |
| `--md-sys-color-on-surface-variant` | `#49454F` | Tekst drugorzędny |

### Kluczowe komponenty M3

| Element UI | Komponent | Uwagi |
|---|---|---|
| Powrót do listy | `<md-icon-button>` + `arrow_back` | W nagłówku widoku inwestycji |
| Przyciski ocen 0–4 | `<md-filter-chip>` | `selected` atrybut dla aktywnej wartości |
| Zapisz oceny | `<md-filled-button>` | Primary color |
| Komentarz | `<md-outlined-text-field type="textarea">` | `rows="3"` |
| Kafelki listy | `<md-elevated-card>` | `href` na całej karcie |
| Badge "do usunięcia" | `<md-badge>` | Na ikonie kosza w karcie |
| Powiadomienie | `<md-snackbar>` | Auto-dismiss po 3s |
| Filtry listy | `<md-filled-select>` + `<md-select-option>` | |
| Lightbox | `<md-dialog>` | `fullscreen` atrybut |

### Gęstość (Density)

M3 default jest przestronne — dla narzędzia pracy:

```css
md-filter-chip { --md-filter-chip-container-height: 28px; }
md-elevated-card { --md-elevated-card-container-color: var(--md-sys-color-surface-variant); }
.gallery-grid {
  display: grid;
  grid-template-columns: repeat(var(--gallery-columns, 3), 1fr);
  gap: var(--gallery-gap, 8px);
}
```

### Wzorzec segmented chips dla ocen USI

```html
<div class="usi-category" data-category="Balkony">
  <span class="md-typescale-label-large category-label">Balkony</span>
  <div class="rating-chips" role="group" aria-label="Ocena Balkony">
    <md-filter-chip label="0" data-value="0" aria-pressed="false"></md-filter-chip>
    <md-filter-chip label="1" data-value="1" aria-pressed="false"></md-filter-chip>
    <md-filter-chip label="2" data-value="2" aria-pressed="false"></md-filter-chip>
    <md-filter-chip label="3" data-value="3" aria-pressed="false"></md-filter-chip>
    <md-filter-chip label="4" data-value="4" aria-pressed="false"></md-filter-chip>
  </div>
</div>
```

JS obsługuje klik na chip: odznacza pozostałe w grupie, ustawia `selected`, triggeruje auto-save.

### Overlay "do usunięcia"

```css
.photo-wrapper { position: relative; cursor: pointer; }
.photo-wrapper.marked::after {
  content: '';
  position: absolute; inset: 0;
  background: rgba(179, 38, 30, 0.35);
  display: flex; align-items: center; justify-content: center;
}
.photo-wrapper.marked .delete-icon {
  position: absolute; top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  color: white; font-size: 36px;
  pointer-events: none;
}
```

### CSS token baseline

```css
:root {
  --md-sys-color-primary: #6750A4;
  --md-sys-color-surface: #FFFBFE;
  --md-sys-color-surface-variant: #E7E0EC;
  --md-sys-color-error: #B3261E;
  --md-sys-color-on-surface: #1C1B1F;
  --md-sys-color-on-surface-variant: #49454F;

  --gallery-columns: 3;
  --gallery-gap: 8px;
  --panel-width: 30%;
}

@media (min-width: 1400px) {
  :root { --gallery-columns: 4; }
}

body {
  font-family: 'Roboto', sans-serif;
  background-color: var(--md-sys-color-surface);
  color: var(--md-sys-color-on-surface);
  margin: 0;
}
```

---

## D. Plan testów interfejsu

### Testy jednostkowe — `python_worker/test_ui_server.py`

Testy używają `pytest` i `flask` test client (`app.test_client()`), z `tmp_path` do izolacji systemu plików. Nie trafiają do rzeczywistego folderu Dropbox.

| Test | Co weryfikuje |
|---|---|
| `test_list_investments_empty_dir` | Endpoint `/` zwraca 200 i pustą listę gdy `USIdata/` jest pusty |
| `test_list_investments_reads_metadata` | Dla fiksturowego `app_result_imported.json`, `/` zwraca nazwę i dewelopera |
| `test_api_data_returns_fields` | `GET /api/data/dev/inv` zwraca wymagane pola (`investment_slug`, `image_paths` itd.) |
| `test_api_data_merges_ratings` | Gdy istnieje `usi_ratings.json`, zwracane dane zawierają pole `ratings` |
| `test_ratings_save_creates_file` | `POST /api/ratings/dev/inv` z payload `{"Balkony": 2, ...}` tworzy `usi_ratings.json` |
| `test_ratings_valid_range` | Wartości 0–4 dla każdej kategorii są akceptowane (HTTP 200) |
| `test_ratings_invalid_score_rejected` | Wartość `5` lub `-1` zwraca HTTP 400 |
| `test_ratings_missing_category_ignored` | Brakująca kategoria w payloadzie nie powoduje błędu (opcjonalny zapis częściowy) |
| `test_deletion_list_save` | `POST /api/mark-delete/dev/inv` z listą ścieżek zapisuje `deletion_list.json` |
| `test_deletion_list_empty` | Pusty payload `[]` tworzy pusty `deletion_list.json` (bez błędu) |
| `test_image_serve_exists` | `/api/image/dev/inv/file.jpg` zwraca 200 i `Content-Type: image/jpeg` |
| `test_image_serve_missing` | `/api/image/dev/inv/nie_ma.jpg` zwraca 404 (nie 500) |
| `test_path_traversal_blocked` | Ścieżka `../../../etc/passwd` w URL zwraca 400 |
| `test_does_not_modify_existing_files` | Po `POST /api/ratings`, pliki `app_result_*.json` i `rp_details.json` pozostają niezmienione |

### Testy integracyjne manualne (checklista)

Wymagania wstępne: dane testowe w `Public/USI/` i `Public/USIdata/` (np. inwestycja `invest-komfort-spolka-akcyjna-spk/nowe-kolibki-etap-4-gdynia-orlowo`).

```bash
python3 -m python_worker.main ui
open http://localhost:5000
```

**Lista kontrolna:**

- [ ] **1. Lista ładuje się** — strona główna wyświetla co najmniej jeden kafelek inwestycji z thumbnail
- [ ] **2. Filtrowanie** — wybór dewelopera z dropdown odświeża listę i pokazuje tylko jego inwestycje
- [ ] **3. Otwarcie inwestycji** — klik w kafelek otwiera widok `/investment/dev/inv` z galerią i formularzem
- [ ] **4. Galeria widoczna** — zdjęcia ładują się przez `/api/image/...`, nie ma obrazków 404
- [ ] **5. Zaznaczenie do usunięcia** — klik na zdjęcie → czerwony overlay + ikona kosza; licznik "Zaznaczono X" aktualizuje się
- [ ] **6. Odznaczenie** — ponowny klik usuwa overlay; klik "Odznacz wszystkie" czyści całą galerię
- [ ] **7. Zapis listy do usunięcia** — "Zapisz listę do usunięcia" → plik `deletion_list.json` pojawia się w `USIdata/dev/inv/`
- [ ] **8. Oceny USI — kliknięcie** — klik na chip "3" dla "Balkony" → chip oznaczony jako `selected`
- [ ] **9. Auto-save ocen** — po zmianie oceny, po ≤1s pojawia się snackbar "Zapisano"; `usi_ratings.json` powstaje w `USIdata/dev/inv/`
- [ ] **10. Trwałość ocen** — odśwież stronę (`F5`) → poprzednio ustawione oceny są wczytane
- [ ] **11. Komentarz** — wpisanie tekstu w pole komentarza + auto-save → zapisany w `usi_ratings.json["komentarz"]`
- [ ] **12. Nawigacja klawiaturowa** — `→` otwiera następną inwestycję; `←` wraca do poprzedniej; `Escape` wraca do listy
- [ ] **13. Skrót oceny** — focus na kategorii "Fasady" + naciśnięcie klawisza `2` → chip "2" zaznaczony
- [ ] **14. Lightbox** — Ctrl+klik na zdjęcie otwiera `<md-dialog>` z pełnym zdjęciem; `Escape` zamyka
- [ ] **15. Integralność danych** — sprawdź że `app_result_*.json`, `rp_details.json`, `oto_details.json` NIE zostały zmodyfikowane (porównaj `mtime` przed i po sesji)
- [ ] **16. Izolacja folderów** — `usi_ratings.json` i `deletion_list.json` istnieją TYLKO w `USIdata/`, nie w `USI/`
- [ ] **17. Bezpieczeństwo ścieżek** — próba `http://localhost:5000/api/image/../../etc/passwd` zwraca 400 lub 404

### Uruchomienie testów jednostkowych

```bash
# Zainstaluj zależności jeśli potrzeba
pip install flask pytest

# Uruchom testy interfejsu
pytest python_worker/test_ui_server.py -v

# Pełna suite
pytest python_worker/ -v
```

---

## E. Pliki do utworzenia / zmodyfikowania

### Nowe pliki

```
python_worker/
├── ui_server.py              # Flask app + API endpoints
├── templates/
│   ├── index.html            # Lista inwestycji (Jinja2)
│   └── investment.html       # Widok inwestycji (Jinja2)
├── static/
│   ├── style.css             # CSS tokens M3 + layout
│   └── app.js                # Logika galerii, klawiatura, auto-save
└── test_ui_server.py         # Testy jednostkowe
```

### Modyfikacje istniejących plików

- [python_worker/main.py](../python_worker/main.py) — dodanie case `ui` w CLI dispatcher
- [python_worker/config.py](../python_worker/config.py) — stała `UI_PORT = 5000`
- `requirements.txt` — dodanie `flask>=3.0`

### Nie modyfikować

`bus.py`, `scraper_rp.py`, `scraper_otodom.py`, `image_saver.py` — żadnych zmian w logice scrapingu.
Żadnych istniejących plików JSON w `USIdata/`.
