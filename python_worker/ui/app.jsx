// app.jsx — USI Tracker SPA

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin'];
const SOURCES = [
  { id: 'RP', label: 'RynekPierwotny', color: '#0052FF' },
  { id: 'OTO', label: 'Otodom', color: '#00E676' },
  { id: 'TO', label: 'TabelaOfert', color: '#FF9800' }
];

function LoadingScreen() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 16 }}>
      <Spinner />
      <span className="usi-small">Ładowanie danych…</span>
    </div>
  );
}

function EmptyScreen({ onFetch, fetching, fetchCount }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', flexDirection: 'column', gap: 20, background: 'var(--usi-bg)' }}>
      <svg width="64" height="64" viewBox="0 0 48 48" fill="none" style={{ opacity: 0.18 }}>
        <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z" fill="currentColor" />
      </svg>
      <h2 className="usi-h1" style={{ margin: 0 }}>Baza jest pusta</h2>
      <p className="usi-body" style={{ color: 'var(--usi-ink-3)', textAlign: 'center', maxWidth: 360, margin: 0 }}>
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
}

function App() {
  const rootRef = React.useRef(null);
  const [view, setView] = React.useState('list');
  const [selectedInv, setSelectedInv] = React.useState(null);
  const { investments, loading, refetch } = useInvestments();
  const [fetching, setFetching] = React.useState(false);
  const [fetchCount, setFetchCount] = React.useState(0);
  const pollRef = React.useRef(null);
  const [dark, setDark] = React.useState(false);

  // Filter state (lifted from ListGrid)
  const [search, setSearch] = React.useState('');
  const [filterDev, setFilterDev] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState('');
  const [activeSources, setActiveSources] = React.useState(new Set(['RP', 'OTO', 'TO']));
  const [activeCities, setActiveCities] = React.useState(new Set());

  const filteredInvestments = React.useMemo(() => {
    return investments.filter(inv => {
      if (search) {
        const s = search.toLowerCase();
        const match = (inv.name?.toLowerCase().includes(s) ||
                     inv.developer?.toLowerCase().includes(s) ||
                     inv.district?.toLowerCase().includes(s) ||
                     inv.address?.toLowerCase().includes(s));
        if (!match) return false;
      }
      if (filterDev && inv.developer !== filterDev) return false;
      if (filterStatus && inv.status !== filterStatus) return false;
      if (activeSources.size > 0 && inv.source && !activeSources.has(inv.source.toUpperCase())) return false;
      if (activeCities.size > 0) {
        const addr = (inv.address || '').toLowerCase();
        const foundCity = MAIN_CITIES.find(c => addr.includes(c.toLowerCase()));
        if (!foundCity || !activeCities.has(foundCity)) return false;
      }
      return true;
    });
  }, [investments, search, filterDev, filterStatus, activeSources, activeCities]);

  React.useEffect(() => {
    injectThemeCSS();
    if (rootRef.current) applyTheme(rootRef.current, false, '#E5006D');
  }, []);

  const handleToggleTheme = () => {
    const next = !dark;
    setDark(next);
    if (rootRef.current) applyTheme(rootRef.current, next, '#E5006D');
  };

  // Keyboard nav in detail view
  React.useEffect(() => {
    if (view !== 'detail') return;
    const handler = (e) => {
      if (e.key === 'Escape') setView('list');
      if (e.key === 'ArrowLeft') setSelectedInv(prev => {
        if (!prev || filteredInvestments.length === 0) return prev;
        const idx = filteredInvestments.findIndex(i => i.slug === prev.slug);
        return filteredInvestments[(idx - 1 + filteredInvestments.length) % filteredInvestments.length];
      });
      if (e.key === 'ArrowRight') setSelectedInv(prev => {
        if (!prev || filteredInvestments.length === 0) return prev;
        const idx = filteredInvestments.findIndex(i => i.slug === prev.slug);
        return filteredInvestments[(idx + 1) % filteredInvestments.length];
      });
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [view, filteredInvestments]);

  React.useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

  const handleSelectInv = (inv) => {
    setSelectedInv(inv);
    setView('detail');
  };

  const handleNav = (v) => {
    if (v === 'list' || v === 'dashboard') setView(v);
  };

  const handleFetchSample = () => {
    setFetching(true);
    fetch('/api/fetch-sample', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ count: 50 }),
    })
      .then(() => {
        pollRef.current = setInterval(() => {
          fetch('/api/fetch-status')
            .then(r => r.json())
            .then(d => {
              setFetchCount(d.count);
              if (d.count > 0) {
                clearInterval(pollRef.current);
                setFetching(false);
                refetch();
              }
            })
            .catch(() => {});
        }, 3000);
      })
      .catch(() => setFetching(false));
  };

  const invIndex = selectedInv
    ? filteredInvestments.findIndex(i => i.slug === selectedInv.slug)
    : 0;

  if (loading) {
    return (
      <div ref={rootRef} style={{ minHeight: '100vh' }}>
        <LoadingScreen />
      </div>
    );
  }

  if (investments.length === 0) {
    return (
      <div ref={rootRef} style={{ minHeight: '100vh' }}>
        <EmptyScreen onFetch={handleFetchSample} fetching={fetching} fetchCount={fetchCount} />
      </div>
    );
  }

  return (
    <div ref={rootRef} style={{ height: '100vh', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <AppHeader activeView={view} onView={handleNav} dark={dark} onToggleTheme={handleToggleTheme} />
      <div style={{ flex: 1, overflow: 'hidden' }}>
        {view === 'list' && (
          <ListGrid
            investments={investments}
            filteredInvestments={filteredInvestments}
            onSelectInv={handleSelectInv}
            onNav={handleNav}
            search={search} onSearch={setSearch}
            filterDev={filterDev} onFilterDev={setFilterDev}
            filterStatus={filterStatus} onFilterStatus={setFilterStatus}
            activeSources={activeSources} onSetActiveSources={setActiveSources}
            activeCities={activeCities} onSetActiveCities={setActiveCities}
          />
        )}
        {view === 'detail' && selectedInv && (
          <DetailRightPanel
            inv={selectedInv}
            invIndex={invIndex >= 0 ? invIndex : 0}
            invTotal={filteredInvestments.length}
            onBack={() => setView('list')}
            onNav={handleNav}
            onPrev={() => setSelectedInv(prev => {
              const idx = filteredInvestments.findIndex(i => i.slug === prev.slug);
              return filteredInvestments[(idx - 1 + filteredInvestments.length) % filteredInvestments.length];
            })}
            onNext={() => setSelectedInv(prev => {
              const idx = filteredInvestments.findIndex(i => i.slug === prev.slug);
              return filteredInvestments[(idx + 1) % filteredInvestments.length];
            })}
          />
        )}
        {view === 'dashboard' && (
          <DashboardGrid investments={investments} onNav={handleNav} />
        )}
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(<App />);
