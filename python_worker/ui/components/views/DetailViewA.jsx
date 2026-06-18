// DetailViewA.jsx — widok szczegółowy tryb A

(function() {
  const { React, usiRegister, MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, PoiModule, ModuleTypes, Gallery, Lightbox, Icon, ModuleErrorBoundary } = window;

  const DetailsA = ({ inv, marked = new Set(), onToggleMark, ratings, handleRating, comment, handleComment, status, handleStatus, 
      segment, handleSegment, saved, focusedCat, onFocusedCatChange, metaConfig, onUpdateInv, onSelectInv }) => {
    const { useDataBus, SourceBadge } = window;
    const [lightbox, setLightbox] = React.useState(null);
    
    // KROK 1: Wyciągamy 'refetch' z szyny danych do odświeżenia listy głównej po złączeniu
    const { bus, setVariable, refetch } = useDataBus();
    
    const [refreshing, setRefreshing] = React.useState(false);
    const [refreshLabel, setRefreshLabel] = React.useState('Odśwież dane');
    const pollRef = React.useRef(null);

    // KROK 2: Wydajna kontrola klawisza Alt przez referencję (O(1) re-render overhead)
    const altPressedRef = React.useRef(false);

    React.useEffect(() => {
        const handleKeyDown = (e) => { if (e.key === 'Alt') altPressedRef.current = true; };
        const handleKeyUp = (e) => { if (e.key === 'Alt') altPressedRef.current = false; };
        const handleBlur = () => { altPressedRef.current = false; };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('keyup', handleKeyUp);
        window.addEventListener('blur', handleBlur);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('keyup', handleKeyUp);
            window.removeEventListener('blur', handleBlur);
        };
    }, []);

    // KROK 3: Interceptor kliknięcia w moduł "W okolicy"
    const handleNearbySelect = async (nearbyInv) => {
        if (altPressedRef.current) {
            // Przechwycono Alt + Klik -> Wykonujemy złączenie struktur danych
            if (!nearbyInv.usi_inv_id) return;
            
            setVariable('appStatus', { type: 'info', msg: 'Łączenie inwestycji z poziomu sąsiedztwa...' });
            try {
                const res = await fetch(`/api/investment/${inv.usi_inv_id}/merge`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        source_id: nearbyInv.usi_inv_id, 
                        target_id: inv.usi_inv_id 
                    })
                });

                if (res.ok) {
                    setVariable('appStatus', { type: 'success', msg: `Pomyślnie podłączono ${nearbyInv.name || nearbyInv.investment_slug} do bieżącego rekordu.` });
                    if (onUpdateInv) onUpdateInv(); // Odświeża stan widoku szczegółowego
                    if (refetch) refetch('investments'); // Odświeża listę w tle
                } else {
                    const errData = await res.json().catch(() => ({}));
                    setVariable('appStatus', { type: 'error', msg: 'Błąd API podczas złączania: ' + (errData.error || 'Nieznany błąd') });
                }
            } catch (err) {
                setVariable('appStatus', { type: 'error', msg: 'Błąd komunikacji z backendem: ' + err.message });
            }
        } else {
            // Standardowe zachowanie - przejście do klikniętej inwestycji
            if (onSelectInv) onSelectInv(nearbyInv);
        }
    };

    // Cleanup poll on unmount
    React.useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

    const handleRefresh = async () => {
        if (!inv.usi_inv_id) return;
        setRefreshing(true);
        setRefreshLabel('Uruchamianie…');
        setVariable('appStatus', { type: 'info', msg: 'Odświeżanie danych…' });

        let jobId = null;
        try {
            const res = await fetch(`/api/investment/${inv.usi_inv_id}/refresh`, { method: 'POST' });
            const data = await res.json();
            if (!data.ok) {
                setVariable('appStatus', { type: 'error', msg: 'Błąd startu: ' + (data.error || 'nieznany błąd') });
                setRefreshing(false);
                setRefreshLabel('Odśwież dane');
                return;
            }
            jobId = data.job_id;
        } catch (err) {
            setVariable('appStatus', { type: 'error', msg: 'Błąd sieci: ' + err.message });
            setRefreshing(false);
            setRefreshLabel('Odśwież dane');
            return;
        }

        // Poll job status every 2s until completed or failed
        pollRef.current = setInterval(async () => {
            try {
                const r = await fetch(`/api/jobs/${jobId}`);
                if (!r.ok) return;
                const job = await r.json();
                if (job.message) setRefreshLabel(job.message.slice(0, 40));

                if (job.status === 'completed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setRefreshing(false);
                    setRefreshLabel('Odśwież dane');
                    setVariable('appStatus', { type: 'success', msg: job.message || 'Zaktualizowano pomyślnie.' });
                    if (onUpdateInv) onUpdateInv();
                } else if (job.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setRefreshing(false);
                    setRefreshLabel('Odśwież dane');
                    setVariable('appStatus', { type: 'error', msg: job.message || 'Błąd odświeżania.' });
                }
            } catch (_) { /* sieć chwilowo niedostępna — czekamy na następny tick */ }
        }, 2000);
    };
    
    return (
      <div data-component="DetailsA" className="detail-grid">
        <div className="detail-gallery-column usi-scroll">
           <Gallery 
              inv={inv} 
              columns={3} 
              marked={marked} 
              onToggleMark={onToggleMark} 
              onLightbox={setLightbox} 
           />
        </div>

        <div className="detail-ratings-column usi-scroll usi-p-16">
           <RatingsPanel 
              inv={inv} ratings={ratings} handleRating={handleRating} 
              comment={comment} handleComment={handleComment}
              status={status} handleStatus={handleStatus}
              segment={segment} handleSegment={handleSegment}
              saved={saved} focusedCat={focusedCat}
              onFocusedCatChange={onFocusedCatChange}
           />
        </div>

        <div className="detail-modules-column usi-scroll usi-p-16">
           <ModuleWrapper
              component={NearbyInvestmentsModule}
              moduleSpec={{
                inputs: { items: { type: ModuleTypes.RecordSet, from: 'nearbyInvestments' } }
              }}
              context={bus}
              title="W okolicy"
              icon="map"
              height={400}
              // PODMIANA TUTAJ: Przekazujemy nasz interceptor zamiast surowej metody nawigacji
              onSelectInv={handleNearbySelect} 
              bus={bus}
              headerAction={
                <button 
                  className="usi-btn ghost sm" 
                  title="Przeskanuj ponownie promienie dla tej inwestycji"
                  onClick={async (e) => {
                    e.stopPropagation();
                    const btn = e.currentTarget;
                    btn.disabled = true;
                    try {
                      const res = await fetch(`/api/investment/${inv.usi_inv_id}/recalc-nearby`, { method: 'POST' });
                      if (res.ok && onUpdateInv) onUpdateInv();
                    } finally {
                      btn.disabled = false;
                    }
                  }}
                >
                  <Icon name="refresh" size={12} />
                </button>
              }
           />
           <div className="usi-h-24" />
           <ModuleErrorBoundary>
               <PoiModule inv={inv} />
           </ModuleErrorBoundary>
        </div>

        <div className="detail-meta-column usi-scroll usi-p-16">
           <button 
              className="usi-btn usi-btn-outline usi-w-full usi-m-b-16" 
              onClick={handleRefresh}
              disabled={refreshing}
           >
              <Icon name="sparkle" size={14} className="usi-m-r-8" />
              {refreshLabel}
           </button>
           <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '8px' }}>
              {inv.master_id && (
                <span className="badge master-group-badge" style={{
                  backgroundColor: 'var(--color-primary, #2b6cb0)',
                  color: '#fff',
                  padding: '4px 8px',
                  borderRadius: '4px',
                  fontSize: '0.85rem',
                  fontWeight: 'bold',
                  display: 'inline-flex',
                  alignItems: 'center'
                }}>
                  ⚙️ MASTER: {inv.master_id}
                </span>
              )}
           </div>
           <MetadataPanel inv={inv} config={metaConfig} />
           <div className="usi-m-b-16" />
           <InvestmentMergeModule inv={inv} onUpdateInv={onUpdateInv} />
        </div>
        {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
      </div>
    );
  };
  usiRegister('DetailsA', DetailsA);

  function InvestmentMergeModule({ inv, onUpdateInv }) {
    const { React, Icon, Spinner, SourceBadge, useApi, useDataBus } = window;
    const { request } = useApi ? useApi() : { request: window.fetch };
    const { refetch, setVariable } = useDataBus ? useDataBus() : { refetch: ()=>{}, setVariable: ()=>{} };

    const [suggesting, setSuggesting] = React.useState(false);
    const [localSuggestions, setLocalSuggestions] = React.useState(inv.suggestions || []);
    const [localMerged, setLocalMerged] = React.useState(inv.merged_from || []);

    React.useEffect(() => {
        setLocalSuggestions(inv.suggestions || []);
        setLocalMerged(inv.merged_from || []);
    }, [inv]);

    const handleSuggest = () => {
        setSuggesting(true);
        request(`/api/investment/${inv.usi_inv_id}/suggest`, { 
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_id: inv.usi_inv_id })
        })
        .then(res => {
            setVariable('appStatus', { type: 'info', msg: 'Rozpoczęto skanowanie...' });
            if (onUpdateInv) setTimeout(onUpdateInv, 5000); // Wait for job then refresh
        })
        .finally(() => setSuggesting(false));
    };

    const handleMerge = (suggestion) => {
        const source_id = suggestion.usi_inv_id;
        setLocalSuggestions(prev => prev.filter(s => s.usi_inv_id !== source_id));
        setLocalMerged(prev => [{
            usi_inv_id: source_id,
            dev_slug: suggestion.developer_slug,
            inv_slug: suggestion.investment_slug,
            name: suggestion.name
        }, ...prev]);

        request(`/api/investment/${inv.usi_inv_id}/merge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_id, target_id: inv.usi_inv_id })
        })
        .then(() => {
            if (onUpdateInv) onUpdateInv();
            refetch('investments');
        });
    };

    const handleUnmerge = (memberId) => {
        setLocalMerged(prev => prev.filter(m => m.usi_inv_id !== memberId));
        request(`/api/investment/${inv.usi_inv_id}/unmerge`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source_id: memberId, target_id: inv.master_id || inv.usi_inv_id })
        })
        .then(() => {
            if (onUpdateInv) onUpdateInv();
            refetch('investments');
        });
    };

    const handleDismiss = (suggested_id) => {
        setLocalSuggestions(prev => prev.filter(s => s.usi_inv_id !== suggested_id));
        request(`/api/investment/${inv.usi_inv_id}/dismiss-suggestion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ usi_inv_id: suggested_id, target_id: inv.usi_inv_id })
        });
    };

    return (
        <div className="usi-flex-col usi-gap-16">
            <div className="usi-card usi-p-16 suggestions-card">
                <div className="usi-flex-row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: localSuggestions.length > 0 ? 12 : 0 }}>
                    <h3 className="dev-panel-header usi-text-accent" style={{ margin: 0, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5 }}>
                        <Icon name="sparkle" size={12} className="usi-m-r-8"/> Sugestie złączeń
                    </h3>
                    <button className="usi-btn sm ghost" onClick={handleSuggest} disabled={suggesting}>
                        {suggesting ? <Spinner size={12}/> : <Icon name="search" size={12}/>}
                    </button>
                </div>
                {localSuggestions.length > 0 ? (
                    <div className="usi-flex-col usi-gap-8">
                        {localSuggestions.map(s => (
                            <div key={s.usi_inv_id} className="dev-mini-card">
                                <div className="usi-body usi-weight-600">{s.name || s.investment_slug}</div>
                                <div className="usi-tiny usi-text-secondary">{s.developer_slug}/{s.investment_slug}</div>
                                <div className="usi-tiny usi-text-secondary usi-m-b-8">{s.reason} ({s.score})</div>
                                <div className="usi-flex-row usi-gap-6">
                                    <button className="usi-btn sm usi-flex-1" onClick={() => handleMerge(s)}>Połącz</button>
                                    <button className="usi-btn sm ghost" onClick={() => handleDismiss(s.usi_inv_id)}>
                                        <Icon name="x" size={12} />
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="usi-tiny usi-text-secondary" style={{ marginTop: 8 }}>Brak sugestii.</div>
                )}
            </div>

            {localMerged.length > 0 && (
                <div className="usi-card usi-p-16">
                    <h3 className="dev-panel-header" style={{ margin: 0, fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
                        <Icon name="grid" size={12} className="usi-m-r-8"/> Skład rekordu
                    </h3>
                    <div className="usi-flex-col usi-gap-8">
                        <div className="dev-mini-card" style={{ background: 'var(--usi-surface-3)' }}>
                            <div className="usi-tiny usi-weight-600">Główny rekord (Target)</div>
                            <div className="usi-tiny usi-mono">{inv.usi_inv_id}</div>
                        </div>
                        {localMerged.map(m => {
                            if (m.usi_inv_id === inv.usi_inv_id) return null; // Skip self
                            return (
                                <div key={m.usi_inv_id} className="dev-mini-card">
                                    <div className="usi-body usi-weight-600">{m.name || m.inv_slug}</div>
                                    <div className="usi-tiny usi-mono">{m.usi_inv_id}</div>
                                    <button className="usi-btn ghost sm" onClick={() => handleUnmerge(m.usi_inv_id)} style={{ marginTop: 8 }}>
                                        Odłącz
                                    </button>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
  }

})();
