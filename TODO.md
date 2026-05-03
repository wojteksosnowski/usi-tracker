# TODO

## Bieżący kamień milowy: Sklepik szkolny

Refactoring Styles to SCSS

### Krok B01. 
Zapamietaj stan wygladu wszystkich nazwanych elementow interfejsu. Zapisz go w formie wystarczajacej do pozniejszego testu refactoringu na SCSS.

### Krok B02. 
**Streamline `components.jsx`:**
   - Break down the 742 lines into smaller files:
     - `components/core.jsx`: UI primitives like `Spinner`, `Icon`.
     - `components/ratings.jsx`: Star Rating and rating components.
     - `components/modules.jsx`: `ModuleWrapper`, `BaseModule`.

### Krok B03. 
**Extract Inline Styles into SCSS Files:**
   - Categorize styles into separate SCSS files, e.g., `styles/components.scss` and `styles/views.scss`, to group similar styling items.

   Example: Replace this inline style:
   ```jsx
   <div style={{ padding: '16px', display: 'flex', background: 'var(--usi-bg)' }}></div>
   ```
   With this SCSS class:
   ```scss
   .dashboard-toolbar {
     padding: 16px;
     display: flex;
     background: var(--usi-bg);
   }
   ``
   Then use in JSX:
   ```jsx
   <div className="dashboard-toolbar"></div>
   ```

### Krok B04. 
**Use CSS Variables for Consistency:**
   - Define reusable variables in SCSS for colors, paddings, and fonts:
   ```scss
   :root {
     --usi-bg: #ffffff;
     --usi-accent: #e5006d;
   }
   ```

### Krok B05. 
**Refactor Animations:**
   - Move animations (e.g., `usi-slide-down`) into SCSS:
     ```scss
     @keyframes usi-slide-down {
       from {
         transform: translateY(-10px);
         opacity: 0;
       }
       to {
         transform: translateY(0);
         opacity: 1;
       }
     }

     .usi-slide-down {
       animation: usi-slide-down 0.2s ease-out forwards;
     }
     ```

### Krok B06. 
**Automate Style Management:**
   - Use tools like `stylelint` to keep code consistent and enforce best practices.
   - Use `postcss` for vendor prefixes and optimizations.

### Krok B07.
Przeprowadz automatyczne testy wykorzystujac zapisana wiedze z Krok B01. Porownaj wyglad elementow przed i po zmianie na SCSS. Zaplanuj automatyczne testy.  

## Następny kamień milowy: Bar Sushi

### Krok N01
Zasady Navbar-Top. Wprowadzenie jasnych reguł dla górnego paska: Hamburger, Tytuł, Nawigacja, Licznik oraz rezerwacja 50% szerokości na pole powiadomień.

### Krok N02
Zasady Navbar-Bottom. Wprowadzenie jasnych reguł dla dolnego paska: Filtry, Wyszukiwanie, Przełączniki, Przyciski oraz powiadomienia (1-2 linie tekstu).

## Przyszłe kamienie milowe

- **Raspbery** - Przygotowanie środowiska i testy wydajnościowe na docelowej architekturze ARM (Raspberry Pi) po przejściu testów lokalnych.
- **Crawler** — Powolne zaciąganie inwestycji w tle.
- **Wikipednia** — Dodawanie kontekstu do rekordów inwestycji.
