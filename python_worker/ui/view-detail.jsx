// view-detail.jsx — widok inwestycji (orchestrator)

(function() {
  const { usiRegister } = window;

  function DetailRightPanel({ inv, onBack, onUpdateInv, onSelectInv }) {
    const { React, useDataBus, useRatings, useMetadataConfig, HeroBand, ModeC, DetailsA, Lightbox, DataBoundary } = window;
    const { bus, setVariable } = useDataBus();
    const detailMode = bus.detailMode || 'A';
    const setDetailMode = (m) => setVariable('detailMode', m);

    const [marked, setMarked] = React.useState(new Set());
    const [focusedCat, setFocusedCat] = React.useState(-1);
    const [lightbox, setLightbox] = React.useState(null);

    // Reset marked when switching investment
    React.useEffect(() => { setMarked(new Set()); }, [inv.usi_inv_id]);

    // Sync marked count to DataBus so ActionBar can show delete button
    React.useEffect(() => {
      setVariable('markedPhotos', marked);
    }, [marked]);

    const toggleMark = (idx) => {
      setMarked(prev => {
        const next = new Set(prev);
        if (next.has(idx)) next.delete(idx); else next.add(idx);
        return next;
      });
    };

    const handleDeleteMarked = async () => {
      const { Icon } = window;
      const photos = (fullInv.photos || fullInv.image_paths || []);
      const paths = [...marked].map(i => photos[i]).filter(Boolean);
      if (!paths.length) return;
      try {
        const data = await request(`/api/investment/${fullInv.usi_inv_id}/mark-delete`, {
          method: 'POST',
          body: JSON.stringify({ paths }),
          headers: { 'Content-Type': 'application/json' }
        });
        if (data && data.ok) {
          setMarked(new Set());
          setVariable('appStatus', { type: 'success', msg: `Oznaczono ${paths.length} zdjęć do usunięcia.` });
          // Expose globally so ActionBar can call it
        }
      } catch (err) {
        setVariable('appStatus', { type: 'error', msg: 'Błąd: ' + err.message });
      }
    };

    // Expose handleDeleteMarked globally so ActionBar delete btn can call it
    React.useEffect(() => {
      window._usiDeleteMarked = handleDeleteMarked;
      return () => { delete window._usiDeleteMarked; };
    });

    const config = window.useConfig();
    const metaConfig = useMetadataConfig();
    const [localReviewed, setLocalReviewed] = React.useState(inv.reviewed);
    const { request } = window.useApi ? window.useApi() : { request: fetch };
    const [fullInv, setFullInv] = React.useState(inv);
    const { ratings, handleRating, comment, handleComment, status, handleStatus, segment, handleSegment, saved } = useRatings(fullInv);

    const [refreshing, setRefreshing] = React.useState(false);
    const [refreshLabel, setRefreshLabel] = React.useState('Odśwież dane');
    const [rebuilding, setRebuilding] = React.useState(false);
    const [rebuildLabel, setRebuildLabel] = React.useState('Odbuduj z raw');
    const pollRef = React.useRef(null);
    React.useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current); }, []);

    const handleRefresh = React.useCallback(async () => {
        if (!inv.usi_inv_id) return;
        if (pollRef.current) clearInterval(pollRef.current);
        setRefreshing(true);
        setRefreshLabel('Uruchamianie…');
        setVariable('appStatus', { type: 'info', msg: 'Odświeżanie danych…' });

        let jobId = null;
        try {
            const res = await request(`/api/investment/${inv.usi_inv_id}/refresh`, { method: 'POST' });
            if (res && res.error) {
                setVariable('appStatus', { type: 'error', msg: 'Błąd startu: ' + (res.error || 'nieznany błąd') });
                setRefreshing(false);
                setRefreshLabel('Odśwież dane');
                return;
            }
            jobId = res ? res.job_id : null;
        } catch (err) {
            setVariable('appStatus', { type: 'error', msg: 'Błąd sieci: ' + err.message });
            setRefreshing(false);
            setRefreshLabel('Odśwież dane');
            return;
        }

        if (!jobId) return;

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
            } catch (_) { }
        }, 2000);
    }, [inv.usi_inv_id, onUpdateInv, request]);

    const handleRebuildFromRaw = React.useCallback(async () => {
        if (!inv.usi_inv_id) return;
        if (pollRef.current) clearInterval(pollRef.current);
        setRebuilding(true);
        setRebuildLabel('Uruchamianie…');
        setVariable('appStatus', { type: 'info', msg: 'Odbudowywanie rekordu z raw…' });

        let jobId = null;
        try {
            const res = await request(`/api/investment/${inv.usi_inv_id}/refresh`, { 
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ use_local_raw: true })
            });
            if (res && res.error) {
                setVariable('appStatus', { type: 'error', msg: 'Błąd startu: ' + (res.error || 'nieznany błąd') });
                setRebuilding(false);
                setRebuildLabel('Odbuduj z raw');
                return;
            }
            jobId = res ? res.job_id : null;
        } catch (err) {
            setVariable('appStatus', { type: 'error', msg: 'Błąd sieci: ' + err.message });
            setRebuilding(false);
            setRebuildLabel('Odbuduj z raw');
            return;
        }

        if (!jobId) return;

        pollRef.current = setInterval(async () => {
            try {
                const r = await fetch(`/api/jobs/${jobId}`);
                if (!r.ok) return;
                const job = await r.json();
                if (job.message) setRebuildLabel(job.message.slice(0, 40));

                if (job.status === 'completed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setRebuilding(false);
                    setRebuildLabel('Odbuduj z raw');
                    setVariable('appStatus', { type: 'success', msg: job.message || 'Odbudowano pomyślnie.' });
                    if (onUpdateInv) onUpdateInv();
                } else if (job.status === 'failed') {
                    clearInterval(pollRef.current);
                    pollRef.current = null;
                    setRebuilding(false);
                    setRebuildLabel('Odbuduj z raw');
                    setVariable('appStatus', { type: 'error', msg: job.message || 'Błąd odbudowywania.' });
                }
            } catch (_) { }
        }, 2000);
    }, [inv.usi_inv_id, onUpdateInv, request]);

    React.useEffect(() => {
        window._usiRefreshData = handleRefresh;
        window._usiRebuildFromRaw = handleRebuildFromRaw;
        setVariable('isRefreshing', refreshing);
        setVariable('refreshLabel', refreshLabel);
        setVariable('isRebuilding', rebuilding);
        setVariable('rebuildLabel', rebuildLabel);
        return () => { 
            delete window._usiRefreshData; 
            delete window._usiRebuildFromRaw;
        };
    }, [handleRefresh, handleRebuildFromRaw, refreshing, refreshLabel, rebuilding, rebuildLabel]);

    React.useEffect(() => {
        // Sync Guard (06.02.02): Reset fullInv immediately to prevent stale photos/metadata
        if (fullInv.usi_inv_id !== inv.usi_inv_id) {
            setFullInv(inv);
        }
        
        let active = true;
        const controller = new AbortController(); // Abort Pattern (06.02.01)
        
        if (inv.usi_inv_id) {
            request(`/api/investment/${inv.usi_inv_id}/data`, { signal: controller.signal })
                .then(data => {
                    if (active && data && !data.error) {
                        setFullInv(prev => {
                            // Final safety check: ignore response if ID moved on
                            if (data.usi_inv_id !== inv.usi_inv_id) return prev;

                            return {
                                ...prev,
                                ...data,
                                // Keep index photos visible until full list arrives; prefer fetched if richer
                                photos: (data.photos && data.photos.length > 0) ? data.photos : prev.photos,
                                ratings: (data.ratings && Object.keys(data.ratings).length > 0) ? data.ratings : prev.ratings
                            };
                        });
                    }
                })
                .catch(err => {
                    if (err.name === 'AbortError' || err.message?.includes('aborted')) {
                        // Silent expected abort
                        return;
                    }
                    console.error("Failed to load full investment data", err);
                });
        }
        return () => { 
            active = false; 
            controller.abort(); 
        };
    }, [inv.usi_inv_id]);

    const handleApprove = async () => {
        try {
            const data = await request(`/api/investment/${inv.usi_inv_id}/review`, { method: 'POST' });
            if (data && data.ok) {
                setLocalReviewed(true);
                setVariable('appStatus', { type: 'success', msg: 'Inwestycja została zatwierdzona.' });
                window.usiRefetch && window.usiRefetch('investments');
            }
        } catch (err) {
            console.error("Approval failed", err);
        }
    };

    React.useEffect(() => {
      setVariable('currentInvestment', fullInv || inv);
      const coords = fullInv?.coords || inv?.coords;
      const lat = coords?.[0];
      const lon = coords?.[1];

      if (lat != null && lon != null) {
          const reqFn = window.request || fetch;
          reqFn(`/api/investments/nearby?lat=${lat}&lon=${lon}&radius=8.0&limit=24`)
            .then(res => (typeof res.json === 'function' ? res.json() : res))
            .then(data => {
                if (data && data.status === 'ok') {
                    setVariable('nearbyInvestments', data.data || []);
                } else {
                    setVariable('nearbyInvestments', []);
                }
            })
            .catch(err => {
                console.error("Failed to fetch nearby investments", err);
                setVariable('nearbyInvestments', []);
            });
      } else {
          setVariable('nearbyInvestments', []);
      }
    }, [inv.usi_inv_id, fullInv?.coords]);

    // Keyboard shortcuts
    React.useEffect(() => {
      const CATS = window.USI_CATEGORIES.map(c => c.key);
      const handler = (e) => {
        if (lightbox != null) return;
        const tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
        if (e.key >= '1' && e.key <= '6') {
          e.preventDefault();
          setFocusedCat(parseInt(e.key) - 1);
        } else if ((e.key === '-' || e.key === '_') && focusedCat >= 0) {
          e.preventDefault();
          const cat = CATS[focusedCat];
          handleRating(cat, Math.max(0, (ratings[cat] || 0) - 1));
        } else if ((e.key === '=' || e.key === '+') && focusedCat >= 0) {
          e.preventDefault();
          const cat = CATS[focusedCat];
          handleRating(cat, Math.min(4, (ratings[cat] || 0) + 1));
        }
      };
      document.addEventListener('keydown', handler);
      return () => document.removeEventListener('keydown', handler);
    }, [lightbox, focusedCat, ratings, window.USI_CATEGORIES, handleRating]);

    return (
      <DataBoundary data={fullInv}>
        {(validInv) => {
          const { Icon } = window;
          const containerClass = `detail-right-panel usi-scroll usi-p-24 ${detailMode === 'C' ? 'usi-overflow-hidden' : 'usi-overflow-auto'}`;
          return (
            <div data-component="DetailRightPanel" className={containerClass}>


              <HeroBand
                inv={validInv}
                showMap={true}
              />

              {detailMode === 'C' ? (
                <ModeC 
                    inv={validInv} 
                    marked={marked} 
                    onToggleMark={toggleMark} 
                    onLightbox={setLightbox}
                    ratings={ratings}
                    handleRating={handleRating}
                    comment={comment}
                    handleComment={handleComment}
                    status={status}
                    handleStatus={handleStatus}
                    segment={segment}
                    handleSegment={handleSegment}
                    saved={saved}
                    focusedCat={focusedCat}
                    onFocusedCatChange={setFocusedCat}
                    onSelectInv={onSelectInv}
                />
              ) : (
                <DetailsA
                    inv={validInv}
                    marked={marked}
                    onToggleMark={toggleMark}
                    ratings={ratings}
                    handleRating={handleRating}
                    comment={comment}
                    handleComment={handleComment}
                    status={status}
                    handleStatus={handleStatus}
                    segment={segment}
                    handleSegment={handleSegment}
                    saved={saved}
                    focusedCat={focusedCat}
                    onFocusedCatChange={setFocusedCat}
                    metaConfig={metaConfig}
                    onUpdateInv={onUpdateInv}
                    onSelectInv={onSelectInv}
                />
              )}

              {lightbox !== null && <Lightbox inv={validInv} index={lightbox} onClose={() => setLightbox(null)} />}

            </div>
          );
        }}
      </DataBoundary>
    );
  }

  usiRegister('DetailRightPanel', DetailRightPanel);
})();
