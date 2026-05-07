// core.jsx — UI primitives for USI

/**
 * safeRender - Validates value type before rendering.
 * Prevents "Objects are not valid as a React child" and other rendering crashes.
 */
function safeRender(val, expectedType = 'string', fallback = '—') {
  if (val === null || val === undefined) return fallback;
  
  // Handle React elements (already rendered)
  if (typeof val === 'object' && val.$$typeof) return val;

  const actualType = Array.isArray(val) ? 'array' : typeof val;
  
  // Special case: currency formatting
  if (expectedType === 'currency') {
    if (actualType === 'number') return `${val.toLocaleString('pl-PL')} zł/m²`;
    if (actualType === 'string' && !isNaN(val) && val !== '') return `${Number(val).toLocaleString('pl-PL')} zł/m²`;
    return fallback;
  }

  if (actualType === expectedType) {
    if (expectedType === 'string' && val.trim() === '') return fallback;
    return val;
  }
  
  // Special case: numbers can often be rendered as strings
  if (expectedType === 'string' && actualType === 'number') return String(val);

  return fallback;
}
window.safeRender = safeRender;
window.usiRegister('safeRender', safeRender);

/**
 * USI_INVESTMENT_SCHEMA - Central definition for investment data validation.
 */
const USI_INVESTMENT_SCHEMA = {
  name: { type: 'string', fallback: 'Bez nazwy' },
  developer: { type: 'string', fallback: 'Nieznany deweloper' },
  district: { type: 'string', fallback: 'Brak lokalizacji' },
  address: { type: 'string', fallback: '—' },
  price_avg: { type: 'number', fallback: 0 },
  delivery: { type: 'string', fallback: '—' },
  coords: { type: 'array', fallback: [0, 0] },
  photos: { type: 'array', fallback: [] },
  ratings: { type: 'object', fallback: {} },
  source: { type: 'string', fallback: '?' },
  source_url: { type: 'string', fallback: '' },
  source_links: { type: 'array', fallback: [] }
};
window.USI_INVESTMENT_SCHEMA = USI_INVESTMENT_SCHEMA;

/**
 * validateData - Transforms raw data into a schema-compliant object.
 */
function validateData(data, schema = USI_INVESTMENT_SCHEMA) {
  const result = {};
  const raw = data || {};
  
  Object.keys(schema).forEach(key => {
    const spec = schema[key];
    const val = raw[key];
    result[key] = safeRender(val, spec.type, spec.fallback);
    
    // Debug warning for type mismatches (excluding null/undefined)
    if (val !== undefined && val !== null) {
      const actualType = Array.isArray(val) ? 'array' : typeof val;
      if (actualType !== spec.type && !(spec.type === 'string' && actualType === 'number')) {
        console.warn(`[DataBoundary] Type mismatch for key "${key}": expected ${spec.type}, got ${actualType}.`, { val });
      }
    }
  });
  
  // Preserve keys not in schema (e.g., slug, source_url)
  return { ...raw, ...result };
}
window.validateData = validateData;

/**
 * DataBoundary - A component that ensures data integrity for its children.
 * Usage: <DataBoundary data={inv} schema={...}>{(validInv) => <MyComp inv={validInv} />}</DataBoundary>
 */
function DataBoundary({ data, schema = USI_INVESTMENT_SCHEMA, children }) {
  const validData = React.useMemo(() => validateData(data, schema), [data, schema]);
  
  if (typeof children === 'function') {
    return children(validData);
  }
  
  return children;
}
window.usiRegister('DataBoundary', DataBoundary);

function USIStarLogo({ size = 24, color }) {
  return (
    <svg data-component="USIStarLogo" width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z" fill={color || 'currentColor'} />
    </svg>
  );
}
window.usiRegister('USIStarLogo', USIStarLogo);

function SourceBadge({ source, url }) {
  const cls = source === 'OTO' || source === 'oto' || source === 'otodom' ? 'oto' : (source === 'RP' || source === 'rp' ? 'rp' : 'to');
  const label = (source === 'otodom' ? 'OTO' : source ? source.toUpperCase() : '??');

  if (url) {
    return (
      <a
        data-component="SourceBadge"
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className={`usi-source ${cls}`}
        onClick={e => e.stopPropagation()}
      >
        {label}
      </a>
    );

  }
  return <span data-component="SourceBadge" className={`usi-source ${cls}`}>{label}</span>;
}
window.usiRegister('SourceBadge', SourceBadge);

function FilterChip({ label, active, onClick, color, source }) {
  return (
    <button
      data-component="FilterChip"
      data-active={active}
      onClick={(e) => onClick && onClick(e.shiftKey)}
      className="usi-filter-chip"
      style={{
        borderColor: active ? (color || 'var(--usi-accent)') : 'var(--usi-border)',
        background: active ? (color ? color + '15' : 'rgba(229, 0, 109, 0.1)') : 'var(--usi-surface)',
        color: active ? (color || 'var(--usi-accent)') : 'var(--usi-ink-3)',
      }}
    >
      {label}
    </button>
  );
}
window.usiRegister('FilterChip', FilterChip);

function StandardCard({ 
  image, 
  title, 
  subtitle, 
  extra, 
  badges, 
  footerLeft, 
  footerRight, 
  onClick, 
  disabled = false,
  overlay = null,
  style = {}
}) {
  const safeTitle = safeRender(title, 'string', 'Brak tytułu');
  const safeSubtitle = safeRender(subtitle, 'string', '');
  const safeImage = safeRender(image, 'object', null); // Returns object if it's a React element

  return (
    <article 
      data-component="StandardCard" 
      className={`usi-standard-card usi-card ${disabled ? 'flat disabled' : ''}`} 
      onClick={disabled ? null : onClick} 
      style={style}
    >
      <div className="usi-card-img-container">
        {image ? (
          typeof image === 'string' ? <img src={image} alt="" className="usi-card-img" /> : safeImage
        ) : (
          <div className="usi-card-img-placeholder">📷</div>
        )}
        <div className="usi-card-badges">
          {badges}
        </div>
        {overlay}
      </div>

      <div className="usi-card-body">
        <div>
          <h3 className="usi-h3 usi-card-title">{safeTitle}</h3>
          <div className="usi-small usi-card-subtitle">{safeSubtitle}</div>
          {extra && <div className="usi-tiny usi-card-extra">{safeRender(extra)}</div>}
        </div>
        <div className="usi-card-footer">
          <div>{footerLeft}</div>
          <div className="usi-card-footer-right">{footerRight}</div>
        </div>
      </div>
    </article>
  );
}
window.usiRegister('StandardCard', StandardCard);

function ProgressRing({ value, max, size = 32, stroke = 3, color }) {
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c - (value / max) * c;
  return (
    <svg data-component="ProgressRing" width={size} height={size}>
      <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="var(--usi-star-empty)" strokeWidth={stroke} />
      <circle cx={size/2} cy={size/2} r={r} fill="none"
        stroke={color || 'var(--usi-accent)'} strokeWidth={stroke}
        strokeDasharray={c} strokeDashoffset={offset} strokeLinecap="round"
        transform={`rotate(-90 ${size/2} ${size/2})`}
        style={{ transition: 'stroke-dashoffset .3s' }} />
    </svg>
  );
}
window.usiRegister('ProgressRing', ProgressRing);

function NavbarShell({ left, center, right, style = {} }) {
  return (
    <header data-component="NavbarShell" className="usi-navbar-top" style={style}>
      <div className="usi-navbar-left">{left}</div>
      <div className="usi-navbar-center">{center}</div>
      <div className="usi-navbar-right">{right}</div>
    </header>
  );
}
window.usiRegister('NavbarShell', NavbarShell);

function NavMenuButton({ onClick, label = 'Menu' }) {
  const { Icon } = window;
  return (
    <button data-component="NavMenuButton" className="usi-btn ghost icon" onClick={onClick} title={label} aria-label={label}>
      <Icon name="menu" size={18} />
    </button>
  );
}
window.usiRegister('NavMenuButton', NavMenuButton);

function NavDrawer({ current = 'list', onClose, onNav, dark, onToggleTheme }) {
  const { React, Icon } = window;
  const items = [
    { id: 'list', label: 'Inwestycje', icon: 'grid', desc: 'Lista wszystkich inwestycji' },
    { id: 'developers', label: 'Deweloperzy', icon: 'list', desc: 'Baza firm deweloperskich' },
    { id: 'reports', label: 'Raporty', icon: 'list', desc: 'Analizy i zestawienia' },
    { id: 'dashboard', label: 'Dashboard', icon: 'sparkle', desc: 'Podsumowania i wykresy' },
    { id: 'download', label: 'Pobieranie', icon: 'download', desc: 'Pobierz nowe inwestycje' },
    { id: 'storyboard', label: 'Storyboard', icon: 'layout', desc: 'Izolowane środowisko testowe' },
    { id: 'library', label: 'Biblioteka', icon: 'box', desc: 'Przegląd komponentów systemowych' },
  ];

  React.useEffect(() => {
    const k = (e) => { if (e.key === 'Escape') onClose(); };
    document.addEventListener('keydown', k);
    return () => document.removeEventListener('keydown', k);
  }, [onClose]);

  return (
    <>
      <div 
        data-component="NavDrawer-Backdrop"
        onClick={onClose}
        className="usi-nav-drawer-backdrop"
      />
      <aside 
        data-component="NavDrawer" 
        className="usi-nav-drawer usi-slide-down"
      >
        <nav className="usi-nav-drawer-nav usi-scroll">
          {items.map(it => {
            const active = it.id === current;
            return (
              <button key={it.id} 
                data-component="NavDrawer-Item"
                data-active={active}
                onClick={() => { if (onNav) onNav(it.id); onClose(); }}
                className="usi-nav-item"
              >
                <span className="usi-nav-item-icon-wrapper" style={{
                  background: active ? 'var(--usi-accent)' : 'var(--usi-surface-3)',
                  color: active ? '#fff' : 'var(--usi-ink-3)',
                }}>
                  <Icon name={it.icon} size={14} />
                </span>
                <span className="usi-nav-item-text-box">
                  <span className="usi-nav-item-label">{it.label}</span>
                </span>
                {active && <span className="usi-nav-item-active-indicator" />}
              </button>
            );
          })}
        </nav>

        <div className="usi-nav-drawer-footer">
          <button
            data-component="ThemeToggle"
            onClick={onToggleTheme}
            className="usi-theme-toggle"
          >
            <span className="usi-theme-toggle-icon">{dark ? '☀' : '◑'}</span>
            <span>{dark ? 'Jasny motyw' : 'Ciemny motyw'}</span>
          </button>

          <button
            data-component="ExportBaseline"
            onClick={() => window.captureVisualBaseline && window.captureVisualBaseline()}
            className="usi-export-baseline"
          >
            <Icon name="download" size={14} />
            <span>Eksportuj Baseline (Visual)</span>
          </button>
        </div>
      </aside>
    </>
  );
}
window.usiRegister('NavDrawer', NavDrawer);

function NotificationCenter() {
  const { React, useDataBus } = window;
  const { bus } = useDataBus();
  const jobs = bus.activeJobs || [];

  if (jobs.length === 0) return null;

  // Pokazujemy tylko pierwsze aktywne zadanie dla uproszczenia w Navbarze
  const job = jobs[0];
  const progress = job.progress || 0;

  return (
    <div data-component="NotificationCenter" className="usi-notification-center">
      <div className="usi-notification-center-header">
        <span className="usi-notification-center-title">
          Zadanie w toku
        </span>
        <span className="usi-mono usi-notification-center-progress-text">{progress}%</span>
      </div>
      <div className="usi-notification-center-body">
        <span className="usi-notification-center-job-name">
          {job.name || 'Przetwarzanie...'}
        </span>
        <div className="usi-notification-center-bar-bg">
          <div className="usi-notification-center-bar-fill" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </div>
  );
}
window.usiRegister('NotificationCenter', NotificationCenter);

function ActionBar({ left, center, right, style = {} }) {
  return (
    <footer data-component="ActionBar" className="usi-navbar-bottom" style={style}>
      <div className="usi-action-left">{left}</div>
      <div className="usi-action-center">{center}</div>
      <div className="usi-action-right">{right}</div>
    </footer>
  );
}
window.usiRegister('ActionBar', ActionBar);

function GlobalSearch({ value, onChange, placeholder = 'Szukaj...', onKeyDown }) {
  const { Icon } = window;
  return (
    <div data-component="GlobalSearch" className="usi-global-search-container">
      <span className="usi-global-search-icon">
        <Icon name="search" size={14} />
      </span>
      <input
        data-component="Search-Input"
        className="usi-input usi-global-search-input"
        placeholder={placeholder}
        value={value}
        onChange={e => onChange(e.target.value)}
        onKeyDown={onKeyDown}
      />
    </div>
  );
}window.usiRegister('GlobalSearch', GlobalSearch);

function FilterGroup({ label, children }) {
  return (
    <div data-component="FilterGroup" className="usi-filter-group">
      {children}
    </div>
  );
}
window.usiRegister('FilterGroup', FilterGroup);

function StatusMessenger() {
  const { React, useDataBus, Icon } = window;
  const { bus, setVariable } = useDataBus();
  const status = bus.appStatus;

  React.useEffect(() => {
    if (status) {
      // Dodaj do historii powiadomień
      setVariable('appNotifications', prev => {
        const last = prev[prev.length - 1];
        if (last && last.msg === status.msg) return prev; // Unikaj duplikatów
        return [...(prev || []), { ...status, time: Date.now() }];
      });

      if (status.type !== 'error') {
        const timer = setTimeout(() => {
          setVariable('appStatus', null);
        }, 3000);
        return () => clearTimeout(timer);
      }
    }
  }, [status, setVariable]);

  if (!status) return null;

  const config = {
    success: { icon: 'check', color: 'var(--usi-success)', bg: 'rgba(34, 197, 94, 0.1)' },
    error: { icon: 'close', color: 'var(--usi-error)', bg: 'rgba(239, 68, 68, 0.1)' },
    info: { icon: 'info', color: 'var(--usi-accent)', bg: 'rgba(229, 0, 109, 0.1)' },
  };

  const theme = config[status.type] || config.info;

  return (
    <div data-component="StatusMessenger" className="usi-status-messenger" style={{
      background: theme.bg, color: theme.color,
      border: `.5px solid ${theme.color}40`,
    }}>
      <Icon name={theme.icon} size={14} stroke={2.5} />
      <span className="usi-status-messenger-text">
        {status.msg}
      </span>
      {status.type === 'error' && (
        <button onClick={() => setVariable('appStatus', null)} className="usi-status-messenger-close">
          <Icon name="close" size={12} />
        </button>
      )}
    </div>
  );
}
window.usiRegister('StatusMessenger', StatusMessenger);

function NavbarTitle({ title, subtitle }) {
  return (
    <div data-component="NavbarTitle" className="usi-navbar-title-container">
      <span className="usi-navbar-title">{title}</span>
      {subtitle && <span className="usi-navbar-subtitle">{subtitle}</span>}
    </div>
  );
}
window.usiRegister('NavbarTitle', NavbarTitle);

function NotificationConsole() {
  const { React, useDataBus, Icon } = window;
  const { bus, setVariable } = useDataBus();
  const [minimized, setMinimized] = React.useState(true);
  const notifications = bus.appNotifications || [];

  if (notifications.length === 0) return null;

  return (
    <div data-component="NotificationConsole" className={`usi-notification-console ${minimized ? 'minimized' : 'expanded'}`}>
      <div className="console-header" onClick={() => setMinimized(!minimized)}>
        <div className="usi-console-header-info">
          <Icon name="terminal" size={14} />
          <span className="usi-tiny usi-weight-700 usi-text-uppercase">Konsola powiadomień ({notifications.length})</span>
        </div>
        <div className="usi-console-header-actions">
          <button className="usi-btn sm ghost icon" onClick={(e) => { e.stopPropagation(); setVariable('appNotifications', []); }}>
            <Icon name="close" size={12} />
          </button>
          <Icon name={minimized ? 'chevronUp' : 'chevronDown'} size={14} />
        </div>
      </div>
      {!minimized && (
        <div className="console-content usi-scroll">
          {notifications.slice().reverse().map((n, i) => (
            <div key={i} className={`console-line ${n.type || 'info'}`}>
              <span className="line-time">[{new Date(n.time).toLocaleTimeString()}]</span>
              <span className="line-msg">{n.msg}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
window.usiRegister('NotificationConsole', NotificationConsole);
