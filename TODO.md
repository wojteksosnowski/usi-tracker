# TODO

## Bieżący kamień milowy: Pizzeria

### Krok B01

- [ ] Wyszukiwanie z API wikipedii interesujących obiektów w okolicy na podstawie lokalizacji

### Krok B02

- [x] element <header ...> do usunięcia. to artefakt. 
- [x] nacisniecie hamburger memu - wysuwana szuflada z listą opcji i przełącznikiem trybu light dark. 
- [x] szuflada zgodna z designem reszty strony. szuflada biale tlo, wysuwa sie spod paska narzędzi.
- [x] tlo szuflady biale, czcnionki bezszeryfowe. na dole szuflady przelacznik light/dark

### Krok B03

- [x] przejście na https://github.com/D4Vinci/Scrapling

### Krok B04

- [x] Dodac funkcjonalność ponownego załadowania JSONa ze strony dostawcy, sprawdzenia obecnosci nowych obrazow, nowych metadanych itp., bez psucia obecnego rekordu. JSON z głównym rekordem powinien zawierac log takich wydarzen.
- [x] utworz plik w ktorym zapiszesz jakie metadane moga byc wyswietlone w widoku rekordu

### Krok B05

- [x] mapa DashboardMap - podstaw stylizowana mape HERE
- [x] mapa DashboardMap - zaznaczaj inwestycje punktami bez liczb i innych informacji. punk ty musza byc widoczne.
- [x] mapa DashboardMap - dopasuj polozenie punktow do mapy
- [x] mapa DashboardMap - mapa powinna miec proporcje 1:1 w pliku źródłowym, a w oknie Dashboardu dostosowywać się do wysokości sąsiednich kart (gridRow span 2).
- [x] mapa DashboardMap - przygotuj plik ze szczegolowym opisem stylizacji pliku mapa-here.jpg
- [x] mapa DashboardMap - zapoaznaj sie z here_map_styling_analysis.md i popraw stylizacje mapy.

### Krok B06

- [x] przeniesc udogodnienia z kolumny 3 do kolumny 2 pod "ocena usi" a nad "status"
- [x] dodac przycisk pobrania nowego surowego JSONa od dostawcy
- [x] na srodku HeroBand umiescic ocene wazona ozbrazowana usi-star- i usi-zero- oraz ulamkami

### Krok B07

Podstrona pobierania, zawierajaca kompletne UI, bez bledow, przyciski pobierania, liczniki dostepnych rekordow, informacje o statusie pobierania

- [x] Utworzyć plik `python_worker/ui/view-download.jsx` ze szkieletem funkcyjnym `ViewDownload`
- [x] Zarejestrować komponent w `window.ViewDownload` (zgodnie z konwencją projektu)
- [x] Dodać import skryptu do `python_worker/ui/index.html`
- [x] Zaimplementować kontener `Box` z układem `flex` (sidebar + content) w `ViewDownload`
- [x] Zastosować odstępy `gap: 16px` i paddingi zgodne z `theme.jsx`
- [x] Dodać komponent `Typography` dla nagłówka sekcji
- [x] Utworzyć stan `results` i warunkowo wyświetlać `EmptyState` gdy lista jest pusta
- [x] Dodać stałą `VIEW_DOWNLOAD` do obiektu `VIEWS` w `app.jsx`
- [x] Zaktualizować instrukcję `switch` w głównym renderowaniu `App`, aby zwracała `<ViewDownload />`
- [x] Dodać element listy w komponencie `Drawer` z ikoną (np. `DownloadIcon`) i etykietą "Pobieranie"
- [x] Podpiąć `onClick`, który wywołuje `setView(VIEWS.VIEW_DOWNLOAD)` i zamyka szufladę
- [x] Zweryfikować poprawność przekazywania stanu nawigacji między `App` a `Drawer`
- [x] Przetestować przełączanie widoków w przeglądarce
- [x] Dodać komponent `Select` lub grupę `Button` do wyboru portalu w sidebarze
- [x] Utworzyć przycisk „Sprawdź aktualizacje” inicjujący żądanie do API
- [x] Dodać trasę `@app.route("/api/discovery/<portal>")` w `ui_server.py`
- [x] Zintegrować endpoint z funkcjami `discover_rp_investments`, `discover_otodom_investments` lub `discover_to_investments`
- [x] Dodać funkcję `fetchDiscovery` w `view-download.jsx` korzystającą z `fetch`
- [x] Zmapować wyniki z API na listę kart/wierszy z przyciskiem „Pobierz/Aktualizuj” dla każdego elementu

### Krok B17

Podstrona Pobierania - musi przejsc test funkcjonalnosci, test widocznosci elementow, test pobierania.

- [x] Nie dziala szuflada
- [x] Niezrozumiały "identyfikator portalu", nigdy wczesniej tego nie bylo
- [x] Zapoznaj sie z materilami /docs/coda aby lepiej zrozumiec jak byly pobierane nowosci ze stron (RP - JSON query, OTO - JSON ze strony z lista inwestycji)

### Krok B27

Podstrona Pobierania

- [x] Pobieranie po deweloperach przeniesc do nastepnego kamienia milowego
- [x] Pobieranie ze stron RP i OTO - zapoznaj sie z plikami pobieranie-rp.md  i pobieranie-oto.md, wyszukaj pokrewne informacje w dokumentach projektu. zadaj pytania gdy nie rozumiesz. 
- [x] Sprobuj zrozumiec query ktore jest wysylane do RP aby uzyskac JSONa z listą inwestycji

### Krok B08

- [x] przenalizuj dotychczasowy design frontendu, przygotuj na tej podstawie szczegolowy opis design system 
- [x] sprawdz czy wszystkie elementy frontendu maja Nazwy sluzace do identyfikowania ich w celu wymiany informacji miedzy uzytkownikiem a LLM

## Następny kamień milowy: Lodziarnia

Ten kamien milowy uporzadkuje importowanie z RP, OTO i TO. Podstrona Pobieranie.

### Krok L01

RP: używanie JSON query tak jak coda.io JSONMAIN RP.  

### Krok L02

OTO: używa predefiniowanej listy adresów, skąd zaciąga listę z HTML (zagnieżdżony JSON). 

### Krok L03

* RP i OTO: zaciąga listę wskaźników inwestycji, którą najpierw odmiela z powtórzeń względem bazy usidata.  

### Krok L04

* Wskaźniki inwestycji są otwierane i system pobiera surowy JSON inwestycji.  

### Krok L05

* Z surowego JSONA system pobiera grafiki i metadane.  

### Krok L06

* Należy zawsze pobierać największy dostępny rozmiar grafik.  

### Krok L07

* Tabela ofert powinna naśladować mechanizm RP i OTO.

### Krok L08

1. Przycisk do zeskanowania nowości bez pobierania.  

### Krok L09

2. Przycisk do pobierania. Przed przyciskiem toggle dla 3 stron RP, OTO, TO 

### Krok L10

4. Postęp w formie: napis informujący o aktualnym działaniu oraz tekstowa belka postępu. 

### Krok L11

5. Delay między zapytaniami, szczególnie dla Otodom (ryzyko blokowania).  

### Krok L12

6. Graficzna informacja o liczbie nowych ofert na inwestycji.


## Przyszłe kamienie milowe

### Krok P01

- [ ] uruchomienie na raspberry pi - dopiero po przejsciu rozleglych testow na lokalnym komputerze

### Krok P02

- [ ] Analiza trendów cenowych: zmiana średniej ceny za m² w czasie.
- [ ] Porównywarka inwestycji: widok side-by-side dla wybranych ofert.
- [ ] Raport "Okazje": automatyczne wykrywanie spadków cen i nowych ofert.
- [ ] Heatmapa dostępności: zagęszczenie inwestycji na mapie.

### Krok P03

- [ ] Eksport do XLSX/CSV dla przefiltrowanych list inwestycji.

### Krok P04

- [ ] System powiadomień o nowych inwestycjach (crawler alerts).

### Krok P05

Podstrona Deweloperzy. Utworzenie podstrony do przegladania listy deweloperów.

- [ ] Utworzyc podstrone Deweloperzy
- [ ] Pobieranie i zarządzanie listą deweloperów (przeniesione z B27)
- [ ] Automatyczne dopasowywanie inwestycji do deweloperów na podstawie danych portalowych

### Krok P06



