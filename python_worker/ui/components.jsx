// components.jsx — wspólne komponenty UI dla USI

// ─── Spinner ───────────────────────────────────────────────────
function Spinner({ size = 40, stroke = 3 }) {
  return (
    <div data-component="Spinner">
      <style>{`@keyframes usi-spin{to{transform:rotate(360deg)}}`}</style>
      <div style={{ width: size, height: size, border: `${stroke}px solid var(--usi-border)`, borderTopColor: 'var(--usi-accent)', borderRadius: '50%', animation: 'usi-spin 0.8s linear infinite' }} />
    </div>
  );
}

// ─── Logo ──────────────────────────────────────────────────────
// Inline SVG gwiazdki — używana w headerze i jako fallback ikon
function USIStarLogo({ size = 24, color }) {
  // 6-ramienna gwiazdka — geometria z gwizdkaWhite.svg
  return (
    <svg data-component="USIStarLogo" width={size} height={size} viewBox="0 0 48 48" fill="none">
      <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z" fill={color || 'currentColor'} />
    </svg>
  );
}

// ─── StarRating ────────────────────────────────────────────────
// Gwiazdki 0–5 z możliwością klikania. Hover preview, half-star jeśli readonly.
function StarRating({ value = 0, max = 4, size = 22, color, onChange, readonly = false, label }) {
  const [hover, setHover] = React.useState(0);
  const display = hover || value;
  const c = color || 'var(--usi-accent, #1F1C16)';
  return (
    <div data-component="StarRating" role="radiogroup" aria-label={label}
      style={{ display: 'inline-flex', gap: 2, color: c, cursor: readonly ? 'default' : 'pointer' }}
      onMouseLeave={() => setHover(0)}>
      {Array.from({ length: max }).map((_, i) => {
        const idx = i + 1;
        const filled = idx <= Math.floor(display);
        const halfFill = !filled && idx - 0.5 <= display;
        return (
          <button key={i} type="button" disabled={readonly}
            aria-checked={value === idx} role="radio"
            onMouseEnter={() => !readonly && setHover(idx)}
            onClick={() => !readonly && onChange && onChange(value === idx ? 0 : idx)}
            style={{
              border: 'none', background: 'transparent', padding: 0,
              cursor: readonly ? 'default' : 'pointer',
              width: size, height: size, lineHeight: 0,
              transform: hover === idx ? 'scale(1.1)' : 'scale(1)',
              transition: 'transform .12s',
            }}>
            <svg width={size} height={size} viewBox="0 0 48 48" style={{ display: 'block' }}>
              <defs>
                <linearGradient id={`half-${i}-${size}`} x1="0" x2="1" y1="0" y2="0">
                  <stop offset="50%" stopColor={c} />
                  <stop offset="50%" stopColor="var(--usi-star-empty)" />
                </linearGradient>
              </defs>
              <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z"
                fill={filled ? c : (halfFill ? `url(#half-${i}-${size})` : 'var(--usi-star-empty)')}
                style={{ transition: 'fill .12s' }} />
            </svg>
          </button>
        );
      })}
    </div>
  );
}

// ─── CategoryRating — wiersz z nazwą kategorii + StarRating ───
// Wariant chipów: 'stars' | 'chips' | 'segmented' | 'dots'
function CategoryRating({ category, value, onChange, variant = 'stars', size = 'md' }) {
  const sz = size === 'sm' ? 18 : size === 'lg' ? 28 : 22;
  if (variant === 'circles') {
    return (
      <div data-component="CategoryRating" style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
        {[0,1,2,3,4].map(n => {
          const filled = value !== null && n <= value;
          return (
            <button key={n} type="button"
              onClick={() => onChange(value === n ? null : n)}
              title={String(n)}
              style={{
                width: 30, height: 30, borderRadius: '50%', padding: 0,
                border: 'none',
                background: filled ? category.color : 'var(--usi-surface-3)',
                cursor: 'pointer',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                transition: 'background .12s',
                flexShrink: 0,
              }}>
              {filled && (
                <img
                  src={n === 0 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'}
                  width="14" height="16"
                  alt={String(n)}
                  style={{ display: 'block', pointerEvents: 'none' }}
                />
              )}
            </button>
          );
        })}
      </div>
    );
  }
  if (variant === 'chips') {
    return (
      <div data-component="CategoryRating" style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
        {[0,1,2,3,4].map(n => (
          <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
            style={{
              border: '.5px solid var(--usi-border-strong)',
              background: value === n ? category.color : 'var(--usi-surface)',
              color: value === n ? '#fff' : 'var(--usi-ink-2)',
              borderColor: value === n ? category.color : 'var(--usi-border-strong)',
              borderRadius: 6, height: 26, minWidth: 26, padding: '0 6px',
              fontSize: 12, fontWeight: 600, cursor: 'pointer',
              fontFamily: 'inherit',
              transition: 'all .12s',
            }}>{n}</button>
        ))}
      </div>
    );
  }
  if (variant === 'segmented') {
    return (
      <div data-component="CategoryRating" style={{ display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2, position: 'relative' }}>
        {[0,1,2,3,4].map(n => (
          <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
            style={{
              border: 'none', background: value === n ? category.color : 'transparent',
              color: value === n ? '#fff' : 'var(--usi-ink-3)',
              borderRadius: 6, height: 24, width: 28, padding: 0,
              fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
              transition: 'all .12s',
            }}>{n}</button>
        ))}
      </div>
    );
  }
  if (variant === 'dots') {
    return (
      <div data-component="CategoryRating" style={{ display: 'inline-flex', gap: 4 }}>
        {[1,2,3,4].map(n => (
          <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
            style={{
              border: 'none', cursor: 'pointer', padding: 0,
              width: 14, height: 14, borderRadius: '50%',
              background: n <= value ? category.color : 'var(--usi-star-empty)',
              transition: 'background .12s, transform .1s',
            }} />
        ))}
      </div>
    );
  }
  return <StarRating value={value} onChange={onChange} color={category.color} size={sz} label={category.key} />;
}

// ─── Source badge ─────────────────────────────────────────────
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

// ─── StandardCard — wspólna baza dla kart ────────────────────
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
        display: 'flex', 
        flexDirection: 'column', 
        cursor: disabled ? 'default' : 'pointer', 
        height: 320, 
        background: 'var(--usi-surface)',
        position: 'relative',
        opacity: disabled ? 0.7 : 1,
        transition: 'all 0.2s ease',
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

// ─── CategoryStripe — paseczek 6 kategorii w karcie listy ────
function CategoryStripe({ ratings, height = 4 }) {
  return (
    <div data-component="CategoryStripe" style={{ display: 'flex', gap: 1.5, height, borderRadius: 2, overflow: 'hidden' }}>
      {USI_CATEGORIES.map(cat => {
        const v = ratings[cat.key] || 0;
        return (
          <div key={cat.key} style={{ flex: 1, background: 'var(--usi-star-empty)', position: 'relative' }}>
            {v > 0 && (
              <div style={{
                position: 'absolute', inset: 0,
                background: cat.color,
                opacity: 0.3 + (v / 4) * 0.7,
              }} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── CategoryDots — 6 kropek dla kompaktowych kart ───────────
function CategoryDots({ ratings, size = 8 }) {
  return (
    <div data-component="CategoryDots" style={{ display: 'flex', gap: 4 }}>
      {USI_CATEGORIES.map(cat => {
        const v = ratings[cat.key] || 0;
        return (
          <div key={cat.key} title={`${cat.key}: ${v || '—'}`}
            style={{
              width: size, height: size, borderRadius: '50%',
              background: v > 0 ? cat.color : 'transparent',
              border: v > 0 ? 'none' : `1px solid var(--usi-border-strong)`,
              opacity: v > 0 ? 0.4 + (v / 4) * 0.6 : 1,
            }} />
        );
      })}
    </div>
  );
}

// ─── useDarkMode — reaktywny nasłuch na zmianę data-dark ────
function useDarkMode() {
  const [dark, setDark] = React.useState(
    document.documentElement.dataset.dark === '1'
  );
  React.useEffect(() => {
    const obs = new MutationObserver(() =>
      setDark(document.documentElement.dataset.dark === '1')
    );
    obs.observe(document.documentElement, {
      attributes: true, attributeFilter: ['data-dark'],
    });
    return () => obs.disconnect();
  }, []);
  return dark;
}

// ─── ModuleWrapper (Krok B03) ──────────────────────────────────
// Mechanizm spinający istniejące komponenty z architekturą modułów.
// Założenia:
// 1. Otrzymuje kontekst wygenerowany z widoku (np. przez extractModuleContext).
// 2. Mapuje ten kontekst na zmienne zrozumiałe dla zawiniętego komponentu używając specyfikacji JSON.
// 3. Renderuje wewnątrz `BaseModule` dla spójności układu i ErrorBoundary.
function ModuleWrapper({ component: Component, moduleSpec, context, title, icon, height }) {
  const validation = ModuleSchemaValidator.validate(moduleSpec.inputs, context);
  
  if (!validation.valid) {
    return (
      <BaseModule title={title} icon={icon}>
        <div style={{ color: 'var(--usi-danger)', fontSize: 12 }}>
          {validation.errors.map((err, i) => <div key={i}>{err}</div>)}
        </div>
      </BaseModule>
    );
  }

  return (
    <BaseModule title={title} icon={icon}>
      <Component {...validation.aliasedData} height={height} />
    </BaseModule>
  );
}

// ─── MiniMap — fake map z markerami, klik → google maps ─────
// W Kroku B07 zostanie zrefaktoryzowana, teraz dostosowujemy ją by czytała GeoPoint
function MiniMap({ geo, label, height = 140, points = [], hereUrl = '', hereUrlDark = '', coords, containerWidth }) {
  // Kompatybilność wsteczna z coords [lat, lng] dla starych widoków, docelowo używa geo {lat, lng}
  const mapCoords = geo ? [geo.lat, geo.lng] : coords;

  // Symulacja map.invalidateSize() lub zmiana wariantu dla wąskich okien (Krok B06)
  React.useEffect(() => {
    if (containerWidth > 0) {
      console.log(`[MiniMap] containerWidth changed to ${Math.round(containerWidth)}px. (Simulating map.invalidateSize())`);
    }
  }, [containerWidth]);

  if (!mapCoords || mapCoords[0] === 0) return null;

  const url = `https://www.google.com/maps/@${mapCoords[0]},${mapCoords[1]},780m/`;
  const isDark = useDarkMode();
  const imgSrc = (isDark && hereUrlDark) ? hereUrlDark : hereUrl;
  return (
    <a data-component="MiniMap" href={url} target="_blank" rel="noopener" title="Otwórz w Google Maps"
      style={{
        display: 'block', position: 'relative', height, width: '100%',
        borderRadius: 10, overflow: 'hidden', textDecoration: 'none',
        background: 'var(--usi-surface-3)',
        border: '.5px solid var(--usi-border)',
      }}>
      {imgSrc ? (
        <img src={imgSrc} alt="Mapa lokalizacji"
          style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
      ) : (
        <svg viewBox="0 0 300 200" preserveAspectRatio="none"
          style={{ width: '100%', height: '100%', display: 'block' }}>
          <rect x="0" y="0" width="300" height="200" fill="var(--usi-surface-3)" />
          <path d="M0 40 L80 50 L120 30 L200 35 L300 60 L300 0 L0 0 Z" fill="color-mix(in oklab, #7DB951 18%, transparent)" />
          <path d="M0 160 L40 165 L80 158 L120 170 L160 168 L200 175 L240 170 L300 178 L300 200 L0 200 Z" fill="color-mix(in oklab, #3989C6 18%, transparent)" />
          <g stroke="var(--usi-border-strong)" strokeWidth="1.2" fill="none" opacity="0.6">
            <path d="M-10 95 L310 105" /><path d="M-10 70 L310 75" /><path d="M-10 130 L310 138" />
            <path d="M70 -10 L75 210" /><path d="M150 -10 L160 210" /><path d="M225 -10 L230 210" />
          </g>
          <g transform="translate(150,100)">
            <circle r="14" fill="var(--usi-accent, #E5006D)" opacity="0.18" />
            <circle r="7" fill="var(--usi-accent, #E5006D)" stroke="#fff" strokeWidth="2" />
          </g>
        </svg>
      )}
    </a>
  );
}

// ─── ProgressRing — pierścień postępu ocenienia ──────────────
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

// ─── Icon — minimalne ikony liniowe ──────────────────────────
function Icon({ name, size = 16, stroke = 1.6 }) {
  const paths = {
    search: <><circle cx="7" cy="7" r="5"/><path d="M11 11l4 4"/></>,
    filter: <path d="M2 4h12M4 8h8M6 12h4"/>,
    grid: <><rect x="2" y="2" width="5" height="5"/><rect x="9" y="2" width="5" height="5"/><rect x="2" y="9" width="5" height="5"/><rect x="9" y="9" width="5" height="5"/></>,
    list: <><path d="M2 4h12M2 8h12M2 12h12"/></>,
    chevron: <path d="M5 3l4 4-4 4"/>,
    chevronDown: <path d="M3 5l4 4 4-4"/>,
    chevronLeft: <path d="M11 13L5 7l6-6"/>,
    arrow: <><path d="M3 8h10M9 4l4 4-4 4"/></>,
    trash: <><path d="M3 4h10M5 4V2h6v2M4 4l1 10h6l1-10"/></>,
    eye: <><path d="M2 8s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z"/><circle cx="8" cy="8" r="2"/></>,
    check: <path d="M3 8l3 3 7-7"/>,
    close: <path d="M3 3l10 10M13 3L3 13"/>,
    star: <path d="M8 2l1.8 4 4.2.4-3.2 2.8 1 4.4L8 11.4 4.2 13.6l1-4.4L2 6.4l4.2-.4z"/>,
    map: <><path d="M2 4l4-2 4 2 4-2v10l-4 2-4-2-4 2z"/><path d="M6 2v10M10 4v10"/></>,
    plus: <path d="M8 3v10M3 8h10"/>,
    sparkle: <><path d="M8 1v3M8 12v3M1 8h3M12 8h3M3 3l2 2M11 11l2 2M3 13l2-2M11 5l2-2"/></>,
    grip: <><circle cx="6" cy="4" r="1"/><circle cx="10" cy="4" r="1"/><circle cx="6" cy="8" r="1"/><circle cx="10" cy="8" r="1"/><circle cx="6" cy="12" r="1"/><circle cx="10" cy="12" r="1"/></>,
    sort: <><path d="M5 3v10M3 11l2 2 2-2"/><path d="M11 13V3M9 5l2-2 2 2"/></>,
    undo: <><path d="M3 7h7a3 3 0 010 6H6"/><path d="M5 4L2 7l3 3"/></>,
    info: <><circle cx="8" cy="8" r="6"/><path d="M8 7v4M8 5h.01"/></>,
    menu: <><path d="M2 4h12M2 8h12M2 12h12"/></>,
    download: <><path d="M8 2v10M4 8l4 4 4-4"/></>,
  };
  return (
    <svg data-component="Icon" width={size} height={size} viewBox="0 0 16 16" fill="none"
      stroke="currentColor" strokeWidth={stroke} strokeLinecap="round" strokeLinejoin="round">
      {paths[name]}
    </svg>
  );
}

// ─── UsiStarScore — gwiazdkowa reprezentacja oceny złożonej ──
function UsiStarScore({ score }) {
  if (score === null || score === undefined) return null;
  let nFull = Math.floor(score);
  const frac = score - nFull;
  let fracChar = null;
  if (frac >= 0.875) {
    nFull += 1;
  } else if (frac >= 0.625) {
    fracChar = '¾';
  } else if (frac >= 0.375) {
    fracChar = '½';
  } else if (frac >= 0.125) {
    fracChar = '¼';
  }
  const Star = ({ opacity = 1 }) => (
    <svg width={15} height={15} viewBox="0 0 16 16" fill="currentColor" style={{ display: 'block', opacity }}>
      <path d="M8 2l1.8 4 4.2.4-3.2 2.8 1 4.4L8 11.4 4.2 13.6l1-4.4L2 6.4l4.2-.4z" />
    </svg>
  );
  return (
    <div data-component="UsiStarScore" style={{ display: 'inline-flex', alignItems: 'center', gap: 1, color: 'var(--usi-accent)' }}>
      {Array.from({ length: nFull }).map((_, i) => <Star key={i} />)}
      {fracChar && (
        <>
          <Star opacity={0.3} />
          <span style={{ fontSize: 12, fontWeight: 600, lineHeight: 1, marginLeft: 1 }}>{fracChar}</span>
        </>
      )}
    </div>
  );
}

// ─── Hamburger / NavDrawer — wspólne dla wszystkich widoków ──
function NavMenuButton({ onClick, label = 'Menu' }) {
  return (
    <button data-component="NavMenuButton" className="usi-btn ghost icon" onClick={onClick} title={label} aria-label={label}>
      <Icon name="menu" size={18} />
    </button>
  );
}

function NavDrawer({ current = 'list', onClose, onNav, dark, onToggleTheme }) {
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
      {/* Backdrop for closing */}
      <div 
        data-component="NavDrawer-Backdrop"
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 850,
          background: 'rgba(0,0,0,0.1)',
        }} 
      />
      <aside 
        data-component="NavDrawer" 
        style={{
          position: 'absolute', top: '100%', left: 0, width: 280,
          background: 'var(--usi-surface)',
          borderRight: '.5px solid var(--usi-border)',
          borderBottom: '.5px solid var(--usi-border)',
          display: 'flex', flexDirection: 'column',
          boxShadow: '0 12px 24px rgba(0,0,0,0.08)',
          zIndex: 860,
          animation: 'usi-slide-down 0.2s ease-out forwards',
          maxHeight: 'calc(100vh - 60px)',
        }}
      >
        <style>{`
          @keyframes usi-slide-down {
            from { transform: translateY(-10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
          }
        `}</style>
        
        <nav style={{ flex: 1, padding: '12px 10px', overflow: 'auto' }} className="usi-scroll">
          {items.map(it => {
            const active = it.id === current;
            return (
              <button key={it.id} onClick={() => { if (onNav) onNav(it.id); onClose(); }}
                style={{
                  display: 'flex', alignItems: 'center', gap: 12, width: '100%',
                  padding: '10px 12px', borderRadius: 8, border: 'none', textAlign: 'left',
                  background: active ? 'var(--usi-surface-2)' : 'transparent',
                  color: active ? 'var(--usi-ink)' : 'var(--usi-ink-2)',
                  cursor: 'pointer', marginBottom: 2, fontFamily: 'inherit',
                }}>
                <span style={{
                  width: 28, height: 28, borderRadius: 6,
                  background: active ? 'var(--usi-accent)' : 'var(--usi-surface-3)',
                  color: active ? '#fff' : 'var(--usi-ink-3)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
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
        
        <div style={{ padding: '12px', borderTop: '.5px solid var(--usi-border)', background: 'var(--usi-surface-2)' }}>
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
        </div>
      </aside>
    </>
  );
}

// ─── WeightedUsiScore — duża ocena dla HeroBand ────────────────
function WeightedUsiScore({ score, size = 40 }) {
  if (score === null || score === undefined) return null;
  let nFull = Math.floor(score);
  const frac = score - nFull;
  let fracChar = null;
  if (frac >= 0.875) {
    nFull += 1;
  } else if (frac >= 0.625) {
    fracChar = '¾';
  } else if (frac >= 0.375) {
    fracChar = '½';
  } else if (frac >= 0.125) {
    fracChar = '¼';
  }
  return (
    <div data-component="WeightedUsiScore" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <div style={{
        width: size, height: size, borderRadius: '50%',
        background: 'var(--usi-accent)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 4px 12px rgba(229, 0, 109, 0.15)',
        flexShrink: 0,
      }}>
        <img 
          src={score < 0.5 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'} 
          width={size * 0.55} height={size * 0.55} 
          alt="USI"
        />
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
        <div style={{ fontSize: size * 0.55, fontWeight: 800, color: 'var(--usi-ink)' }}>
          {nFull}{fracChar && <span style={{ fontSize: '0.65em', verticalAlign: 'top', marginLeft: 1 }}>{fracChar}</span>}
          <span style={{ fontSize: '0.5em', color: 'var(--usi-ink-4)', fontWeight: 600, marginLeft: 3 }}>/ 4</span>
        </div>
        <div className="usi-tiny" style={{ opacity: 0.5, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 9 }}>Ważona USI</div>
      </div>
    </div>
  );
}

// ─── Moduły (BaseModule & ErrorBoundary) ───────────────────────
class ModuleErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{ padding: 16, border: '1px dashed var(--usi-danger)', borderRadius: 12, backgroundColor: 'var(--usi-surface-2)', color: 'var(--usi-danger)', fontSize: 13, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <strong>Moduł niedostępny</strong>
          <span style={{ fontSize: 11, opacity: 0.8, fontFamily: 'monospace' }}>{this.state.error?.message || 'Błąd renderowania'}</span>
        </div>
      );
    }
    return this.props.children;
  }
}

function BaseModule({ title, icon, children, errorFallback, style }) {
  const containerRef = React.useRef(null);
  const [containerWidth, setContainerWidth] = React.useState(0);

  React.useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        // Prevent layout thrashing loops if possible
        window.requestAnimationFrame(() => {
          setContainerWidth(entry.contentRect.width);
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  const enhancedChildren = React.Children.map(children, child => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, { containerWidth });
    }
    return child;
  });

  return (
    <div ref={containerRef} className="usi-card module-card" style={{ display: 'flex', flexDirection: 'column', minHeight: 100, ...style }}>
      {title && (
        <div style={{ padding: '12px 16px', borderBottom: '.5px solid var(--usi-border)', display: 'flex', alignItems: 'center', gap: 8 }}>
          {icon && <Icon name={icon} size={16} color="var(--usi-ink-3)" />}
          <span className="usi-h3" style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--usi-ink-2)' }}>{title}</span>
        </div>
      )}
      <div style={{ flex: 1, padding: 16, display: 'flex', flexDirection: 'column', position: 'relative' }}>
        <ModuleErrorBoundary fallback={errorFallback}>
          {enhancedChildren}
        </ModuleErrorBoundary>
      </div>
    </div>
  );
}

function SkeletonModule({ shouldThrow = false }) {
  if (shouldThrow) {
    throw new Error("Sztuczny błąd wygenerowany dla testu ErrorBoundary");
  }
  return (
    <BaseModule title="Skeleton Test" icon="box">
      <div style={{ flex: 1, backgroundColor: 'var(--usi-surface-3)', borderRadius: 8, animation: 'pulse 1.5s infinite ease-in-out' }} />
      <style>{`
        @keyframes pulse {
          0% { opacity: 0.5; }
          50% { opacity: 0.8; }
          100% { opacity: 0.5; }
        }
      `}</style>
    </BaseModule>
  );
}

// ─── System Typów dla Modułów (B02) ────────────────────────────
const ModuleTypes = {
  RecordSet: 'RecordSet', // Tablica rekordów inwestycji
  GeoPoint: 'GeoPoint',   // { lat: number, lng: number }
  Rating: 'Rating',       // { value: number, count: number }
  Color: 'Color',         // String hex/rgb
  Number: 'Number',       // Liczba
};

class ModuleSchemaValidator {
  static validate(schema, data) {
    const result = { valid: true, errors: [], aliasedData: {} };
    for (const [key, spec] of Object.entries(schema)) {
      const sourceKey = spec.from || key;
      const value = data[sourceKey];
      if (value === undefined && spec.required) {
        result.valid = false;
        result.errors.push(`Missing required field: ${sourceKey} for module input: ${key}`);
      } else if (value !== undefined) {
        if (spec.type === ModuleTypes.GeoPoint && (typeof value.lat !== 'number' || typeof value.lng !== 'number')) {
          result.valid = false; result.errors.push(`Invalid GeoPoint for ${sourceKey}`);
        } else if (spec.type === ModuleTypes.RecordSet && !Array.isArray(value)) {
          result.valid = false; result.errors.push(`Invalid RecordSet for ${sourceKey}`);
        }
        result.aliasedData[key] = value;
      }
    }
    return result;
  }
}

// Przykładowa specyfikacja (i test walidacji w konsoli)
const exampleModuleJSON = {
  inputs: {
    center: { type: ModuleTypes.GeoPoint, required: true, from: 'currentGeo' },
    items: { type: ModuleTypes.RecordSet, required: false, from: 'visibleInvestments' }
  }
};
console.log("ModuleSchema Test:", ModuleSchemaValidator.validate(exampleModuleJSON.inputs, { currentGeo: { lat: 52.2, lng: 21.0 } }));

Object.assign(window, {
  Spinner, USIStarLogo, StarRating, CategoryRating, SourceBadge, StandardCard,
  CategoryStripe, CategoryDots, MiniMap, ProgressRing, Icon,
  NavDrawer, NavMenuButton, UsiStarScore, WeightedUsiScore,
  ModuleErrorBoundary, BaseModule, SkeletonModule,
  ModuleTypes, ModuleSchemaValidator, ModuleWrapper
});
