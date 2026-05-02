# Analiza Stylizacji Mapy (Ref: mapa-here.jpg)

Dokument ten opisuje parametry wizualne mapy referencyjnej oraz ich implementację w HERE Map Image API v3 dla projektu USI Tracker.

## Charakterystyka Wizualna
- **Paleta Barw**: Głęboka czerń/granat (Night mode). Brak widocznych lądów i wód w wysokim kontraście – mapa służy jako tło dla danych.
- **Etykiety**: Całkowity brak etykiet (nazw miast, ulic, POI). Minimalizuje to szum informacyjny.
- **Markery**: 
    - Kształt: Czyste koła (`circle`).
    - Kolor: Biały (`#FFFFFF`).
    - Wielkość: Mała (`small`), stała dla wszystkich punktów.
    - Brak etykiet tekstowych przy punktach.
- **Kompozycja**: Kadrowanie skupione na zagęszczeniu punktów, bez zbędnych marginesów (użycie `bbox` lub `padding`).

## Mapowanie na HERE API v3
Dla uzyskania powyższego efektu stosujemy następujące parametry:

| Cecha | Parametr API | Wartość |
|-------|--------------|---------|
| Styl Mapy | `style` | `lite.night` |
| Brak POI | `features` | `pois:disabled` |
| Kolor Punktu | `color` | `FFFFFF` |
| Ikona | `icon` | `circle` |
| Rozmiar | `size` | `small` |
| Proporcje | `WxH` | `600x600` (1:1) |
| Dopasowanie | Path Segment | `mc/overlay:padding=32` |
| Wiele punktów| `overlay` | Wielokrotne powtórzenie parametru `&overlay=point:...` (separator `|` może powodować błąd 400 w v3) |

## Uwagi Techniczne
- Styl `lite.night` jest preferowany nad `explore.night`, ponieważ natywnie ogranicza liczbę szczegółów topograficznych.
- Wyłączenie etykiet (`labels:disabled`) w niektórych konfiguracjach v3 może zwracać błąd 400, dlatego polegamy na minimalizmie stylu `lite`.
