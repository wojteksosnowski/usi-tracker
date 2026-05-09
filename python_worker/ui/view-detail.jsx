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

    const { ratings, handleRating, comment, handleComment, status, handleStatus, saved } = useRatings(inv);
    const metaConfig = useMetadataConfig();

    React.useEffect(() => {
      setVariable('currentInvestment', inv);
      if (inv.coords && inv.coords[0] !== 0) {
        const [lat, lng] = inv.coords;
        const allInvestments = bus.investments || [];
        const nearby = allInvestments
          .filter(other => {
            if (other.slug === inv.slug) return false;
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
