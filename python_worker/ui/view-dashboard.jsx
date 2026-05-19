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
  const [doktorStatus, setDoktorStatus] = React.useState(null);

  React.useEffect(() => {
    request('/api/crawler/status').then(setCrawlerStatus).catch(() => {});
    request('/api/doktor/status').then(setDoktorStatus).catch(() => {});
  }, [request]);

  // 1:1 map — measure wrapper width, pass it as height
  const mapWrapRef = React.useRef(null);
  const [mapHeight, setMapHeight] = React.useState(400);
  React.useEffect(() => {
    if (!mapWrapRef.current) return;
    const ro = new ResizeObserver(entries => {
      const w = Math.round(entries[0].contentRect.width);
      if (w > 0) setMapHeight(w);
    });
    ro.observe(mapWrapRef.current);
    return () => ro.disconnect();
  }, []);

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

  const unreviewedCount = bus.unreviewedCount || 0;

  return (
    <div data-component="DashboardGrid" className="dashboard-content usi-scroll usi-h-full usi-p-24 usi-overflow-auto">
        {/* Row 1: KPI Cards */}
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI
          title="Nieprzejrzane"
          value={unreviewedCount}
          sub="nowości do weryfikacji"
          col={3}
          accent="var(--usi-accent)"
          onClick={() => {
            setVariable('view', 'list');
            setVariable('filters.onlyUnreviewed', true);
          }}
        />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        {/* Row 2: Charts & Map — 3+1 kolumny */}
        <BaseModule title="Średnia ocena per kategoria" icon="chart-bar" style={{ gridColumn: 'span 9' }}>
          <div className="dashboard-category-list">
            {avgByCat.map(c => (
              <CategoryAvgRow key={c.key} label={c.key} avg={c.avg} count={c.n} color={c.color} />
            ))}
          </div>
        </BaseModule>

        <div ref={mapWrapRef} style={{ gridColumn: 'span 3' }}>
          <MapModule
            title="Rozkład geograficzny"
            height={mapHeight}
            data={investments}
            hereApiKey={hereApiKey}
          />
        </div>

        {/* Row 3: Top + Wędrowiec + Doktor + Postęp — 1+1+1+1 kolumny */}
        <BaseModule title="Top inwestycje wg średniej" icon="award" style={{ gridColumn: 'span 3', minHeight: 360 }}>
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
                    width: 24,
                    align: 'center',
                    render: (_, row) => <span className="usi-mono usi-tiny" style={{ opacity: 0.5 }}>{ranked.indexOf(row) + 1}</span>
                  },
                  {
                    key: 'name',
                    label: 'Inwestycja',
                    render: (val, row) => (
                      <div className="dashboard-top-investment-info">
                        <div className="dashboard-top-investment-name">{val}</div>
                        <div className="usi-small usi-tiny">{row.developer}</div>
                      </div>
                    )
                  },
                  {
                    key: 'avg',
                    label: '★',
                    width: 48,
                    align: 'right',
                    render: (_, row) => <span className="usi-mono usi-weight-600">{avgRating(row).toFixed(2)}</span>
                  }
                ]}
              />
            </div>
          )}
        </BaseModule>

        <BaseModule title="Wędrowiec" icon="activity" style={{ gridColumn: 'span 3' }}>
          <CrawlerStatusCard status={crawlerStatus} />
        </BaseModule>

        <BaseModule title="Doktor" icon="search" style={{ gridColumn: 'span 3' }}>
          <DoktorStatusCard status={doktorStatus} />
        </BaseModule>

        <BaseModule title="Postęp ocen" icon="check-circle" style={{ gridColumn: 'span 3' }}>
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
  const inWizyta = !!status.current_dev;
  const inEksploracja = status.exploration && Object.keys(status.exploration).length > 0;

  return (
    <div className="usi-flex-col usi-gap-12 usi-p-4">
      <div className="usi-flex-row usi-gap-8 usi-items-center">
        <div className={`usi-dot ${isRunning && !isPaused ? 'usi-bg-success' : 'usi-bg-danger'}`} style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0 }} />
        <span className="usi-small usi-weight-600">
          {isRunning ? (isPaused ? 'Wstrzymany' : 'Aktywny') : 'Nieaktywny'}
        </span>
        {isRunning && !isPaused && (
          <span className="usi-tiny usi-text-secondary" style={{ marginLeft: 4 }}>
            {inWizyta ? '· Tryb Wizyta' : inEksploracja ? '· Tryb Eksploracja' : '· Czeka'}
          </span>
        )}
      </div>

      {inWizyta && (
        <div className="usi-card usi-p-10 usi-surface-2 flat">
          <div className="usi-tiny usi-text-secondary usi-m-b-2">Odwiedza dewelopera:</div>
          <div className="usi-small usi-weight-600">{status.current_dev}</div>
          {status.next_visit_at && (
            <div className="usi-tiny usi-text-secondary" style={{ marginTop: 4 }}>
              Następna: {new Date(status.next_visit_at).toLocaleTimeString('pl-PL', { hour: '2-digit', minute: '2-digit' })}
            </div>
          )}
        </div>
      )}

      {!inWizyta && status.next_visit_at && (
        <div className="usi-tiny usi-text-secondary">
          Następna wizyta: <span className="usi-ink">{new Date(status.next_visit_at).toLocaleString('pl-PL', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })}</span>
        </div>
      )}

      {inEksploracja && (
        <div>
          <div className="usi-tiny usi-text-secondary usi-m-b-6">Przeszukuje katalogi portali:</div>
          <div className="crawler-status-grid">
            {Object.entries(status.exploration).map(([portal, stats]) => (
              <div key={portal} className="crawler-portal-stat">
                <span className="crawler-portal-name">{portal.toUpperCase()}</span>
                <div className="crawler-stat-row">
                  <span className="crawler-stat-label">Strona</span>
                  <span className="crawler-stat-value">{stats.page}/{stats.max_pages}</span>
                </div>
                <div className="crawler-stat-row">
                  <span className="crawler-stat-label">Widziano</span>
                  <span className="crawler-stat-value">{stats.total_seen}</span>
                </div>
                {stats.new_reg > 0 && (
                  <div className="crawler-stat-row" style={{ color: 'var(--usi-success)' }}>
                    <span className="crawler-stat-label">Nowi</span>
                    <span className="crawler-stat-value">+{stats.new_reg}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function DoktorStatusCard({ status }) {
  const { React, Spinner } = window;

  if (!status) return <div className="usi-flex-row usi-gap-8 usi-p-16"><Spinner size={14} /> <span className="usi-small">Pobieranie statusu...</span></div>;

  const isRunning = status.running;
  const queueDone = status.total_indexed > 0
    ? status.total_indexed - status.queue_remaining
    : 0;
  const pct = status.total_indexed > 0
    ? Math.round((queueDone / status.total_indexed) * 100)
    : 0;

  const lastRefreshStr = status.last_refresh
    ? new Date(status.last_refresh).toLocaleString('pl-PL', { hour: '2-digit', minute: '2-digit', day: 'numeric', month: 'short' })
    : null;

  return (
    <div className="usi-flex-col usi-gap-12 usi-p-4">
      <div className="usi-flex-row usi-gap-8 usi-items-center">
        <div className={`usi-dot ${isRunning ? 'usi-bg-success' : 'usi-bg-danger'}`} style={{ width: 8, height: 8, borderRadius: '50%', flexShrink: 0 }} />
        <span className="usi-small usi-weight-600">
          {isRunning ? 'Aktywny' : 'Nieaktywny'}
        </span>
        <span className="usi-tiny usi-text-secondary">· co {status.tick_seconds}s</span>
      </div>

      {status.total_indexed > 0 && (
        <div>
          <div className="usi-flex-row usi-gap-8" style={{ justifyContent: 'space-between', marginBottom: 4 }}>
            <span className="usi-tiny usi-text-secondary">Zbadano deweloperów</span>
            <span className="usi-tiny usi-weight-600">{queueDone} / {status.total_indexed}</span>
          </div>
          <div style={{ height: 4, borderRadius: 2, background: 'var(--usi-surface-3)', overflow: 'hidden' }}>
            <div style={{ height: '100%', width: `${pct}%`, background: 'var(--usi-accent)', borderRadius: 2, transition: 'width 0.3s' }} />
          </div>
          <div className="usi-tiny usi-text-secondary" style={{ marginTop: 4 }}>{pct}% cyklu</div>
        </div>
      )}

      {lastRefreshStr && (
        <div className="usi-tiny usi-text-secondary">
          Indeks odświeżony: <span className="usi-ink">{lastRefreshStr}</span>
          <span style={{ opacity: 0.6 }}> (co {status.index_refresh_hours}h)</span>
        </div>
      )}
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent, onClick }) {
  const { React } = window;
  return (
    <div
      data-component="KPI"
      className={`usi-card kpi-card ${onClick ? 'clickable' : ''}`}
      style={{ gridColumn: `span ${col}`, cursor: onClick ? 'pointer' : 'default' }}
      onClick={onClick}
    >
      <div className="usi-tiny kpi-title">{title}</div>
      <div className="usi-mono kpi-value" style={{ color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small kpi-sub">{sub}</div>
      {accent && <div className="kpi-accent-bar" style={{ background: accent }} />}
    </div>
  );
}

Object.assign(window, { DashboardGrid, KPI, CrawlerStatusCard, DoktorStatusCard });
