// theme.jsx — design system tokens dla USI
// Kolory pochodzą z logo USI (gwiazdka): 6 kolorów = 6 kategorii
// Każda kategoria ma swój kolor akcentu, używany w mini-paskach, wykresach itp.

const USI_CATEGORIES = [
  { key: 'Balkony',      short: 'BAL', color: '#E5006D', icon: 'balcony' },      // magenta
  { key: 'Fasady',       short: 'FAS', color: '#7DB951', icon: 'building' },     // zielony
  { key: 'Wnętrza',      short: 'WNT', color: '#F39200', icon: 'sofa' },         // pomarańczowy
  { key: 'Teren',        short: 'TER', color: '#3989C6', icon: 'tree' },         // niebieski
  { key: 'Mieszkania',   short: 'MSZ', color: '#FFCC00', icon: 'plan' },         // żółty
  { key: 'Udogodnienia', short: 'UDG', color: '#7E7B7B', icon: 'amenity' },      // szary
];

const USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona'];

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin'];

const SOURCES = [
  { id: 'RP', label: 'RynekPierwotny', color: '#0052FF' },
  { id: 'OTO', label: 'Otodom', color: '#00E676' },
  { id: 'TO', label: 'TabelaOfert', color: '#FF9800' }
];

// Inject design-system CSS once per page (vars + base typography + component primitives)
function injectThemeCSS() {
  // Styles are now loaded via link tags in index.html
}

function applyTheme(root, dark, accent) {
  if (accent) root.style.setProperty('--usi-accent', accent);
  document.documentElement.dataset.dark = dark ? '1' : '';
}

Object.assign(window, { USI_CATEGORIES, USI_STATUSES, MAIN_CITIES, SOURCES, injectThemeCSS, applyTheme });
