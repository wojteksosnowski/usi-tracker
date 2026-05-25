// DetailViewA.jsx — widok szczegółowy tryb A

(function() {
  const { React, usiRegister, MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, PoiModule, ModuleTypes, Gallery, Lightbox, Icon } = window;

  const DetailsA = ({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, 
      segment, handleSegment, saved, focusedCat, onFocusedCatChange, metaConfig, onUpdateInv }) => {
    const { useDataBus, SourceBadge } = window;
    const [marked, setMarked] = React.useState(new Set());
    const [lightbox, setLightbox] = React.useState(null);
    const { bus, setVariable } = useDataBus();
    const [refreshing, setRefreshing] = React.useState(false);
    const [refreshLabel, setRefreshLabel] = React.useState('Odśwież dane');
    const pollRef = React.useRef(null);

    // Cleanup poll on unmount
    React.useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

    const handleRefresh = async () => {
        if (!inv.developer_slug || !inv.investment_slug) return;
        setRefreshing(true);
        setRefreshLabel('Uruchamianie…');
        setVariable('appStatus', { type: 'info', msg: 'Odświeżanie danych…' });

        let jobId = null;
        try {
            const res = await fetch(`/api/refresh/${inv.developer_slug}/${inv.investment_slug}`, { method: 'POST' });
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
              onToggleMark={(idx) => {
                  const next = new Set(marked);
                  if (next.has(idx)) next.delete(idx); else next.add(idx);
                  setMarked(next);
              }} 
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
           />
           <div className="usi-h-24" />
           <PoiModule inv={inv} />
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
        request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/suggest`, { 
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

        request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/merge`, {
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
        request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/unmerge`, {
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
        request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/dismiss-suggestion`, {
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
