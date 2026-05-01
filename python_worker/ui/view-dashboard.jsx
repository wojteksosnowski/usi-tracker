// view-dashboard.jsx — dashboard z mapą, wykresami, podsumowaniem

function DashboardGrid({ investments = [], onNav = () => {}, accent }) {
  const [navOpen, setNavOpen] = React.useState(false);
  const total = investments.length;
  const rated = investments.filter(i => ratingStatus(i) === 'done').length;
  const partial = investments.filter(i => ratingStatus(i) === 'partial').length;
  const photos = investments.reduce((a, i) => a + (i.photos ? i.photos.length : 0), 0);
  const toDelete = investments.reduce((a, i) => a + (i.photos_to_delete || 0), 0);
  const avgByCat = USI_CATEGORIES.map(cat => {
    const vs = investments.map(i => ((i.ratings || {})[cat.key] || 0)).filter(v => v > 0);
    return { ...cat, avg: vs.length ? vs.reduce((a, b) => a + b, 0) / vs.length : 0, n: vs.length };
  });
  const ranked = [...investments]
    .filter(i => ratingStatus(i) !== 'none')
    .sort((a, b) => avgRating(b) - avgRating(a));
  const ratedWithAvg = investments.filter(i => avgRating(i) > 0);
  const globalAvg = ratedWithAvg.length
    ? ratedWithAvg.reduce((a, i) => a + avgRating(i), 0) / ratedWithAvg.length
    : 0;

  return (
    <div className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12, borderBottom: '.5px solid var(--usi-border)', background: 'var(--usi-surface)', flexShrink: 0 }}>
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h1" style={{ margin: 0 }}>Dashboard</h1>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Stan bazy danych</span>
        <div style={{ flex: 1 }} />
      </div>
      {navOpen && <NavDrawer current="dashboard" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} />}
      <div style={{ padding: 24, display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 16, overflow: 'auto', flex: 1 }} className="usi-scroll">
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        <div className="usi-card" style={{ gridColumn: 'span 6', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 16 }}>Średnia ocena per kategoria</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {avgByCat.map(c => (
              <div key={c.key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 100, fontSize: 13, fontWeight: 500 }}>{c.key}</div>
                <div style={{ flex: 1, height: 20, background: 'var(--usi-surface-3)', borderRadius: 4, position: 'relative' }}>
                  <div style={{
                    height: '100%', width: `${(c.avg / 5) * 100}%`,
                    background: c.color, borderRadius: 4, transition: 'width .4s',
                  }} />
                  <span className="usi-mono" style={{
                    position: 'absolute', right: 8, top: 1, fontSize: 11, fontWeight: 600,
                    color: c.avg > 2.5 ? '#fff' : 'var(--usi-ink)',
                  }}>{c.n > 0 ? c.avg.toFixed(2) : '—'}</span>
                </div>
                <div style={{ width: 36, textAlign: 'right' }} className="usi-small">n={c.n}</div>
                <StarRating value={c.avg} readonly size={14} color={c.color} />
              </div>
            ))}
          </div>
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 6', padding: 18, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
            <span className="usi-tiny">Rozkład geograficzny</span>
            <span className="usi-small">{total} inwestycji</span>
          </div>
          <DashboardMap investments={investments} accent={accent} />
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 5', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Postęp ocen</div>
          {total > 0 ? (
            <>
              <div style={{ display: 'flex', height: 36, borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ width: `${rated/total*100}%`, background: 'var(--usi-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                  {rated > 0 ? rated : ''}
                </div>
                <div style={{ width: `${partial/total*100}%`, background: '#F39200', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                  {partial > 0 ? partial : ''}
                </div>
                <div style={{ flex: 1, background: 'var(--usi-surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--usi-ink-3)', fontSize: 12, fontWeight: 600 }}>
                  {total - rated - partial > 0 ? total - rated - partial : ''}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 14, marginTop: 12, flexWrap: 'wrap' }}>
                <Legend color="var(--usi-success)" label="Pełne" />
                <Legend color="#F39200" label="Częściowe" />
                <Legend color="var(--usi-surface-3)" label="Nieocenione" />
              </div>
            </>
          ) : (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak danych</div>
          )}
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 7', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Top inwestycje wg średniej</div>
          {ranked.length === 0 ? (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ranked.slice(0, 5).map((inv, i) => {
                const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
                return (
                  <div key={inv.slug} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className="usi-mono" style={{ width: 18, color: 'var(--usi-ink-4)', fontSize: 12 }}>{i+1}</span>
                    {thumb
                      ? <img src={thumb} alt="" style={{ width: 36, height: 36, borderRadius: 6, objectFit: 'cover' }} />
                      : <div style={{ width: 36, height: 36, borderRadius: 6, background: 'var(--usi-surface-3)' }} />
                    }
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{inv.name}</div>
                      <div className="usi-small">{inv.developer}</div>
                    </div>
                    <CategoryDots ratings={inv.ratings || {}} size={6} />
                    <span className="usi-mono" style={{ fontWeight: 600, minWidth: 36, textAlign: 'right' }}>★ {avgRating(inv).toFixed(2)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent }) {
  return (
    <div className="usi-card" style={{ gridColumn: `span ${col}`, padding: 18, position: 'relative', overflow: 'hidden' }}>
      <div className="usi-tiny" style={{ marginBottom: 6 }}>{title}</div>
      <div className="usi-mono" style={{ fontSize: 32, fontWeight: 600, letterSpacing: -0.02, color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small" style={{ marginTop: 2 }}>{sub}</div>
      {accent && <div style={{ position: 'absolute', top: 0, right: 0, width: 4, bottom: 0, background: accent, opacity: 0.5 }} />}
    </div>
  );
}

function Legend({ color, label }) {
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
      <span style={{ width: 10, height: 10, borderRadius: 2, background: color }} /> {label}
    </span>
  );
}

function DashboardMap({ investments = [], accent }) {
  const proj = (lat, lon) => {
    if (!lat || !lon) return null;
    // Flexible bounds based on actual data
    const x = 10 + ((lon - 14.0) / (24.0 - 14.0)) * 580;
    const y = 300 - ((lat - 49.0) / (55.0 - 49.0)) * 290;
    return { x: Math.max(10, Math.min(590, x)), y: Math.max(10, Math.min(290, y)) };
  };
  const withCoords = investments.filter(i => i.coords && i.coords[0] !== 0);
  return (
    <div style={{ flex: 1, position: 'relative', minHeight: 240 }}>
      <svg viewBox="0 0 600 300" preserveAspectRatio="xMidYMid meet"
        style={{ width: '100%', height: '100%', display: 'block', background: 'var(--usi-surface-3)', borderRadius: 8 }}>
        <rect x="0" y="0" width="600" height="300" fill="var(--usi-surface-3)" />
        <g stroke="var(--usi-border-strong)" strokeWidth="0.8" fill="none" opacity="0.4">
          {Array.from({length:7}).map((_,i)=><path key={i} d={`M-10 ${30+i*40} L610 ${30+i*40+5}`} />)}
          {Array.from({length:9}).map((_,i)=><path key={i} d={`M${30+i*70} -10 L${36+i*70} 310`} />)}
        </g>
        {withCoords.length === 0 && (
          <text x="300" y="150" textAnchor="middle" fontSize="12" fill="var(--usi-ink-4)">Brak danych geolokalizacyjnych</text>
        )}
        {withCoords.map((inv, idx) => {
          const p = proj(inv.coords[0], inv.coords[1]);
          if (!p) return null;
          const v = avgRating(inv);
          const r = 6 + (v ? (v / 5) * 8 : 0);
          const color = ratingStatus(inv) === 'done' ? 'var(--usi-success)'
            : ratingStatus(inv) === 'partial' ? '#F39200' : 'var(--usi-ink-4)';
          return (
            <g key={inv.slug} transform={`translate(${p.x},${p.y})`}>
              <title>{inv.name}</title>
              <circle r={r + 4} fill={color} opacity="0.18" />
              <circle r={r} fill={color} stroke="var(--usi-surface)" strokeWidth="1.5" />
              <text y="3" textAnchor="middle" fontSize="9" fontWeight="600" fill="#fff">
                {v > 0 ? v.toFixed(1) : '·'}
              </text>
            </g>
          );
        })}
      </svg>
      <div style={{ position: 'absolute', bottom: 8, right: 8, padding: '4px 8px', borderRadius: 6, background: 'var(--usi-overlay-strong)', backdropFilter: 'blur(8px)', fontSize: 10, color: 'var(--usi-ink-3)' }}>
        rozmiar = średnia ocen
      </div>
    </div>
  );
}

Object.assign(window, { DashboardGrid });
