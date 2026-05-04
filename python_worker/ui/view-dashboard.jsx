// view-dashboard.jsx — dashboard z mapą, wykresami, podsumowaniem

function DashboardGrid({ accent, dark, hereApiKey }) {
  const {
    React, USI_CATEGORIES, ratingStatus, avgRating,
    CategoryAvgRow, ProgressBarAnalytics, MiniMap, useDataBus
  } = window;

  const { bus } = useDataBus();
  const investments = bus.visibleInvestments || [];

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
    <div data-component="DashboardGrid" className="dashboard-content usi-scroll" style={{ height: '100%', overflowY: 'auto', padding: '24px' }}>
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

        <div data-component="Dashboard-TopInvestments" className="usi-card dashboard-card-half" style={{ display: 'flex', flexDirection: 'column' }}>
          <div className="usi-tiny" style={{ padding: '16px 16px 8px' }}>Top inwestycje wg średniej</div>
          {ranked.length === 0 ? (
            <div className="usi-small" style={{ padding: 16, color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div style={{ flex: 1, minHeight: 300 }}>
              <DataGrid 
                data={ranked.slice(0, 10)} 
                rowHeight={60}
                columns={[
                  { 
                    key: 'rank', 
                    label: '#', 
                    width: 30, 
                    align: 'center',
                    render: (_, row) => <span className="usi-mono" style={{ fontSize: 11, opacity: 0.5 }}>{ranked.indexOf(row) + 1}</span>
                  },
                  {
                    key: 'name',
                    label: 'Inwestycja',
                    render: (val, row) => {
                      const thumb = row.photos && row.photos.length > 0 ? row.photos[0] : null;
                      return (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                          {thumb
                            ? <img src={thumb} alt="" className="dashboard-top-investment-thumb" />
                            : <div className="dashboard-top-investment-thumb-empty" />
                          }
                          <div className="dashboard-top-investment-info">
                            <div className="dashboard-top-investment-name">{val}</div>
                            <div className="usi-small" style={{ fontSize: 11 }}>{row.developer}</div>
                          </div>
                        </div>
                      );
                    }
                  },
                  {
                    key: 'ratings',
                    label: 'Kategorie',
                    align: 'center',
                    render: (val) => <CategoryDots ratings={val || {}} size={6} />
                  },
                  {
                    key: 'avg',
                    label: '★',
                    width: 60,
                    align: 'right',
                    render: (_, row) => <span className="usi-mono" style={{ fontWeight: 600 }}>{avgRating(row).toFixed(2)}</span>
                  }
                ]}
              />
            </div>
          )}
        </div>

        <div data-component="Dashboard-Progress" className="usi-card dashboard-card-full">
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Postęp ocen</div>
          <ProgressBarAnalytics rated={rated} partial={partial} total={total} />
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
  const { MiniMap } = window;
  return (
    <div className="dashboard-map-container">
        <MiniMap coords={[52.23, 21.01]} height="100%" />
    </div>
  );
}

Object.assign(window, { DashboardGrid });
