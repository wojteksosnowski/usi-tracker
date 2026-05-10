window.usiRegister('ViewDownload', function ViewDownload() {
  const {
    React, Icon, Spinner, useDevelopers, useDataBus,
    FilterGroup, DataGrid, ListCard, SourceBadge, useApi
  } = window;

  const { bus, setVariable, refetch } = useDataBus();
  const { download } = bus;
  const { request } = useApi();
  const activePortals = Array.from(download.activePortals || ['rp']);
  const identifier = download.search || '';
  const showOnlyNew = download.onlyNew || false;

  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [errorMsg, setErrorMsg] = React.useState(null);
  const [registering, setRegistering] = React.useState({});

  const handleGlobalScan = React.useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    setResults([]);
    setVariable('appStatus', { type: 'info', msg: 'Rozpoczęto skanowanie portali...' });
    let allResults = [];
    
    try {
      for (const p of activePortals) {
        try {
          setVariable('appStatus', { type: 'info', msg: `Skanowanie: ${p}...` });
          const data = await request(`/api/discovery/${p}`);
          console.log(`[Discovery] Portal ${p} returned:`, data);
          if (Array.isArray(data)) {
            allResults = [...allResults, ...data.map(r => ({ ...r, source: p }))];
          } else {
            console.error(`[Discovery] Expected array from /api/discovery/${p}, got:`, data);
          }
        } catch (e) {
          console.error(`Błąd skanowania ${p}:`, e);
        }
      }
      console.log(`[Discovery] Final results set:`, allResults.length, "items");
      setResults(allResults);
      if (allResults.length === 0) {
        setErrorMsg('Nie znaleziono inwestycji na wybranych portalach.');
        setVariable('appStatus', { type: 'info', msg: 'Skanowanie zakończone - brak wyników.' });
      } else {
        const newCount = allResults.filter(r => r.is_new).length;
        setVariable('appStatus', { type: 'success', msg: `Skanowanie zakończone. Znaleziono ${allResults.length} inwestycji (w tym ${newCount} nowych).` });
      }
    } catch (err) {
      setErrorMsg('Błąd krytyczny podczas skanowania');
      setVariable('appStatus', { type: 'error', msg: 'Błąd krytyczny podczas skanowania' });
    } finally {
      setLoading(false);
    }
  }, [activePortals, request, setVariable]);

  // Expose trigger to global scope for App ActionBar
  React.useEffect(() => {
    window.usiTriggerScan = handleGlobalScan;
    return () => { 
      delete window.usiTriggerScan; 
    };
  }, [handleGlobalScan]);

  const handleRegister = async (res) => {
    setRegistering(prev => ({ ...prev, [res.url]: true }));
    try {
      const data = await request('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          developer_name: res.developer || res.agency_name || res.agency || res.vendor_slug || "Nieznany Deweloper",
          inv_slug: res.slug || String(res.id),
          name: res.name || String(res.id),
          id: res.id,
          url: res.url,
          portal: res.source
        })
      });
      if (data) {
        setResults(prev => prev.filter(r => r.url !== res.url));
        if (refetch) {
          refetch('jobs');
          refetch('investments');
        }
      }
    } catch (err) {
      // Error handled by useApi
    } finally {
      setRegistering(prev => ({ ...prev, [res.url]: false }));
    }
  };

  const handleRegisterAll = async () => {
    const newOnes = visibleResults.filter(r => r.is_new && !r.registered);
    if (newOnes.length === 0) return;
    setVariable('appStatus', { type: 'info', msg: `Pobieranie ${newOnes.length} nowych inwestycji...` });
    for (const res of newOnes) {
      await handleRegister(res);
    }
    setVariable('appStatus', { type: 'success', msg: `Zlecono pobranie ${newOnes.length} inwestycji. Postęp możesz śledzić w pasku zadań.` });
  };

  const visibleResults = React.useMemo(() => {
    return results.filter(r => {
      if (!r) return false;
      if (showOnlyNew && !r.is_new) return false;
      if (identifier) {
          const query = identifier.toLowerCase();
          const matchesName = String(r.name || '').toLowerCase().includes(query);
          const matchesDev = String(r.developer || '').toLowerCase().includes(query);
          const matchesId = String(r.id || '').toLowerCase().includes(query);
          if (!matchesName && !matchesDev && !matchesId) return false;
      }
      return true;
    });
  }, [results, showOnlyNew, identifier]);

  const renderCard = (res) => (
    <ListCard
      inv={{...res, developer: res.developer || '-'}}
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
      render: (val) => val ? <img src={val} alt="thumb" className="list-table-thumb" /> : <div className="list-table-thumb-empty" />
    },
    {
      key: 'name',
      label: 'Nazwa',
      render: (val, row) => (
        <div>
          <div className="usi-weight-600">{val}</div>
          <div className="usi-tiny usi-text-secondary">{row.id}</div>
        </div>
      )
    },
    {
      key: 'source',
      label: 'Źródło',
      width: 100,
      render: (val) => window.SourceBadge ? <window.SourceBadge source={val} /> : <span className="usi-tiny usi-weight-600" style={{ textTransform: 'uppercase' }}>{val}</span>
    },
    {
      key: 'developer',
      label: 'Deweloper',
      render: (val) => String(val || '-')
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

  const emptyMessage = React.useMemo(() => {
    if (loading) return "Przeszukiwanie wybranych portali...";
    if (results.length > 0 && visibleResults.length === 0) {
      return `Brak wyników (ukryto ${results.length} już pobranych inwestycji - wyłącz filtr "Tylko nowe")`;
    }
    return "Nie znaleziono inwestycji spełniających kryteria.";
  }, [loading, results.length, visibleResults.length]);

  const newCount = visibleResults.filter(r => r.is_new && !r.registered).length;

  return (
    <div data-component="ViewDownload" className="download-view-container">
      {newCount > 0 && (
        <div className="usi-download-bulk-bar">
          <span className="usi-tiny usi-text-secondary">{newCount} nowych do pobrania</span>
          <button className="usi-btn sm" onClick={handleRegisterAll}>
            <Icon name="zap" size={12} /> Pobierz wszystkie nowe ({newCount})
          </button>
        </div>
      )}
      <div className="usi-flex-1 usi-overflow-hidden">
        {errorMsg && (
          <div className="usi-p-24" style={{ paddingBottom: 0 }}>
            <div className="usi-pill error usi-p-16">{errorMsg}</div>
          </div>
        )}
        
        {visibleResults.length === 0 && !loading && !errorMsg ? (
            <div className="usi-app-empty download-empty-state">
                <Icon name="zap" size={48} className="usi-m-16" />
                <div className="usi-h2">Kliknij "Skanuj", aby wyszukać nowe inwestycje</div>
            </div>
        ) : (
          <DataGrid 
            data={visibleResults}
            columns={columns}
            mode={download.mode || 'grid'}
            gridConfig={{ minCardWidth: 180, itemsPerRow: 4, cardHeight: 340 }}
            renderCard={renderCard}
            emptyMessage={emptyMessage}
          />
        )}
      </div>
    </div>
  );
});
