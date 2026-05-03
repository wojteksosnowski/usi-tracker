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
    <div data-component="DashboardGrid" className="usi-app dashboard-grid">
      <div data-component="Dashboard-Toolbar" className="dashboard-toolbar">
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h1" style={{ margin: 0 }}>Dashboard</h1>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Stan bazy danych</span>
        <div style={{ flex: 1 }} />
        {navOpen && <NavDrawer current="dashboard" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      <div data-component="Dashboard-Content" className="dashboard-content usi-scroll">
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        <div data-component="Dashboard-CategoryAvg" className="usi-card dashboard-card-half">
          <div className="usi-tiny dashboard-section-title">Średnia ocena per kategoria</div>
          <div className="dashboard-category-list">
            {avgByCat.map(c => (
              <CategoryAvgRow key={c.key} label={c.key} avg={c.avg} count={c.n} color={c.color} />
            ))}
          </div>
        </div>

        <div data-component="Dashboard-GeoDistribution" className="usi-card dashboard-geo-distribution">
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
            <span className="usi-tiny">Rozkład geograficzny</span>
            <span className="usi-small">{total} inwestycji</span>
          </div>
          <DashboardMap investments={investments} accent={accent} dark={dark} apiKey={hereApiKey} />
        </div>

        <div data-component="Dashboard-TopInvestments" className="usi-card dashboard-card-half">
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Top inwestycje wg średniej</div>
          {ranked.length === 0 ? (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div className="dashboard-top-investments-list">
              {ranked.slice(0, 5).map((inv, i) => {
                const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
                return (
                  <div key={inv.slug} data-component="TopInvestment-Row" className="dashboard-top-investment-row">
                    <span className="usi-mono dashboard-top-investment-rank">{i+1}</span>
                    {thumb
                      ? <img src={thumb} alt="" className="dashboard-top-investment-thumb" />
                      : <div className="dashboard-top-investment-thumb-empty" />
                    }
                    <div className="dashboard-top-investment-info">
                      <div className="dashboard-top-investment-name">{inv.name}</div>
                      <div className="usi-small">{inv.developer}</div>
                    </div>
                    <CategoryDots ratings={inv.ratings || {}} size={6} />
                    <span className="usi-mono dashboard-top-investment-avg">★ {avgRating(inv).toFixed(2)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div data-component="Dashboard-Progress" className="usi-card dashboard-card-full">
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Postęp ocen</div>
          <ProgressBarAnalytics rated={rated} partial={partial} total={total} />
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent }) {
  return (
    <div data-component="KPI" className="usi-card kpi-card" style={{ gridColumn: `span ${col}` }}>
      <div className="usi-tiny kpi-title">{title}</div>
      <div className="usi-mono kpi-value" style={{ color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small kpi-sub">{sub}</div>
      {accent && <div className="kpi-accent-bar" style={{ background: accent }} />}
    </div>
  );
}

function DashboardMap({ investments = [], accent, dark, apiKey }) {
  const withCoords = investments.filter(i => i.coords && i.coords[0] !== 0);
  return (
    <div className="dashboard-map-container">
        <MiniMap coords={[52.23, 21.01]} height="100%" />
    </div>
  );
}

Object.assign(window, { DashboardGrid });
