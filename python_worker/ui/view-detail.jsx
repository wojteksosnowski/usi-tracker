// view-detail.jsx — widok inwestycji (orchestrator)

(function() {
  const { usiRegister } = window;

  function DetailRightPanel({ inv, onBack, onUpdateInv }) {
    const { React, useDataBus, useRatings, useMetadataConfig, HeroBand, ModeC, DetailsA, Lightbox, DataBoundary } = window;
    const { bus, setVariable } = useDataBus();
    const detailMode = bus.detailMode || 'A';
    const setDetailMode = (m) => setVariable('detailMode', m);

    const [marked, setMarked] = React.useState(new Set());
    const [focusedCat, setFocusedCat] = React.useState(-1);
    const [lightbox, setLightbox] = React.useState(null);

    const config = window.useConfig();
    const metaConfig = useMetadataConfig();
    const [localReviewed, setLocalReviewed] = React.useState(inv.reviewed);
    const { request } = window.useApi ? window.useApi() : { request: fetch };
    const [fullInv, setFullInv] = React.useState(inv);
    const { ratings, handleRating, comment, handleComment, status, handleStatus, segment, handleSegment, saved } = useRatings(fullInv);

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
      setVariable('currentInvestment', inv);
      // Task 06.02.03: Sync nearby investments from either full data or index stub
      const nearby = fullInv.nearby_investments || inv.nearby_investments || [];
      setVariable('nearbyInvestments', nearby);
    }, [inv.usi_inv_id, inv.nearby_investments, fullInv.nearby_investments]);

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
                    onToggleMark={(idx) => {
                        const next = new Set(marked);
                        if (next.has(idx)) next.delete(idx); else next.add(idx);
                        setMarked(next);
                    }} 
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
                />
              ) : (
                <DetailsA
                    inv={validInv}
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
