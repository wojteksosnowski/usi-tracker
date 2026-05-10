// view-dashboard.jsx — dashboard z mapą, wykresami, podsumowaniem

function DashboardGrid({ accent, dark, hereApiKey }) {
  const {
    React, USI_CATEGORIES, ratingStatus, avgRating,
    CategoryAvgRow, ProgressBarAnalytics, MiniMap, useDataBus,
    KPI, MapModule, DataGrid, CategoryDots, BaseModule, useApi, Icon, Spinner
  } = window;

  const { bus } = useDataBus();
  const { request } = useApi();
  const investments = bus.visibleInvestments || [];
  const [crawlerStatus, setCrawlerStatus] = React.useState(null);

  React.useEffect(() => {
    request('/api/crawler/status').then(setCrawlerStatus).catch(() => {});
  }, [request]);

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
    <div data-component="DashboardGrid" className="dashboard-content usi-scroll usi-h-full usi-p-24 usi-overflow-auto">
        {/* Row 1: KPI Cards */}
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        {/* Row 2: Charts & Map */}
        <BaseModule title="Średnia ocena per kategoria" icon="chart-bar" style={{ gridColumn: 'span 4' }}>
          <div className="dashboard-category-list">
            {avgByCat.map(c => (
              <CategoryAvgRow key={c.key} label={c.key} avg={c.avg} count={c.n} color={c.color} />
            ))}
          </div>
        </BaseModule>

        <div style={{ gridColumn: 'span 8' }}>
          <MapModule 
            title="Rozkład geograficzny" 
            height={380} 
            data={investments} 
            hereApiKey={hereApiKey} 
          />
        </div>

        {/* Row 3: Top Investments & Crawler Status */}
        <BaseModule title="Top inwestycje wg średniej" icon="award" style={{ gridColumn: 'span 7', minHeight: 400 }}>
          {ranked.length === 0 ? (
            <div className="usi-small usi-p-16" style={{ color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div className="usi-flex-1" style={{ height: '100%' }}>
              <DataGrid 
                data={ranked.slice(0, 10)} 
                rowHeight={60}
                columns={[
                  { 
                    key: 'rank', 
                    label: '#', 
                    width: 30, 
                    align: 'center',
                    render: (_, row) => <span className="usi-mono usi-tiny" style={{ opacity: 0.5 }}>{ranked.indexOf(row) + 1}</span>
                  },
                  {
                    key: 'name',
                    label: 'Inwestycja',
                    render: (val, row) => {
                      const thumb = row.photos && row.photos.length > 0 ? row.photos[0] : null;
                      return (
                        <div className="usi-flex-row usi-gap-12">
                          {thumb
                            ? <img src={thumb} alt="" className="dashboard-top-investment-thumb" />
                            : <div className="dashboard-top-investment-thumb-empty" />
                          }
                          <div className="dashboard-top-investment-info">
                            <div className="dashboard-top-investment-name">{val}</div>
                            <div className="usi-small usi-tiny">{row.developer}</div>
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
                    render: (_, row) => <span className="usi-mono usi-weight-600">{avgRating(row).toFixed(2)}</span>
                  }
                ]}
              />
            </div>
          )}
        </BaseModule>

        <BaseModule title="Status Wędrowca" icon="activity" style={{ gridColumn: 'span 5' }}>
          <CrawlerStatusCard status={crawlerStatus} />
        </BaseModule>

        {/* Row 4: Progress */}
        <BaseModule title="Postęp ocen" icon="check-circle" style={{ gridColumn: 'span 12' }}>
          <ProgressBarAnalytics rated={rated} partial={partial} total={total} />
        </BaseModule>
    </div>
  );
}

function CrawlerStatusCard({ status }) {
  const { React, Icon, Spinner } = window;
  
  if (!status) return <div className="usi-flex-row usi-gap-8 usi-p-16"><Spinner size={14} /> <span className="usi-small">Pobieranie statusu...</span></div>;

  const isRunning = status.running;
  const isPaused = status.paused;

  return (
    <div className="usi-flex-col usi-gap-16">
      <div className="usi-flex-row usi-gap-8 usi-items-center">
        <div className={`usi-dot ${isRunning && !isPaused ? 'usi-bg-success' : 'usi-bg-danger'}`} style={{ width: 8, height: 8 }} />
        <span className="usi-small usi-weight-600">
          {isRunning ? (isPaused ? 'Wstrzymany' : 'Aktywny') : 'Nieaktywny'}
        </span>
      </div>

      {status.current_dev && (
        <div className="usi-card usi-p-12 usi-surface-2 flat">
          <div className="usi-tiny usi-text-secondary usi-m-b-4">Obecnie odwiedza:</div>
          <div className="usi-small usi-weight-600">{status.current_dev}</div>
        </div>
      )}

      {status.next_visit_at && (
        <div className="usi-small usi-text-secondary">
          Następna wizyta: <span className="usi-ink">{new Date(status.next_visit_at).toLocaleString('pl-PL')}</span>
        </div>
      )}

      {status.exploration && (
        <div className="crawler-status-grid">
          {Object.entries(status.exploration).map(([portal, stats]) => (
            <div key={portal} className="crawler-portal-stat">
              <span className="crawler-portal-name">{portal}</span>
              <div className="crawler-stat-row">
                <span className="crawler-stat-label">Strona:</span>
                <span className="crawler-stat-value">{stats.page}/{stats.max_pages}</span>
              </div>
              <div className="crawler-stat-row">
                <span className="crawler-stat-label">Znaleziono:</span>
                <span className="crawler-stat-value">{stats.total_seen}</span>
              </div>
              {stats.new_reg > 0 && (
                <div className="crawler-stat-row usi-text-success">
                  <span className="crawler-stat-label">Nowe:</span>
                  <span className="crawler-stat-value">+{stats.new_reg}</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent }) {
  const { React } = window;
  return (
    <div data-component="KPI" className="usi-card kpi-card" style={{ gridColumn: `span ${col}` }}>
      <div className="usi-tiny kpi-title">{title}</div>
      <div className="usi-mono kpi-value" style={{ color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small kpi-sub">{sub}</div>
      {accent && <div className="kpi-accent-bar" style={{ background: accent }} />}
    </div>
  );
}

Object.assign(window, { DashboardGrid, KPI, CrawlerStatusCard });
