// app.jsx — USI Tracker SPA

(function() {
  const { React, usiRegister } = window;

  const LoadingScreen = () => {
    const { Spinner } = window;
    return (
      <div data-component="LoadingScreen" className="app-loading-screen">
        <Spinner />
        <span className="usi-small">Ładowanie danych…</span>
      </div>
    );
  };
  usiRegister('LoadingScreen', LoadingScreen);

  const EmptyScreen = ({ onFetch, fetching, fetchCount }) => {
    const { Spinner, Icon } = window;
    return (
      <div data-component="EmptyScreen" className="app-empty-screen">
        <div className="empty-screen-icon">
          <svg width="64" height="64" viewBox="0 0 48 48" fill="none">
            <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z" fill="currentColor" />
          </svg>
        </div>
        <h2 className="usi-h1" style={{ margin: 0 }}>Baza jest pusta</h2>
        <p className="usi-body empty-screen-text">
          Brak inwestycji w bazie. Pobierz przykładowe rekordy z RynekPierwotny.pl.
        </p>
        {fetching ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, color: 'var(--usi-ink-3)' }}>
            <Spinner size={20} stroke={2} />
            <span className="usi-small">Pobieram dane… {fetchCount > 0 ? `(${fetchCount} rekordów)` : ''}</span>
          </div>
        ) : (
          <button className="usi-btn" style={{ padding: '10px 24px', fontSize: 14 }} onClick={onFetch}>
            <Icon name="sparkle" size={15} /> Pobierz 50 inwestycji z RP
          </button>
        )}
      </div>
    );
  };
  usiRegister('EmptyScreen', EmptyScreen);

  const App = () => {
    try {
      const {
        Spinner, Icon, ModuleErrorBoundary,
        ViewList, DeveloperListGrid, DeveloperDetail,
        DetailRightPanel, DashboardGrid, ViewDownload,
        ReportsList, ReportDetail, DataBusProvider, useDataBus,
        useInvestments, useDevelopers, useConfig,
        MAIN_CITIES, SOURCES, USI_STATUSES, applyTheme, injectThemeCSS,
        NavbarShell, NavbarTitle, NavbarCounter, ActionBar, NotificationCenter, StatusMessenger,
        GlobalSearch, FilterGroup, FilterChip, NavMenuButton, NavDrawer,
        LoadingScreen, EmptyScreen
      } = window;

      const rootRef = React.useRef(null);
      const [view, setView] = React.useState('list');
      const [navOpen, setNavOpen] = React.useState(false);
      const [selectedInv, setSelectedInv] = React.useState(null);
      const [selectedDev, setSelectedDev] = React.useState(null);
      const [selectedReport, setSelectedReport] = React.useState(null);
      const { refetch } = useInvestments();
      const config = useConfig();
      const [fetching] = React.useState(false);
      const [fetchCount] = React.useState(0);
      const [dark, setDark] = React.useState(false);
      const [mode, setMode] = React.useState('grid');

      const { bus, setVariable } = useDataBus();
      const { 
        investments, developers, loading,
        search, filterDev, filterStatus, activeSources, activeCities,
        visibleInvestments
      } = bus;

      React.useEffect(() => {
        injectThemeCSS();
        if (rootRef.current) applyTheme(rootRef.current, false, '#E5006D');
      }, []);

      const handleToggleTheme = () => {
        const next = !dark;
        setDark(next);
        if (rootRef.current) applyTheme(rootRef.current, next, '#E5006D');
      };

      const handleNav = (v) => {
        setView(v);
        setNavOpen(false);
        if (v !== 'detail') setSelectedInv(null);
        if (v !== 'dev-detail') setSelectedDev(null);
        if (v !== 'report-detail') setSelectedReport(null);
      };

      const toggleSource = (id, isShift) => {
        setVariable('activeSources', prev => {
          const next = new Set(prev);
          if (isShift) return new Set([id]);
          if (next.has(id)) {
            if (next.size > 1) next.delete(id);
          } else {
            next.add(id);
          }
          return next;
        });
      };

      const toggleCity = (city, isShift) => {
        setVariable('activeCities', prev => {
          if (city === null) return new Set();
          const next = new Set(prev);
          if (isShift) return new Set([city]);
          if (next.has(city)) next.delete(city);
          else next.add(city);
          return next;
        });
      };

      const toggleDownloadPortal = (id, isShift) => {
        setVariable('activeDownloadPortals', prev => {
          const next = new Set(prev);
          if (isShift) return new Set([id]);
          if (next.has(id)) {
            if (next.size > 1) next.delete(id);
          } else {
            next.add(id);
          }
          return next;
        });
      };

      if (loading && investments.length === 0) return <div data-component="App" ref={rootRef} className="app-container usi-app"><LoadingScreen /></div>;
      if (!loading && investments.length === 0) return <div data-component="App" ref={rootRef} className="app-container usi-app"><EmptyScreen onFetch={() => {}} fetching={fetching} fetchCount={fetchCount} /></div>;

      const getTitle = () => {
        if (view === 'list') return "Inwestycje";
        if (view === 'developers') return "Deweloperzy";
        if (view === 'dashboard') return "Dashboard";
        if (view === 'download') return "Pobieranie";
        if (view === 'reports') return "Raporty";
        if (view === 'detail') return selectedInv?.name || "Szczegóły";
        if (view === 'dev-detail') return selectedDev?.name || "Szczegóły dewelopera";
        return "USI Tracker";
      };

      const getSubtitle = () => {
        if (view === 'list') return `${visibleInvestments.length} widocznych`;
        if (view === 'developers') return `${developers.length} firm`;
        return "System monitoringu rynku";
      };

      return (
        <div data-component="App" ref={rootRef} className="usi-app-container usi-app">
          <NavbarShell
            left={
              <div className="usi-flex-row usi-gap-12">
                <NavMenuButton onClick={() => setNavOpen(true)} />
                <NavbarTitle title={getTitle()} subtitle={getSubtitle()} />
              </div>
            }
            center={
              bus.appStatus 
                ? <StatusMessenger />
                : (bus.activeJobs || []).length > 0 
                  ? <NotificationCenter /> 
                  : null
            }
            right={
              <div className="usi-flex-row usi-gap-12">
                  <NavbarCounter />
                  <button className="usi-btn ghost icon sm" onClick={handleToggleTheme} title="Przełącz motyw">
                      <Icon name={dark ? 'sparkle' : 'star'} size={16} />
                  </button>
              </div>
            }
          />

          <ActionBar
            left={
              view === 'list' || view === 'developers' ? (
                <div className="usi-action-bar-group">
                  {view === 'list' && (
                    <div className="mode-toggle">
                      <button className="usi-btn icon sm" aria-pressed={mode === 'grid'} onClick={() => setMode('grid')}><Icon name="grid" /></button>
                      <button className="usi-btn icon sm" aria-pressed={mode === 'table'} onClick={() => setMode('table')}><Icon name="list" /></button>
                    </div>
                  )}
                  <GlobalSearch value={search} onChange={v => setVariable('search', v)} placeholder={view === 'list' ? "Szukaj inwestycji..." : "Szukaj dewelopera..."} />
                </div>
              ) : view === 'download' ? (
                <div className="usi-action-bar-group">
                  <div className="mode-toggle">
                    <button className="usi-btn icon sm" aria-pressed={bus.downloadMode === 'grid'} onClick={() => setVariable('downloadMode', 'grid')}><Icon name="grid" /></button>
                    <button className="usi-btn icon sm" aria-pressed={bus.downloadMode === 'table'} onClick={() => setVariable('downloadMode', 'table')}><Icon name="list" /></button>
                  </div>
                  <GlobalSearch 
                    value={bus.downloadSearch || ''} 
                    onChange={v => setVariable('downloadSearch', v)} 
                    placeholder="Filtruj wyniki..." 
                  />
                </div>
              ) : (view !== 'download') ? (
                <button className="usi-btn ghost sm" onClick={() => handleNav('list')}><Icon name="chevronLeft" /> Powrót do listy</button>
              ) : null
            }
            center={
              (view === 'list' || view === 'developers') ? (
                <div className="usi-flex-row usi-gap-24">
                  <FilterGroup label="Źródła">
                    {SOURCES.map(s => (
                      <FilterChip key={s.id} label={s.label} source={s.id} active={activeSources.has(s.id)} color={s.color} onClick={(isShift) => toggleSource(s.id, isShift)} />
                    ))}
                  </FilterGroup>
                  <div className="usi-divider-v" />
                  <FilterGroup label="Miasta">
                    {MAIN_CITIES.map(city => (
                      <FilterChip key={city} label={city} active={activeCities.has(city)} onClick={(isShift) => toggleCity(city, isShift)} />
                    ))}
                    {activeCities.size > 0 && <button className="usi-btn ghost sm" onClick={() => toggleCity(null)}>Reset</button>}
                  </FilterGroup>
                </div>
              ) : view === 'download' ? (
                <FilterGroup label="Opcje">
                  <label className="usi-label-clickable">
                    <input type="checkbox" checked={bus.downloadOnlyNew || false} onChange={e => setVariable('downloadOnlyNew', e.target.checked)} />
                    Tylko nowe
                  </label>
                </FilterGroup>
              ) : null
            }
            right={
              view === 'list' ? (
                <div className="usi-flex-row usi-gap-8">
                  <select className="usi-input sm usi-w-150" value={filterDev} onChange={e => setVariable('filterDev', e.target.value)}>
                    <option value="">Deweloperzy</option>
                    {developers.map(d => <option key={d.developer_slug} value={d.developer_slug}>{d.name}</option>)}
                  </select>
                  <select className="usi-input sm usi-w-120" value={filterStatus} onChange={e => setVariable('filterStatus', e.target.value)}>
                    <option value="">Statusy</option>
                    {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              ) : view === 'download' ? (
                <div className="usi-flex-row usi-gap-16">
                  <FilterGroup label="Portal">
                    {[
                      { id: 'rp', label: 'RynekPierwotny' },
                      { id: 'oto', label: 'Otodom' },
                      { id: 'to', label: 'TabelaOfert' }
                    ].map(p => (
                      <FilterChip 
                        key={p.id} 
                        label={p.label} 
                        active={(bus.activeDownloadPortals || new Set()).has(p.id)} 
                        onClick={(isShift) => toggleDownloadPortal(p.id, isShift)} 
                      />
                    ))}
                  </FilterGroup>
                  <div className="usi-divider-v" />
                  <button className="usi-btn ghost sm" onClick={() => window.usiTriggerScan && window.usiTriggerScan()}>
                    <Icon name="zap" size={14} style={{ marginRight: 4 }} /> Skanuj
                  </button>
                </div>
              ) : (
                <div className="usi-flex-row usi-gap-8">
                  <button className="usi-btn ghost sm" onClick={() => handleNav('dashboard')}>Dashboard</button>
                  <button className="usi-btn ghost sm" onClick={() => handleNav('reports')}>Raporty</button>
                </div>
              )
            }
          />

          <main className="usi-app-main usi-scroll">
            <ModuleErrorBoundary fallback={
              <div className="usi-p-24" style={{ textAlign: 'center' }}>
                <h2 className="usi-h2">Coś poszło nie tak</h2>
                <p className="usi-body">Wystąpił błąd podczas renderowania tego widoku.</p>
                <button className="usi-btn" onClick={() => window.location.reload()}>Odśwież aplikację</button>
              </div>
            }>
              {view === 'list' && (
                <ViewList 
                  onSelectInv={(inv) => { setSelectedInv(inv); setView('detail'); }} 
                  mode={mode} 
                />
              )}

              {view === 'developers' && (
                <DeveloperListGrid
                  developers={developers}
                  onSelectDev={(dev) => { setSelectedDev(dev); setView('dev-detail'); }}
                />
              )}

              {view === 'dashboard' && (
                <DashboardGrid 
                  hereApiKey={config?.hereApiKey} 
                />
              )}

              {view === 'detail' && selectedInv && (
                <DetailRightPanel
                  inv={selectedInv}
                  onBack={() => setView('list')}
                  onUpdateInv={() => refetch()}
                />
              )}

              {view === 'dev-detail' && selectedDev && (
                <DeveloperDetail
                  dev_slug={selectedDev.developer_slug}
                  onBack={() => setView('developers')}
                  onSelectInv={(inv) => { setSelectedInv(inv); setView('detail'); }}
                />
              )}

              {view === 'download' && <ViewDownload />}
              {view === 'reports' && <ReportsList onSelectReport={(r) => { setSelectedReport(r); setView('report-detail'); }} />}
              {view === 'report-detail' && selectedReport && <ReportDetail reportId={selectedReport.id} onBack={() => setView('reports')} />}
            </ModuleErrorBoundary>
          </main>

          {navOpen && <NavDrawer current={view} onClose={() => setNavOpen(false)} onNav={handleNav} dark={dark} onToggleTheme={handleToggleTheme} />}
        </div>
      );
    } catch (err) {
      console.error("CRITICAL APP RENDER ERROR:", err);
      return <div style={{ padding: 40, color: '#c00' }}><h1>Błąd renderowania</h1><pre>{err.stack}</pre></div>;
    }
  }
  usiRegister('App', App);

})();

const renderApp = () => {
  const deps = [
    'React', 'ReactDOM', 'DataBusProvider', 'App'
  ];
  
  const missing = deps.filter(d => window[d] === undefined);
  if (missing.length > 0) {
    if (window._renderAttempts > 50) {
      console.error("Missing UI dependencies after 5s:", missing);
    }
    window._renderAttempts = (window._renderAttempts || 0) + 1;
    setTimeout(renderApp, 100);
    return;
  }
  
  const { ReactDOM, DataBusProvider, App } = window;
  ReactDOM.createRoot(document.getElementById('root')).render(
    <DataBusProvider><App /></DataBusProvider>
  );
};

renderApp();
