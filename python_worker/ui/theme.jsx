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

// Mapy palet light/dark — operujemy przez --usi-* CSS vars.
const THEME_LIGHT = {
  '--usi-bg':            '#F5F2EC',  // ciepły off-white tła
  '--usi-surface':       '#FFFFFF',
  '--usi-surface-2':     '#FAF8F3',
  '--usi-surface-3':     '#EFEAE0',
  '--usi-border':        'rgba(31, 28, 22, 0.10)',
  '--usi-border-strong': 'rgba(31, 28, 22, 0.20)',
  '--usi-ink':           '#1F1C16',
  '--usi-ink-2':         '#3A352B',
  '--usi-ink-3':         'rgba(31, 28, 22, 0.62)',
  '--usi-ink-4':         'rgba(31, 28, 22, 0.42)',
  '--usi-shadow-sm':     '0 1px 2px rgba(31,28,22,.06), 0 2px 6px rgba(31,28,22,.04)',
  '--usi-shadow-md':     '0 2px 4px rgba(31,28,22,.06), 0 8px 24px rgba(31,28,22,.08)',
  '--usi-shadow-lg':     '0 8px 16px rgba(31,28,22,.08), 0 24px 56px rgba(31,28,22,.12)',
  '--usi-overlay-strong':'rgba(255,255,255,.78)',
  '--usi-success':       '#1F8A4C',
  '--usi-warn':          '#F39200',
  '--usi-danger':        '#C0392B',
  '--usi-star-empty':    'rgba(31,28,22,0.14)',
  '--usi-star-half':     'linear-gradient(90deg, currentColor 50%, rgba(31,28,22,0.14) 50%)',
};

const THEME_DARK = {
  '--usi-bg':            '#16140F',
  '--usi-surface':       '#1F1C16',
  '--usi-surface-2':     '#26221B',
  '--usi-surface-3':     '#312C23',
  '--usi-border':        'rgba(255, 248, 232, 0.08)',
  '--usi-border-strong': 'rgba(255, 248, 232, 0.18)',
  '--usi-ink':           '#F5F1E8',
  '--usi-ink-2':         '#D8D2C2',
  '--usi-ink-3':         'rgba(245, 241, 232, 0.62)',
  '--usi-ink-4':         'rgba(245, 241, 232, 0.38)',
  '--usi-shadow-sm':     '0 1px 2px rgba(0,0,0,.4), 0 2px 6px rgba(0,0,0,.3)',
  '--usi-shadow-md':     '0 2px 4px rgba(0,0,0,.4), 0 8px 24px rgba(0,0,0,.45)',
  '--usi-shadow-lg':     '0 8px 16px rgba(0,0,0,.5), 0 24px 56px rgba(0,0,0,.55)',
  '--usi-overlay-strong':'rgba(22,20,15,.78)',
  '--usi-success':       '#4ED38A',
  '--usi-warn':          '#F39200',
  '--usi-danger':        '#FF6B5C',
  '--usi-star-empty':    'rgba(245,241,232,0.16)',
  '--usi-star-half':     'linear-gradient(90deg, currentColor 50%, rgba(245,241,232,0.16) 50%)',
};

// Inject design-system CSS once per page (vars + base typography + component primitives)
function injectThemeCSS() {
  // Styles are now loaded via link tags in index.html
}

function applyTheme(root, dark, accent) {
  const palette = dark ? THEME_DARK : THEME_LIGHT;
  for (const [k, v] of Object.entries(palette)) root.style.setProperty(k, v);
  if (accent) root.style.setProperty('--usi-accent', accent);
  root.style.setProperty('--usi-bg-input', palette['--usi-surface']);
  document.documentElement.dataset.dark = dark ? '1' : '';
}

Object.assign(window, { USI_CATEGORIES, USI_STATUSES, MAIN_CITIES, SOURCES, THEME_LIGHT, THEME_DARK, injectThemeCSS, applyTheme });
