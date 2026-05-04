window.usiRegister('ViewDownload', function ViewDownload() {
  const {
    React, Icon, Spinner, useDevelopers, useDataBus,
    FilterGroup, DataGrid, ListCard, SourceBadge
  } = window;

  const { bus, setVariable, refetch } = useDataBus();
  const activePortals = Array.from(bus.activeDownloadPortals || ['rp']);
  const identifier = bus.downloadSearch || '';
  const showOnlyNew = bus.downloadOnlyNew || false;

  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [errorMsg, setErrorMsg] = React.useState(null);
  const [registering, setRegistering] = React.useState({});

  const handleSearch = React.useCallback(async () => {
    if (!identifier) return;
    setLoading(true);
    setErrorMsg(null);
    setResults([]);
    
    let allResults = [];
    try {
      for (const portal of activePortals) {
        try {
          const response = await fetch(`/api/discovery/${portal}?id=${encodeURIComponent(identifier)}`);
          const data = await response.json();
          if (response.ok && Array.isArray(data)) {
            allResults = [...allResults, ...data.map(r => ({ ...r, source: portal }))];
          }
        } catch (e) {
          console.error(`Błąd wyszukiwania na ${portal}:`, e);
        }
      }
      setResults(allResults);
      if (allResults.length === 0) setErrorMsg('Nie znaleziono inwestycji spełniającej kryteria.');
    } catch (err) {
      setErrorMsg('Błąd połączenia podczas wyszukiwania');
    } finally {
      setLoading(false);
    }
  }, [activePortals, identifier]);

  const handleGlobalScan = React.useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    setResults([]);
    let allResults = [];
    
    try {
      for (const p of activePortals) {
        try {
          const response = await fetch(`/api/discovery/${p}`);
          const data = await response.json();
          if (response.ok && Array.isArray(data)) {
            allResults = [...allResults, ...data.map(r => ({ ...r, source: p }))];
          }
        } catch (e) {
          console.error(`Błąd skanowania ${p}:`, e);
        }
      }
      setResults(allResults);
      if (allResults.length === 0) setErrorMsg('Nie znaleziono nowych inwestycji na wybranych portalach.');
    } catch (err) {
      setErrorMsg('Błąd krytyczny podczas skanowania');
    } finally {
      setLoading(false);
    }
  }, [activePortals]);

  // Expose triggers to global scope for App ActionBar
  React.useEffect(() => {
    window.usiTriggerScan = handleGlobalScan;
    window.usiHandleSearch = handleSearch;
    return () => { 
      delete window.usiTriggerScan; 
      delete window.usiHandleSearch;
    };
  }, [handleGlobalScan, handleSearch]);

  const handleRegister = async (res) => {
    setRegistering(prev => ({ ...prev, [res.url]: true }));
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          developer_name: res.developer || res.agency_name || res.agency || "Nieznany Deweloper",
          inv_slug: res.slug || String(res.id),
          name: res.name || String(res.id),
          id: res.id,
          url: res.url,
          portal: res.source
        })
      });
      const data = await response.json();
      if (response.ok) {
        setResults(prev => prev.map(r => r.url === res.url ? { ...r, registered: true } : r));
        // Refresh jobs and main investments list
        if (refetch) {
          refetch('jobs');
          refetch('investments');
        }
      } else {
        alert(data.error || 'Błąd rejestracji');
      }
    } catch (err) {
      alert('Błąd połączenia');
    } finally {
      setRegistering(prev => ({ ...prev, [res.url]: false }));
    }
  };

  const visibleResults = results.filter(r => r && (!showOnlyNew || r.is_new));

  const renderCard = (res) => (
    <ListCard
      inv={res}
      footerRight={
        <button 
          className={`usi-btn sm ${res.registered ? 'success' : ''}`} 
          disabled={res.registered || registering[res.url]}
          onClick={(e) => {
            e.stopPropagation();
            handleRegister(res);
          }}
        >
          {registering[res.url] ? <Spinner size={12} stroke={1.5} /> : (res.registered ? 'Pobrano' : 'Pobierz')}
        </button>
      }
    />
  );

  const columns = [
    {
      key: 'image',
      label: 'Zdjęcie',
      width: 80,
      render: (val) => val ? <img src={val} alt="thumb" style={{ width: 60, height: 40, objectFit: 'cover', borderRadius: 4 }} /> : <div style={{ width: 60, height: 40, background: 'var(--usi-surface-2)', borderRadius: 4 }} />
    },
    {
      key: 'name',
      label: 'Nazwa',
      render: (val, row) => (
        <div>
          <div style={{ fontWeight: 600 }}>{val}</div>
          <div style={{ fontSize: 11, color: 'var(--usi-ink-3)' }}>{row.id}</div>
        </div>
      )
    },
    {
      key: 'source',
      label: 'Źródło',
      width: 100,
      render: (val) => SourceBadge ? <SourceBadge source={val} /> : <span style={{ textTransform: 'uppercase', fontSize: 11, fontWeight: 700 }}>{val}</span>
    },
    {
      key: 'developer',
      label: 'Deweloper',
      render: (val) => val || '-'
    },
    {
      key: 'registered',
      label: 'Status',
      width: 120,
      align: 'right',
      render: (val, row) => (
        <button 
          className={`usi-btn sm ${val ? 'success' : ''}`} 
          disabled={val || registering[row.url]}
          onClick={(e) => {
            e.stopPropagation();
            handleRegister(row);
          }}
        >
          {registering[row.url] ? <Spinner size={12} stroke={1.5} /> : (val ? 'Pobrano' : 'Pobierz')}
        </button>
      )
    }
  ];

  return (
    <div data-component="ViewDownload" className="usi-app download-view-content" style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--usi-bg)' }}>
      
      <div style={{ flex: 1, position: 'relative', overflow: 'hidden' }}>
        {errorMsg && (
          <div style={{ padding: '24px 24px 0 24px' }}>
            <div className="usi-pill error" style={{ padding: '12px 16px' }}>{errorMsg}</div>
          </div>
        )}
        
        {visibleResults.length === 0 && !loading && !errorMsg ? (
            <div className="usi-app-empty" style={{ height: '70%', display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: 0.5 }}>
                <Icon name="sparkle" size={48} style={{ marginBottom: 16 }} />
                <div className="usi-body" style={{ fontSize: '1.2rem' }}>Wklej URL inwestycji w pasku u góry i naciśnij Enter</div>
            </div>
        ) : (
          <DataGrid 
            data={visibleResults}
            columns={columns}
            mode={bus.downloadMode || 'grid'}
            gridConfig={{ minCardWidth: 180, itemsPerRow: 4, cardHeight: 340 }}
            renderCard={renderCard}
            emptyMessage={loading ? "Przeszukiwanie wybranych portali..." : "Brak wyników"}
          />
        )}

        {loading && (
          <div style={{ position: 'absolute', top: 24, right: 24, zIndex: 100 }}>
             <Spinner size={24} />
          </div>
        )}
      </div>

    </div>
  );
});
