// core.jsx — UI primitives for USI

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
        style={{ textDecoration: 'none' }}
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
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '6px 12px',
        borderRadius: '16px',
        fontSize: '11px',
        fontWeight: 700,
        cursor: 'pointer',
        border: '1.5px solid ' + (active ? (color || 'var(--usi-accent)') : 'var(--usi-border)'),
        background: active ? (color ? color + '15' : 'rgba(229, 0, 109, 0.1)') : 'var(--usi-surface)',
        color: active ? (color || 'var(--usi-accent)') : 'var(--usi-ink-3)',
        transition: 'all 0.15s ease',
        boxShadow: active ? '0 2px 4px rgba(0,0,0,0.06)' : 'none',
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
  return (
    <article 
      data-component="StandardCard" 
      className={`usi-card ${disabled ? 'flat' : ''}`} 
      onClick={disabled ? null : onClick} 
      style={{ 
        height: 320, 
        display: 'flex', 
        flexDirection: 'column', 
        cursor: disabled ? 'default' : 'pointer', 
        opacity: disabled ? 0.7 : 1,
        ...style 
      }}
    >
      <div style={{ position: 'relative', height: 160, background: 'var(--usi-surface-3)', overflow: 'hidden' }}>
        {image ? (
          typeof image === 'string' ? <img src={image} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : image
        ) : (
          <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--usi-ink-4)', fontSize: 32 }}>📷</div>
        )}
        <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', gap: 6 }}>
          {badges}
        </div>
        {overlay && (
          <div style={{
            position: 'absolute', inset: 0, background: 'rgba(0,0,0,0.4)', 
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 800, fontSize: 14, backdropFilter: 'blur(2px)',
            zIndex: 2
          }}>
            {overlay}
          </div>
        )}
      </div>
      <div style={{ padding: '12px 14px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <h3 className="usi-h3" style={{ margin: 0, marginBottom: 2, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{title}</h3>
          <div className="usi-small" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{subtitle}</div>
          {extra && <div className="usi-tiny" style={{ marginTop: 4, opacity: 0.7 }}>{extra}</div>}
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>{footerLeft}</div>
          <div style={{ textAlign: 'right' }}>{footerRight}</div>
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
        <nav style={{ flex: 1, padding: '12px 10px', overflow: 'auto' }} className="usi-scroll">
          {items.map(it => {
            const active = it.id === current;
            return (
              <button key={it.id} 
                data-component="NavDrawer-Item"
                data-active={active}
                onClick={() => { if (onNav) onNav(it.id); onClose(); }}
                className="usi-nav-item"
              >
                <span className="usi-nav-icon-wrapper" style={{
                  background: active ? 'var(--usi-accent)' : 'var(--usi-surface-3)',
                  color: active ? '#fff' : 'var(--usi-ink-3)',
                }}>
                  <Icon name={it.icon} size={14} />
                </span>
                <span style={{ flex: 1, minWidth: 0 }}>
                  <span style={{ display: 'block', fontWeight: 600, fontSize: 13 }}>{it.label}</span>
                </span>
                {active && <span style={{ width: 4, height: 16, borderRadius: 2, background: 'var(--usi-accent)' }} />}
              </button>
            );
          })}
        </nav>

        <div style={{ padding: '12px', borderTop: '.5px solid var(--usi-border)', background: 'var(--usi-surface-2)', display: 'flex', flexDirection: 'column', gap: 8 }}>
          <button
            data-component="ThemeToggle"
            onClick={onToggleTheme}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 12px', borderRadius: 6, border: '.5px solid var(--usi-border-strong)',
              background: 'var(--usi-surface)', color: 'var(--usi-ink)',
              cursor: 'pointer', fontFamily: 'inherit', fontWeight: 600, fontSize: 12
            }}
          >
            <span style={{ fontSize: 16 }}>{dark ? '☀' : '◑'}</span>
            <span>{dark ? 'Jasny motyw' : 'Ciemny motyw'}</span>
          </button>

          <button
            data-component="ExportBaseline"
            onClick={() => window.captureVisualBaseline && window.captureVisualBaseline()}
            style={{
              width: '100%', display: 'flex', alignItems: 'center', gap: 10,
              padding: '8px 12px', borderRadius: 6, border: '.5px solid var(--usi-border)',
              background: 'var(--usi-surface-3)', color: 'var(--usi-ink-2)',
              cursor: 'pointer', fontFamily: 'inherit', fontWeight: 500, fontSize: 11
            }}
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
    <div data-component="NotificationCenter" style={{ 
      width: '100%', maxWidth: 400, display: 'flex', flexDirection: 'column', gap: 4,
      background: 'var(--usi-surface-2)', padding: '6px 12px', borderRadius: 8,
      border: '.5px solid var(--usi-border)', animation: 'usi-slide-down 0.3s ease-out'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span className="usi-tiny" style={{ fontWeight: 700, color: 'var(--usi-accent)', textTransform: 'uppercase', fontSize: 9 }}>
          Zadanie w toku
        </span>
        <span className="usi-mono" style={{ fontSize: 10, fontWeight: 700 }}>{progress}%</span>
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span className="usi-small" style={{ fontWeight: 600, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {job.name || 'Przetwarzanie...'}
        </span>
        <div style={{ flex: 1.5, height: 4, background: 'var(--usi-surface-3)', borderRadius: 2, overflow: 'hidden' }}>
          <div style={{ 
            height: '100%', width: `${progress}%`, background: 'var(--usi-accent)', 
            transition: 'width 0.3s ease-out', borderRadius: 2 
          }} />
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
    <div data-component="GlobalSearch" style={{
      position: 'relative', flex: 1, maxWidth: 400, display: 'flex', alignItems: 'center'
    }}>
      <span style={{ position: 'absolute', left: 12, color: 'var(--usi-ink-4)', display: 'flex' }}>
        <Icon name="search" size={14} />
      </span>
      <input
        data-component="Search-Input"
        className="usi-input"
        style={{ paddingLeft: 34, height: 36, borderRadius: 18, fontSize: 13, background: 'var(--usi-surface-2)', border: '.5px solid var(--usi-border)' }}
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
    <div data-component="FilterGroup" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      {label && <span className="usi-tiny" style={{ fontWeight: 700, opacity: 0.6, textTransform: 'uppercase' }}>{label}</span>}
      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
        {children}
      </div>
    </div>
  );
}
window.usiRegister('FilterGroup', FilterGroup);

function StatusMessenger() {
  const { React, useDataBus, Icon } = window;
  const { bus, setVariable } = useDataBus();
  const status = bus.appStatus;

  React.useEffect(() => {
    if (status && status.type !== 'error') {
      const timer = setTimeout(() => {
        setVariable('appStatus', null);
      }, 3000);
      return () => clearTimeout(timer);
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
    <div data-component="StatusMessenger" style={{
      display: 'flex', alignItems: 'center', gap: 8, padding: '6px 14px',
      borderRadius: '20px', background: theme.bg, color: theme.color,
      border: `.5px solid ${theme.color}40`, animation: 'usi-slide-down 0.2s ease-out'
    }}>
      <Icon name={theme.icon} size={14} stroke={2.5} />
      <span style={{ fontSize: 13, fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
        {status.msg}
      </span>
      {status.type === 'error' && (
        <button onClick={() => setVariable('appStatus', null)} style={{ 
          background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', padding: 2, display: 'flex' 
        }}>
          <Icon name="close" size={12} />
        </button>
      )}
    </div>
  );
}
window.usiRegister('StatusMessenger', StatusMessenger);

function NavbarTitle({ title, subtitle }) {
  return (
    <div data-component="NavbarTitle" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <span style={{ fontWeight: 700, fontSize: 15, lineHeight: 1.2, color: 'var(--usi-ink)' }}>{title}</span>
      {subtitle && <span style={{ fontSize: 11, fontWeight: 500, color: 'var(--usi-ink-3)' }}>{subtitle}</span>}
    </div>
  );
}
window.usiRegister('NavbarTitle', NavbarTitle);
