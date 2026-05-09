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
          <Icon name="usiLogo" size={64} />
        </div>
        <h2 className="usi-h1">Baza jest pusta</h2>
        <p className="usi-body empty-screen-text">
          Brak inwestycji w bazie. Pobierz przykładowe rekordy z RynekPierwotny.pl.
        </p>
        {fetching ? (
          <div className="usi-flex-row usi-gap-12 usi-text-secondary">
            <Spinner size={20} stroke={2} />
            <span className="usi-small">Pobieram dane… {fetchCount > 0 ? `(${fetchCount} rekordów)` : ''}</span>
          </div>
        ) : (
          <button className="usi-btn usi-p-24" onClick={onFetch}>
            <Icon name="sparkle" size={15} /> Pobierz 50 inwestycji z RP
          </button>
        )}
      </div>
    );
  };
  usiRegister('EmptyScreen', EmptyScreen);

  const App = () => {
    const {
      Spinner, Icon, ModuleErrorBoundary,
      ViewList, DeveloperListGrid, DeveloperDetail,
      DetailRightPanel, DashboardGrid, ViewDownload, ViewLibrary, ViewStoryboard, UIStoryboard, ReportsList, ReportDetail, DataBusProvider, useDataBus,
      useInvestments, useDevelopers, useConfig,
      MAIN_CITIES, SOURCES, USI_STATUSES, applyTheme, injectThemeCSS,
      NavbarShell, NavbarTitle, NavbarCounter, ActionBar, NotificationCenter, StatusMessenger,
      GlobalSearch, FilterGroup, FilterChip, NavMenuButton, NavDrawer,
      LoadingScreen, EmptyScreen, useDataBusSelector, TestSuite
    } = window;

    const rootRef = React.useRef(null);
    const [view, setView] = React.useState('list');
    const [navOpen, setNavOpen] = React.useState(false);
    const [selectedInv, setSelectedInv] = React.useState(null);
    const [selectedDev, setSelectedDev] = React.useState(null);
    const [selectedReport, setSelectedReport] = React.useState(null);
    
    // Combined DataBus access
    const { bus, setVariable, refetch: busRefetch } = useDataBus();

    // Secondary hooks
    const config = useConfig();
    const testResults = useDataBusSelector(state => state.testResults);

    // Manual refetch wrapper since we have bus here
    const refetch = React.useCallback((type) => busRefetch(type), [busRefetch]);

    // 3. UI State
    const [fetching] = React.useState(false);
    const [fetchCount] = React.useState(0);
    const [dark, setDark] = React.useState(false);
    const [mode, setMode] = React.useState('grid');

    try {
      const { 
        investments, developers, loading,
        filters, download, visibleInvestments
      } = bus;
      const { search, dev: filterDev, status: filterStatus, sources: activeSources, cities: activeCities } = filters;

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

      const handleSelectInv = (inv) => {
        if (!inv) return;
        console.group('[App] Selected Investment');
        console.log('Slug:', inv.slug);
        console.log('Photos:', inv.photos?.length || 0, inv.photos);
        console.log('Metadata:', { price: inv.price_avg, delivery: inv.delivery, units: inv.units });
        console.groupEnd();
        setSelectedInv(inv);
        setView('detail');
      };

      const toggleSource = (id, isShift) => {
        setVariable('filters.sources', prev => {
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
        setVariable('filters.cities', prev => {
          if (city === null) return new Set();
          const next = new Set(prev);
          if (isShift) return new Set([city]);
          if (next.has(city)) next.delete(city);
          else next.add(city);
          return next;
        });
      };

      const toggleDownloadPortal = (id, isShift) => {
        setVariable('download.activePortals', prev => {
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

      React.useEffect(() => {
        const { TestSuite } = window;
        if (TestSuite) {
          setTimeout(() => TestSuite.run(setVariable), 2000);
        }
      }, [setVariable]);

      if (loading && investments.length === 0) return <div data-component="App" ref={rootRef} className="app-container usi-app"><LoadingScreen /></div>;
      if (!loading && investments.length === 0) return <div data-component="App" ref={rootRef} className="app-container usi-app"><EmptyScreen onFetch={() => {}} fetching={fetching} fetchCount={fetchCount} /></div>;

      const getTitle = () => {
        if (view === 'list') return "Inwestycje";
        if (view === 'developers') return "Deweloperzy";
        if (view === 'dashboard') return "Dashboard";
        if (view === 'library') return "Biblioteka Modułów";
        if (view === 'storyboard') return "USI Storyboard";
        if (view === 'download') return "Pobieranie";
        if (view === 'reports') return "Raporty";
        if (view === 'detail') return selectedInv?.name || "Szczegóły";
        if (view === 'dev-detail') return selectedDev?.name || "Szczegóły dewelopera";
        return "USI Tracker";
      };

      const getSubtitle = () => {
        if (view === 'list') return `${visibleInvestments.length} widocznych`;
        if (view === 'developers') return `${developers.length} firm`;
        if (view === 'library') return "Przegląd komponentów systemowych";
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
                  {(() => {
                    const hasFailures = testResults && testResults.some(s => s.tests.some(t => t.status === 'fail'));
                    const statusColor = !testResults ? 'var(--usi-ink-4)' : hasFailures ? 'var(--usi-danger)' : 'var(--usi-success)';
                    
                    return (
                      <button 
                        className="usi-btn ghost icon sm" 
                        onClick={() => TestSuite && TestSuite.run(setVariable)} 
                        title="Uruchom testy jednostkowe JS"
                        style={{ color: statusColor }}
                      >
                        <Icon name="zap" size={16} />
                      </button>
                    );
                  })()}
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
                  <GlobalSearch value={search} onChange={v => setVariable('filters.search', v)} placeholder={view === 'list' ? "Szukaj inwestycji..." : "Szukaj dewelopera..."} />
                </div>
              ) : view === 'download' ? (
                <div className="usi-action-bar-group">
                  <div className="mode-toggle">
                    <button className="usi-btn icon sm" aria-pressed={download.mode === 'grid'} onClick={() => setVariable('download.mode', 'grid')}><Icon name="grid" /></button>
                    <button className="usi-btn icon sm" aria-pressed={download.mode === 'table'} onClick={() => setVariable('download.mode', 'table')}><Icon name="list" /></button>
                  </div>
                  <GlobalSearch 
                    value={download.search || ''} 
                    onChange={v => setVariable('download.search', v)} 
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
                  {view === 'list' && (
                    <>
                      <div className="usi-divider-v" />
                      <FilterGroup label="Miasta">
                        {MAIN_CITIES.map(city => (
                          <FilterChip key={city} label={city} active={activeCities.has(city)} onClick={(isShift) => toggleCity(city, isShift)} />
                        ))}
                      </FilterGroup>
                    </>
                  )}
                </div>
              ) : view === 'download' ? (
                <FilterGroup label="Opcje">
                  <label className="usi-label-clickable">
                    <input type="checkbox" checked={download.onlyNew || false} onChange={e => setVariable('download.onlyNew', e.target.checked)} />
                    Tylko nowe
                  </label>
                </FilterGroup>
              ) : null
            }
            right={
              view === 'list' ? (
                <div className="usi-flex-row usi-gap-8">
                  <select className="usi-input sm usi-w-150" value={filterDev} onChange={e => setVariable('filters.dev', e.target.value)}>
                    <option value="">Deweloperzy</option>
                    {developers.map(d => <option key={d.developer_slug} value={d.developer_slug}>{d.name}</option>)}
                  </select>
                  <select className="usi-input sm usi-w-120" value={filterStatus} onChange={e => setVariable('filters.status', e.target.value)}>
                    <option value="">Statusy</option>
                    {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              ) : view === 'detail' && selectedInv ? (
                <div className="usi-flex-row usi-gap-16">
                  {window.SourceLinks && <window.SourceLinks inv={selectedInv} />}
                  <div className="usi-divider-v" />
                  <div className="mode-switch">
                    <button 
                      className={`usi-btn sm ghost mode-switch-btn ${ (bus.detailMode || 'A') === 'A' ? 'active' : ''}`} 
                      onClick={() => setVariable('detailMode', 'A')}
                    >
                      Standard
                    </button>
                    <button 
                      className={`usi-btn sm ghost mode-switch-btn ${ (bus.detailMode || 'A') === 'C' ? 'active' : ''}`} 
                      onClick={() => setVariable('detailMode', 'C')}
                    >
                      Media
                    </button>
                  </div>
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
                        active={(download.activePortals || new Set()).has(p.id)} 
                        onClick={(isShift) => toggleDownloadPortal(p.id, isShift)} 
                      />
                    ))}
                  </FilterGroup>
                  <div className="usi-divider-v" />
                  <button className="usi-btn ghost sm" onClick={() => window.usiTriggerScan && window.usiTriggerScan()}>
                    <Icon name="zap" size={14} /> Skanuj
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
              <div className="usi-p-24 usi-flex-col usi-flex-center">
                <h2 className="usi-h2">Coś poszło nie tak</h2>
                <p className="usi-body">Wystąpił błąd podczas renderowania tego widoku.</p>
                <button className="usi-btn" onClick={() => window.location.reload()}>Odśwież aplikację</button>
              </div>
            }>
              {view === 'list' && (
                <ViewList 
                  onSelectInv={handleSelectInv} 
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
                  onSelectInv={handleSelectInv}
                />
              )}

              {view === 'download' && <ViewDownload />}
              {view === 'library' && <ViewLibrary />}
              {view === 'storyboard' && (window.ViewStoryboard ? <ViewStoryboard /> : <UIStoryboard />)}
              {view === 'reports' && <ReportsList onSelectReport={(r) => { setSelectedReport(r); setView('report-detail'); }} />}
              {view === 'report-detail' && selectedReport && <ReportDetail reportId={selectedReport.id} onBack={() => setView('reports')} />}
            </ModuleErrorBoundary>
          </main>

          <NotificationConsole />
          {navOpen && <NavDrawer current={view} onClose={() => setNavOpen(false)} onNav={handleNav} dark={dark} onToggleTheme={handleToggleTheme} />}
        </div>
      );
    } catch (err) {
      console.error("CRITICAL APP RENDER ERROR:", err);
      return <div className="usi-p-24" style={{ color: '#c00' }}><h1>Błąd renderowania</h1><pre>{err.stack}</pre></div>;
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
