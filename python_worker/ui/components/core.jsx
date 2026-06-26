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
 * resolvePhotoUrl - Extracts a string URL from potentially complex image objects.
 */
function resolvePhotoUrl(photo) {
  if (!photo) return null;
  if (typeof photo === 'string') return photo;
  if (typeof photo === 'object') {
    return photo.thumbnail || photo.medium || photo.small || photo.large || photo.url || null;
  }
  return null;
}
window.resolvePhotoUrl = resolvePhotoUrl;
window.usiRegister('resolvePhotoUrl', resolvePhotoUrl);

/**
 * USI_INVESTMENT_SCHEMA - Central definition for investment data validation.
 */
const USI_INVESTMENT_SCHEMA = {
  name: { type: 'string', fallback: 'Bez nazwy' },
  developer: { type: 'string', fallback: 'Nieznany deweloper' },
  district: { type: 'string', fallback: 'Brak lokalizacji' },
  address: { type: 'string', fallback: '—' },
  price_avg: { type: 'number', fallback: 0 },
  price_min: { type: 'number', fallback: null },
  price_max: { type: 'number', fallback: null },
  price_m2_min: { type: 'number', fallback: null },
  price_m2_max: { type: 'number', fallback: null },
  delivery: { type: 'string', fallback: '—' },
  ceiling_height_min: { type: 'number', fallback: null },
  ceiling_height_max: { type: 'number', fallback: null },
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
  // UWAGA: kolorowanie img jest ograniczone, ale używamy ujednoliconego zasobu
  return (
    <img
      data-component="USIStarLogo"
      src="/assets/usi-star-white.svg"
      width={size}
      height={size}
      alt="USI Star Logo"
      style={{ display: 'inline-block', verticalAlign: 'middle' }}
    />
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
  const { React } = window;
  const [imgError, setImgError] = React.useState(false);
  
  const safeTitle = safeRender(title, 'string', 'Brak tytułu');
  const safeSubtitle = safeRender(subtitle, 'string', '');

  // Handle complex image objects (Otodom pattern) or React elements
  let finalImage = null;
  if (image && !imgError) {
    if (typeof image === 'object' && image.$$typeof) {
      finalImage = image; // It's already a React element
    } else {
      // Use local function directly for safety in core.jsx
      const src = typeof resolvePhotoUrl === 'function' ? resolvePhotoUrl(image) : null;
      if (src) {
        finalImage = <img src={src} alt="" className="usi-card-img" loading="lazy" onError={() => setImgError(true)} />;
      }
    }
  }

  return (
    <article 
      data-component="StandardCard" 
      className={`usi-standard-card usi-card ${disabled ? 'flat disabled' : ''}`} 
      onClick={disabled ? null : onClick} 
      style={style}
    >
      <div className="usi-card-img-container">
        {!finalImage ? (
          <div className={`usi-card-img-placeholder ${imgError ? 'broken' : ''}`}>
            {imgError ? '⚠️' : '📷'}
          </div>
        ) : finalImage}
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
    { id: 'download', label: 'Pobieranie', icon: 'zap', desc: 'Skanowanie i status Wędrowca' },
    { id: 'reports', label: 'Raporty', icon: 'list', desc: 'Analizy i zestawienia' },
    { id: 'dashboard', label: 'Dashboard', icon: 'sparkle', desc: 'Podsumowania i wykresy' },
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
          {(() => {
            const { useDataBusSelector } = window;
            const health = useDataBusSelector(state => state.systemHealth);
            if (!health) return null;
            
            const isOk = health.ok && health.status === 'ok';
            const statusLabel = isOk ? 'Scrapers: Połączono' : 'Scrapers: Błąd spójności';
            const statusColor = isOk ? 'var(--usi-success)' : 'var(--usi-danger)';
            
            return (
              <div 
                className="usi-library-health" 
                title={health.error || (health.result && JSON.stringify(health.result))}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '12px 16px',
                  fontSize: '11px',
                  borderTop: '1px solid var(--usi-surface-3)',
                  color: statusColor,
                  background: 'var(--usi-surface-2)'
                }}
              >
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  background: statusColor,
                  boxShadow: isOk ? '0 0 8px var(--usi-success)' : 'none'
                }} />
                <span className="usi-nav-drawer-health-label">{statusLabel}</span>
              </div>
            );
          })()}

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

  // Renderuje pasek kropkowy o stałej szerokości 10 znaków
  const renderDotBar = (progress, total = 100) => {
    const width = 10;
    const percent = Math.min(100, Math.max(0, (progress / total) * 100));
    const filled = Math.round((percent / 100) * width);
    return '●'.repeat(filled) + '○'.repeat(width - filled);
  };

  // Pokazujemy tylko pierwsze aktywne zadanie w formie tekstowej konsoli
  const job = jobs[0];
  const progress = job.progress || 0;
  const total = job.total || 100;
  const message = job.message || 'Przetwarzanie...';
  const name = job.name || 'Zadanie';
  const isFinished = job.status === 'completed' || job.status === 'failed';

  // Format licznika: [n/m] jeśli total != 100, w przeciwnym razie [XX%]
  const counterStr = total !== 100 ? `[${progress}/${total}]` : `[${Math.round((progress/total)*100)}%]`;
  const dotBar = renderDotBar(progress, total);

  return (
    <div data-component="NotificationCenter" className="usi-notification-center-minimal">
      <div className="usi-mono usi-notification-center-text">
        <span style={{ color: isFinished ? 'var(--usi-success)' : 'inherit' }}>
          &gt; {name}: {message}
        </span>
        <span className="usi-notification-dotbar">{dotBar}</span>
        <span className="usi-notification-counter">{counterStr}</span>
        {jobs.length > 1 && <span className="usi-notification-extra"> (+{jobs.length - 1} zad.)</span>}
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
      {value && (
        <span 
          className="usi-global-search-clear" 
          onClick={() => onChange('')} 
          style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', padding: '0 8px', color: 'var(--usi-ink-3)' }}
        >
          <Icon name="close" size={14} />
        </span>
      )}
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

function ReportModal({ isOpen, onClose, onConfirm }) {
  const { React } = window;
  const [note, setNote] = React.useState('');
  if (!isOpen) return null;

  return (
    <div className="usi-modal-backdrop" onClick={onClose}>
      <div className="usi-modal-content usi-card" onClick={e => e.stopPropagation()}>
        <h2 className="usi-h2">Flaguj do audytu</h2>
        <p className="usi-small usi-text-secondary usi-m-t-4">Opisz problemy ze zdjęciami, metadanymi lub danymi dewelopera.</p>
        <textarea 
          className="usi-input usi-m-t-16" 
          style={{ width: '100%', minHeight: 120, resize: 'vertical', background: 'var(--usi-surface-2)' }}
          placeholder="np. Błędne zdjęcie główne, brak współrzędnych..."
          value={note}
          onChange={e => setNote(e.target.value)}
          autoFocus
        />
        <div className="usi-flex-row usi-gap-12 usi-m-t-24" style={{ justifyContent: 'flex-end' }}>
          <button className="usi-btn ghost" onClick={onClose}>Anuluj</button>
          <button className="usi-btn primary" onClick={() => { onConfirm(note); setNote(''); }}>Flaguj Inwestycję</button>
        </div>
      </div>
    </div>
  );
}
window.usiRegister('ReportModal', ReportModal);

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
  const [visible, setVisible] = React.useState(false);
  const notifications = bus.appNotifications || [];

  React.useEffect(() => {
    const handler = (e) => {
      if (e.key === '§') setVisible(v => !v);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  return (
    <div data-component="NotificationConsole"
         className={`usi-notification-console expanded${visible ? ' visible' : ''}`}>
      <div className="console-header" onClick={() => setVisible(false)}>
        <div className="usi-console-header-info">
          <Icon name="terminal" size={14} />
          <span className="usi-tiny usi-weight-700 usi-text-uppercase">
            Konsola [{notifications.length}] — § zamknij
          </span>
        </div>
        <div className="usi-console-header-actions">
          <button className="usi-btn sm ghost icon" onClick={(e) => { e.stopPropagation(); setVariable('appNotifications', []); }}>
            <Icon name="close" size={12} />
          </button>
        </div>
      </div>
      <div className="console-content usi-scroll">
        {notifications.length === 0
          ? <div className="console-line info"><span className="line-msg">— brak powiadomień —</span></div>
          : notifications.slice().reverse().map((n, i) => (
            <div key={i} className={`console-line ${n.type || 'info'}`}>
              <span className="line-time">[{new Date(n.time).toLocaleTimeString()}]</span>
              <span className="line-msg">{n.msg}</span>
            </div>
          ))
        }
      </div>
    </div>
  );
}
window.usiRegister('NotificationConsole', NotificationConsole);
