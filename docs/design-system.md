# USI Tracker Design System

System projektowy USI Tracker oparty jest na zasadach wysokiej gęstości informacji, nowoczesnej typografii oraz unikalnej palecie barw wywodzącej się z logo USI (6-ramienna gwiazdka).

## 1. Fundamenty (Tokens)

### Typografia
- **Font główny**: `Instrument Sans` (400, 500, 600, 700) - używany do treści i UI.
- **Font mono**: `JetBrains Mono` (400, 500) - używany do liczb, ścieżek plików i danych technicznych.
- **Skala**:
  - `h0`: 36px / 600 (nagłówki dashboardu)
  - `h1`: 28px / 600 (nazwa inwestycji)
  - `h2`: 20px / 600 (nagłówki sekcji)
  - `h3`: 15px / 600 (podtytuły)
  - `body`: 14px (standardowy tekst)
  - `small`: 12px (metadane, opisy)
  - `tiny`: 11px / 600 / All Caps (etykiety sekcji)

### Kolory Kategorii USI
Każda kategoria ocen posiada przypisany stały kolor:
- **Balkony**: `#E5006D` (magenta)
- **Fasady**: `#7DB951` (zielony)
- **Wnętrza**: `#F39200` (pomarańczowy)
- **Teren**: `#3989C6` (niebieski)
- **Mieszkania**: `#FFCC00` (żółty)
- **Udogodnienia**: `#7E7B7B` (szary)

### Motywy (Light & Dark)
Aplikacja w pełni wspiera tryb ciemny poprzez zmienne CSS `--usi-*`.

| Zmienna | Tryb Jasny | Tryb Ciemny | Opis |
| :--- | :--- | :--- | :--- |
| `--usi-bg` | `#F5F2EC` | `#16140F` | Tło główne aplikacji |
| `--usi-surface` | `#FFFFFF` | `#1F1C16` | Tło kart i paneli |
| `--usi-surface-2` | `#FAF8F3` | `#26221B` | Tło elementów interaktywnych (hover) |
| `--usi-ink` | `#1F1C16` | `#F5F1E8` | Główny kolor tekstu |
| `--usi-accent` | `#E5006D` | `#E5006D` | Główny kolor akcentu (gwiazdka USI) |
| `--usi-border` | `rgba(31,28,22,.1)` | `rgba(255,248,232,.08)` | Delikatne obramowania |

## 2. Katalog Komponentów (`data-component`)

Wszystkie kluczowe elementy UI są oznaczone atrybutem `data-component` w celu ułatwienia komunikacji i modyfikacji.

### Globalne / Wspólne
- `Spinner`: Animowany wskaźnik ładowania.
- `Icon`: System ikon liniowych (16px).
- `NavMenuButton`: Przycisk hamburgera.
- `NavDrawer`: Wysuwane menu nawigacyjne.
- `SourceBadge`: Mała etykieta źródła (RP, OTO, TO).

### Widok Listy (`view-list.jsx`)
- `ListGrid`: Główny kontener listy.
- `FilterBar`: Pasek filtrów na górze listy.
- `ListCard`: Pojedyncza karta inwestycji na liście.
- `CategoryStripe`: Mały kolorowy pasek ocen na karcie.

### Widok Szczegółowy (`view-detail.jsx`)
- `DetailRightPanel`: Główny kontener widoku rekordu.
- `HeroBand`: Górna sekcja z nazwą, linkami i mapą.
- `WeightedUsiScore`: Duża, graficzna ocena ważona USI na środku HeroBand.
- `MetadataBlock`: Sekcja danych technicznych (powierzchnia, ceny, dostawa).
- `ModeC`: Alternatywny tryb wyświetlania z galerią full-width.
- `MiniMap`: Mała podglądowa mapa HERE.

### Oceny i Interakcje (`view-detail-ratings.jsx`)
- `RatingsPanel`: Panel z suwakami/kółkami ocen kategorii.
- `CategoryRating`: Wiersz oceny pojedynczej kategorii.
- `StarRating` / `UsiStarScore`: Reprezentacja gwiazdkowa ocen.
- `ProgressRing`: Okrągły wskaźnik postępu wypełnienia ocen.

### Dashboard (`view-dashboard.jsx`)
- `DashboardGrid`: Główny kontener dashboardu.
- `DashboardMap`: Mapa z zaznaczonymi inwestycjami.
- `StatCard`: Karta z pojedynczą statystyką.

## 3. Zasady Layoutu
- **Gęstość**: UI jest zaprojektowane jako "high-density" — małe odstępy (8px/16px), kompaktowe czcionki.
- **Obramowania**: Stała grubość `.5px`.
- **Zaokrąglenia**: 8px (przyciski, inputy) do 14px (karty).
- **Cienie**: Trzy poziomy (`sm`, `md`, `lg`) zdefiniowane jako zmienne CSS.

## 4. Komunikacja z LLM
Przy zlecaniu zmian, używaj nazw z sekcji **Katalog Komponentów** (np. *"Zmień kolor tła w MetadataBlock"*), aby precyzyjnie wskazać element do modyfikacji.
