window.usiRegister('ViewDownload', function ViewDownload() {
  const {
    React, Icon, Spinner, useDataBus, useApi
  } = window;

  const { bus, setVariable, refetch } = useDataBus();
  const { download = {} } = bus;
  const { request } = useApi();
  const activePortals = Array.from(download.activePortals || ['rp']);
  const identifier = download.search || '';

  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [errorMsg, setErrorMsg] = React.useState(null);
  const [crawlerStatus, setCrawlerStatus] = React.useState(null);
  const [explorationStatus, setExplorationStatus] = React.useState(null);

  // Stats
  const totalFound = results.length;
  const newCount = results.filter(r => r.is_new && !r.registered).length;

  const loadCrawlerStatus = React.useCallback(async () => {
    try {
      const [status, exploration] = await Promise.all([
        request('/api/crawler/status'),
        request('/api/crawler/exploration')
      ]);
      setCrawlerStatus(status);
      setExplorationStatus(exploration);
    } catch (e) {
      console.error("Failed to load crawler status", e);
    }
  }, [request]);

  React.useEffect(() => {
    loadCrawlerStatus();
    const interval = setInterval(loadCrawlerStatus, 5000);
    return () => clearInterval(interval);
  }, [loadCrawlerStatus]);

  const handleGlobalScan = React.useCallback(async (limit = null) => {
    setLoading(true);
    setErrorMsg(null);
    setResults([]);
    const limitLabel = limit ? ` (limit: ok. ${limit} ofert)` : '';
    setVariable('appStatus', { type: 'info', msg: `Rozpoczęto skanowanie portali${limitLabel} w tle...` });
    let allResults = [];
    
    try {
      for (const p of activePortals) {
        try {
          let url = `/api/discovery/${p}/job?id=${encodeURIComponent(identifier)}`;
          if (limit) url += `&limit=${limit}`;
          
          const jobStart = await request(url, { method: 'POST' });
          if (!jobStart.job_id) throw new Error("Nie udało się uruchomić zadania discovery");

          const result = await new Promise((resolve, reject) => {
            const poll = setInterval(async () => {
              try {
                const job = await request(`/api/jobs/${jobStart.job_id}`, { noCache: true });
                if (job.status === 'completed') {
                  clearInterval(poll);
                  resolve(job.result);
                } else if (job.status === 'failed') {
                  clearInterval(poll);
                  reject(new Error(job.error || "Zadanie nie powiodło się"));
                }
              } catch (e) {
                clearInterval(poll);
                reject(e);
              }
            }, 1500);
          });

          if (Array.isArray(result)) {
            allResults = [...allResults, ...result.map(r => ({ ...r, source: p }))];
          }
        } catch (e) {
          console.error(`Błąd skanowania ${p}:`, e);
        }
      }
      setResults(allResults);
      if (allResults.length === 0) {
        setErrorMsg('Nie znaleziono inwestycji na wybranych portalach.');
        setVariable('appStatus', { type: 'info', msg: 'Skanowanie zakończone - brak wyników.' });
      } else {
        const foundNew = allResults.filter(r => r.is_new).length;
        setVariable('appStatus', { type: 'success', msg: `Skanowanie zakończone. Znaleziono ${allResults.length} inwestycji (w tym ${foundNew} nowych).` });
      }
    } catch (err) {
      setErrorMsg('Błąd krytyczny podczas skanowania: ' + err.message);
      setVariable('appStatus', { type: 'error', msg: 'Błąd krytyczny podczas skanowania' });
    } finally {
      setLoading(false);
    }
  }, [activePortals, request, setVariable, identifier]);

  // Expose triggers
  React.useEffect(() => {
    window.usiTriggerScan = handleGlobalScan;
    window.usiTriggerScanLimited = () => handleGlobalScan(150);
    return () => { 
      delete window.usiTriggerScan; 
      delete window.usiTriggerScanLimited;
    };
  }, [handleGlobalScan]);

  const handleRegisterAll = async () => {
    const newOnes = results.filter(r => r.is_new && !r.registered);
    if (newOnes.length === 0) return;
    
    // Group by source (portal) as our API handles one portal at a time per batch
    const bySource = newOnes.reduce((acc, r) => {
      acc[r.source] = acc[r.source] || [];
      acc[r.source].push(r);
      return acc;
    }, {});

    setVariable('appStatus', { type: 'info', msg: `Uruchamianie pobierania zbiorczego dla ${newOnes.length} inwestycji...` });
    
    let startedJobs = 0;
    for (const source in bySource) {
      try {
        const data = await request('/api/register-bulk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            portal: source,
            investments: bySource[source]
          })
        });
        if (data && data.ok) startedJobs++;
      } catch (e) {
        console.error("Bulk registration failed for", source, e);
      }
    }

    if (startedJobs > 0) {
      setResults([]); // Clear results as they are being handled by background jobs
      refetch('investments');
      setVariable('appStatus', { type: 'success', msg: `Zlecono pobranie ${newOnes.length} inwestycji w ${startedJobs} zadaniach zbiorczych.` });
    }
  };

  const toggleCrawler = async () => {
    const isPaused = crawlerStatus?.paused;
    await request(`/api/crawler/${isPaused ? 'resume' : 'pause'}`, { method: 'POST' });
    loadCrawlerStatus();
  };

  return (
    <div data-component="ViewDownload" className="usi-p-24 usi-flex-col usi-gap-24">
      
      {/* 1. Skanowanie manualne (Quick Stats) */}
      <section className="usi-card usi-p-24">
        <div className="usi-flex-row usi-gap-16" style={{ alignItems: 'center' }}>
          <div className="usi-flex-1">
            <h2 className="usi-h2" style={{ marginBottom: 4 }}>Skanowanie manualne</h2>
            <p className="usi-body usi-text-secondary">Wyszukaj i zarejestruj nowe inwestycje z wybranych portali.</p>
          </div>
          <div className="usi-flex-row usi-gap-12">
             <div className="usi-stat-box">
                <div className="usi-tiny usi-text-secondary">Zeskanowano</div>
                <div className="usi-h2">{loading ? <Spinner size={16} /> : totalFound}</div>
             </div>
             <div className="usi-stat-box">
                <div className="usi-tiny usi-text-secondary">Nowe</div>
                <div className="usi-h2 usi-text-success">{loading ? <Spinner size={16} /> : newCount}</div>
             </div>
          </div>
        </div>

        {newCount > 0 && (
          <div className="usi-m-t-24 usi-p-16 usi-surface-2 usi-round-12 usi-flex-row usi-gap-16" style={{ alignItems: 'center' }}>
            <Icon name="sparkle" className="usi-text-accent" />
            <div className="usi-flex-1">
              <div className="usi-weight-600">Znaleziono {newCount} nowych inwestycji</div>
              <div className="usi-tiny usi-text-secondary">Możesz je teraz dodać do bazy jednym kliknięciem.</div>
            </div>
            <button className="usi-btn" onClick={handleRegisterAll}>
              Pobierz wszystko
            </button>
          </div>
        )}
        
        {errorMsg && <div className="usi-pill error usi-m-t-16">{errorMsg}</div>}
      </section>

      {/* 2. Wędrowiec (Crawler Dashboard) */}
      <section className="usi-card usi-p-24">
        <div className="usi-flex-row usi-gap-16" style={{ alignItems: 'center', marginBottom: 20 }}>
          <div className="usi-flex-1">
            <h2 className="usi-h2" style={{ marginBottom: 4 }}>Wędrowiec</h2>
            <p className="usi-body usi-text-secondary">Automatyczny monitoring i eksploracja katalogów portali.</p>
          </div>
          <button className={`usi-btn ${crawlerStatus?.paused ? 'outline' : 'danger'}`} onClick={toggleCrawler}>
             <Icon name={crawlerStatus?.paused ? 'play' : 'pause'} size={14} />
             {crawlerStatus?.paused ? 'Wznów pracę' : 'Wstrzymaj'}
          </button>
        </div>

        <div className="usi-grid usi-gap-16" style={{ gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))' }}>
          
          {/* Status operacyjny */}
          <div className="usi-surface-2 usi-p-16 usi-round-12">
            <h3 className="usi-tiny usi-weight-700 usi-text-secondary usi-uppercase usi-m-b-12">Status operacyjny</h3>
            <div className="usi-flex-row usi-gap-12" style={{ alignItems: 'center' }}>
              <div className={`usi-dot ${crawlerStatus?.running && !crawlerStatus?.paused ? 'active' : ''}`} />
              <div className="usi-weight-600">
                {crawlerStatus?.paused ? 'Wstrzymany' : (crawlerStatus?.running ? 'Aktywny' : 'Wyłączony')}
              </div>
            </div>
            <div className="usi-m-t-16">
               <div className="usi-tiny usi-text-secondary">Ostatnia/Bieżąca wizyta:</div>
               <div className="usi-body usi-weight-500">{crawlerStatus?.current_dev || 'Oczekiwanie...'}</div>
            </div>
          </div>

          {/* Eksploracja katalogów */}
          <div className="usi-surface-2 usi-p-16 usi-round-12">
            <h3 className="usi-tiny usi-weight-700 usi-text-secondary usi-uppercase usi-m-b-12">Eksploracja katalogów</h3>
            <div className="usi-flex-col usi-gap-8">
              {['rp', 'otodom', 'tabelaofert'].map(p => {
                const stat = explorationStatus?.[p] || {};
                const progress = stat.total_pages ? Math.round((stat.current_page / stat.total_pages) * 100) : 0;
                return (
                  <div key={p} className="usi-flex-col usi-gap-4">
                    <div className="usi-flex-row" style={{ justifyContent: 'space-between' }}>
                      <span className="usi-tiny usi-weight-600 usi-uppercase">{p === 'oto' ? 'otodom' : p}</span>
                      <span className="usi-tiny usi-text-secondary">{stat.current_page || 0} / {stat.total_pages || '?'}</span>
                    </div>
                    <div className="usi-progress-bar-bg" style={{ height: 4, background: 'var(--usi-surface-3)', borderRadius: 2 }}>
                       <div className="usi-progress-bar-fill" style={{ height: '100%', width: `${progress}%`, background: 'var(--usi-accent)', borderRadius: 2 }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>
      </section>

      <style>{`
        .usi-stat-box {
          padding: 12px 20px;
          background: var(--usi-surface-2);
          border-radius: 12px;
          min-width: 120px;
          text-align: center;
        }
        .usi-m-t-16 { margin-top: 16px !important; }
        .usi-m-t-24 { margin-top: 24px !important; }
        .usi-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--usi-ink-3);
        }
        .usi-dot.active {
          background: var(--usi-success);
          box-shadow: 0 0 8px var(--usi-success);
          animation: usi-pulse 2s infinite;
        }
        @keyframes usi-pulse {
          0% { opacity: 1; }
          50% { opacity: 0.4; }
          100% { opacity: 1; }
        }
      `}</style>
    </div>
  );
});
