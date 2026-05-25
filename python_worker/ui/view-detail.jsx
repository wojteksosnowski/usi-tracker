// view-detail.jsx — widok inwestycji (orchestrator)

(function() {
  const { React, usiRegister, useDataBus, useRatings, useMetadataConfig } = window;

  function getDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }

  function DetailRightPanel({ inv, onBack, onUpdateInv }) {
    const { HeroBand, ModeC, DetailsA, Lightbox, DataBoundary } = window;
    const { bus, setVariable } = useDataBus();
    const detailMode = bus.detailMode || 'A';
    const setDetailMode = (m) => setVariable('detailMode', m);

    const [marked, setMarked] = React.useState(new Set());
    const [focusedCat, setFocusedCat] = React.useState(-1);
    const [lightbox, setLightbox] = React.useState(null);

    const { ratings, handleRating, comment, handleComment, status, handleStatus, segment, handleSegment, saved } = useRatings(inv);
    const config = window.useConfig();
    const metaConfig = useMetadataConfig();
    const [localReviewed, setLocalReviewed] = React.useState(inv.reviewed);
    const { request } = window.useApi ? window.useApi() : { request: fetch };

    const handleApprove = async () => {
        try {
            const data = await request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/review?id=${inv.usi_inv_id}`, { method: 'POST' });
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
      if (inv.coords && inv.coords[0] !== 0) {
        const [lat, lng] = inv.coords;
        const allInvestments = bus.investments || [];
        const nearby = allInvestments
          .filter(other => {
            if (other.usi_inv_id === inv.usi_inv_id) return false;
            if (!other.coords || other.coords[0] === 0) return false;
            const dist = getDistance(lat, lng, other.coords[0], other.coords[1]);
            return dist <= 5;
          })
          .map(other => ({ 
            ...other, 
            distance: getDistance(lat, lng, other.coords[0], other.coords[1]) 
          }))
          .sort((a, b) => a.distance - b.distance);
        setVariable('nearbyInvestments', nearby);
      }
    }, [inv.slug, bus.investments, setVariable]);

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
      <DataBoundary data={inv}>
        {(validInv) => {
          const { Icon } = window;
          const containerClass = `detail-right-panel usi-scroll usi-p-24 ${detailMode === 'C' ? 'usi-overflow-hidden' : 'usi-overflow-auto'}`;
          return (
            <div data-component="DetailRightPanel" className={containerClass}>
              {localReviewed === false && (
                <div className="usi-flex-row usi-m-b-16">
                  <button className="usi-btn success" onClick={handleApprove}>
                    <Icon name="check" size={12} /> Zatwierdź nową inwestycję
                  </button>
                </div>
              )}

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
