// DetailViewA.jsx — widok szczegółowy tryb A

(function() {
  const { React, usiRegister, MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, PoiModule, ModuleTypes, Gallery, Lightbox, Icon } = window;

  const DetailsA = ({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange, metaConfig, onUpdateInv }) => {
    const { useDataBus } = window;
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
        </div>
        {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
      </div>
    );
  };
  usiRegister('DetailsA', DetailsA);
})();
