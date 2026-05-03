// view-dashboard.jsx — dashboard z mapą, wykresami, podsumowaniem

function DashboardGrid({ investments = [], onNav = () => {}, accent, dark, onToggleTheme, hereApiKey }) {
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
    <div data-component="DashboardGrid" className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div data-component="Dashboard-Toolbar" style={{ 
        padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12, 
        borderBottom: '.5px solid var(--usi-border)', background: 'var(--usi-surface)', 
        flexShrink: 0, position: 'relative' 
      }}>
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h1" style={{ margin: 0 }}>Dashboard</h1>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Stan bazy danych</span>
        <div style={{ flex: 1 }} />
        {navOpen && <NavDrawer current="dashboard" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      <div data-component="Dashboard-Content" style={{ padding: 24, display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 16, overflow: 'auto', flex: 1 }} className="usi-scroll">
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        <div data-component="Dashboard-CategoryAvg" className="usi-card" style={{ gridColumn: 'span 6', padding: 16 }}>
          <div className="usi-tiny" style={{ marginBottom: 16 }}>Średnia ocena per kategoria</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {avgByCat.map(c => (
              <CategoryAvgRow key={c.key} label={c.key} avg={c.avg} count={c.n} color={c.color} />
            ))}
          </div>
        </div>

        <div data-component="Dashboard-GeoDistribution" className="usi-card" style={{ gridColumn: 'span 6', gridRow: 'span 2', padding: 16, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
            <span className="usi-tiny">Rozkład geograficzny</span>
            <span className="usi-small">{total} inwestycji</span>
          </div>
          <DashboardMap investments={investments} accent={accent} dark={dark} apiKey={hereApiKey} />
        </div>

        <div data-component="Dashboard-TopInvestments" className="usi-card" style={{ gridColumn: 'span 6', padding: 16 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Top inwestycje wg średniej</div>
          {ranked.length === 0 ? (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ranked.slice(0, 5).map((inv, i) => {
                const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
                return (
                  <div key={inv.slug} data-component="TopInvestment-Row" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
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

        <div data-component="Dashboard-Progress" className="usi-card" style={{ gridColumn: 'span 12', padding: 16 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Postęp ocen</div>
          <ProgressBarAnalytics rated={rated} partial={partial} total={total} />
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent }) {
  return (
    <div data-component="KPI" className="usi-card" style={{ gridColumn: `span ${col}`, padding: 16, position: 'relative', overflow: 'hidden' }}>
      <div className="usi-tiny" style={{ marginBottom: 6 }}>{title}</div>
      <div className="usi-mono" style={{ fontSize: 32, fontWeight: 600, letterSpacing: -0.02, color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small" style={{ marginTop: 2 }}>{sub}</div>
      {accent && <div style={{ position: 'absolute', top: 0, right: 0, width: 4, bottom: 0, background: accent, opacity: 0.5 }} />}
    </div>
  );
}

function DashboardMap({ investments = [], accent, dark, apiKey }) {
  const withCoords = investments.filter(i => i.coords && i.coords[0] !== 0);
  return (
    <div style={{ flex: 1, minHeight: 300, borderRadius: 8, overflow: 'hidden' }}>
        <MiniMap coords={[52.23, 21.01]} height="100%" />
    </div>
  );
}

Object.assign(window, { DashboardGrid });
