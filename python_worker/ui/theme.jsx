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
  '--usi-danger':        '#FF6B5C',
  '--usi-star-empty':    'rgba(245,241,232,0.16)',
  '--usi-star-half':     'linear-gradient(90deg, currentColor 50%, rgba(245,241,232,0.16) 50%)',
};

// Inject design-system CSS once per page (vars + base typography + component primitives)
function injectThemeCSS() {
  if (document.getElementById('usi-theme-css')) return;
  const style = document.createElement('style');
  style.id = 'usi-theme-css';
  style.textContent = `
    @import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    .usi-app {
      font-family: 'Instrument Sans', ui-sans-serif, system-ui, -apple-system, sans-serif;
      color: var(--usi-ink);
      background: var(--usi-bg);
      line-height: 1.42;
      letter-spacing: -0.005em;
      -webkit-font-smoothing: antialiased;
      font-feature-settings: 'ss01';
    }
    .usi-app * { box-sizing: border-box; }
    .usi-mono { font-family: 'JetBrains Mono', ui-monospace, monospace; font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }
    .usi-num  { font-variant-numeric: tabular-nums; }

    /* Typography scale */
    .usi-h0 { font-size: 36px; font-weight: 600; letter-spacing: -0.02em; line-height: 1.1; }
    .usi-h1 { font-size: 28px; font-weight: 600; letter-spacing: -0.015em; line-height: 1.15; }
    .usi-h2 { font-size: 20px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.2; }
    .usi-h3 { font-size: 15px; font-weight: 600; letter-spacing: -0.005em; }
    .usi-body { font-size: 14px; }
    .usi-small { font-size: 12px; color: var(--usi-ink-3); }
    .usi-tiny { font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase; color: var(--usi-ink-3); font-weight: 600; }

    /* Surfaces */
    .usi-card {
      background: var(--usi-surface);
      border: .5px solid var(--usi-border);
      border-radius: 14px;
      box-shadow: var(--usi-shadow-sm);
      overflow: hidden;
    }
    .usi-card.flat { box-shadow: none; }
    .usi-divider { height: 1px; background: var(--usi-border); margin: 0; border: 0; }

    /* Buttons */
    .usi-btn {
      display: inline-flex; align-items: center; gap: 6px;
      height: 32px; padding: 0 12px;
      border-radius: 8px;
      border: .5px solid var(--usi-border-strong);
      background: var(--usi-surface);
      color: var(--usi-ink);
      font: 500 13px/1 'Instrument Sans', sans-serif;
      cursor: pointer;
      transition: background .12s, transform .06s;
    }
    .usi-btn:hover { background: var(--usi-surface-2); }
    .usi-btn.primary {
      background: var(--usi-ink); color: var(--usi-bg); border-color: var(--usi-ink);
    }
    .usi-btn.primary:hover { background: var(--usi-ink-2); }
    .usi-btn.ghost { background: transparent; border-color: transparent; color: var(--usi-ink-3); }
    .usi-btn.ghost:hover { background: var(--usi-surface-2); color: var(--usi-ink); }
    .usi-btn.icon { width: 32px; padding: 0; justify-content: center; }
    .usi-btn.sm { height: 26px; padding: 0 9px; font-size: 12px; }
    .usi-btn.danger {
      background: var(--usi-danger); color: #fff; border-color: var(--usi-danger);
    }
    .usi-btn.danger:hover { filter: brightness(.92); }

    /* Pill badge */
    .usi-pill {
      display: inline-flex; align-items: center; gap: 4px;
      height: 22px; padding: 0 8px;
      border-radius: 999px;
      background: var(--usi-surface-3);
      color: var(--usi-ink-2);
      font-size: 11px; font-weight: 500; letter-spacing: 0.01em;
    }
    .usi-pill.success { background: color-mix(in oklab, var(--usi-success) 15%, transparent); color: var(--usi-success); }
    .usi-pill.danger  { background: color-mix(in oklab, var(--usi-danger) 16%, transparent); color: var(--usi-danger); }
    .usi-pill.outline { background: transparent; border: .5px solid var(--usi-border-strong); }

    /* Source badge — RP / OTO / TO */
    .usi-source {
      display: inline-flex; align-items: center;
      height: 18px; padding: 0 6px;
      border-radius: 4px;
      font-size: 10px; font-weight: 700; letter-spacing: 0.06em;
      background: var(--usi-ink); color: var(--usi-bg);
    }
    .usi-source.oto { background: #002C57; color: #fff; }   /* otodom navy */
    .usi-source.rp  { background: #C0392B; color: #fff; }
    .usi-source.to  { background: #5A4A2A; color: #fff; }

    /* Form fields */
    .usi-input {
      appearance: none;
      width: 100%; height: 34px; padding: 0 10px;
      border: .5px solid var(--usi-border-strong);
      border-radius: 8px;
      background: var(--usi-surface);
      color: var(--usi-ink);
      font: 13px 'Instrument Sans', sans-serif;
      outline: none;
      transition: border-color .12s, background .12s;
    }
    .usi-input:focus { border-color: var(--usi-ink); }
    .usi-textarea { min-height: 80px; padding: 9px 10px; resize: vertical; line-height: 1.45; height: auto; }

    /* Scrollbar */
    .usi-scroll { scrollbar-width: thin; scrollbar-color: var(--usi-border-strong) transparent; }
    .usi-scroll::-webkit-scrollbar { width: 8px; height: 8px; }
    .usi-scroll::-webkit-scrollbar-thumb { background: var(--usi-border-strong); border-radius: 4px; }

    /* USI rainbow stripe (paleta z logo) */
    .usi-rainbow {
      background: linear-gradient(90deg,
        #E5006D 0%, #E5006D 16.66%,
        #7DB951 16.66%, #7DB951 33.33%,
        #F39200 33.33%, #F39200 50%,
        #3989C6 50%, #3989C6 66.66%,
        #FFCC00 66.66%, #FFCC00 83.33%,
        #7E7B7B 83.33%, #7E7B7B 100%);
    }
  `;
  document.head.appendChild(style);
}

function applyTheme(root, dark, accent) {
  const palette = dark ? THEME_DARK : THEME_LIGHT;
  for (const [k, v] of Object.entries(palette)) root.style.setProperty(k, v);
  if (accent) root.style.setProperty('--usi-accent', accent);
  root.style.setProperty('--usi-bg-input', palette['--usi-surface']);
  document.documentElement.dataset.dark = dark ? '1' : '';
}

Object.assign(window, { USI_CATEGORIES, USI_STATUSES, THEME_LIGHT, THEME_DARK, injectThemeCSS, applyTheme });
