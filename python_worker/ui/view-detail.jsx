// view-detail.jsx — widok inwestycji (orchestrator)

(function() {
  const { React, usiRegister, useDataBus, useRatings, useMetadataConfig, extractModuleContext } = window;

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
    const [detailMode, setDetailMode] = React.useState('A');
    const [marked, setMarked] = React.useState(new Set());
    const [focusedCat, setFocusedCat] = React.useState(-1);
    const [lightbox, setLightbox] = React.useState(null);

    const { ratings, handleRating, comment, handleComment, status, handleStatus, saved } = useRatings(inv);
    const metaConfig = useMetadataConfig();
    const { bus, setVariable } = useDataBus();

    React.useEffect(() => {
      setVariable('currentInvestment', inv);
      if (inv.coords && inv.coords[0] !== 0) {
        const [lat, lng] = inv.coords;
        const visible = bus.visibleInvestments || [];
        const nearby = visible
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
    }, [inv.slug, bus.visibleInvestments, setVariable]);

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
          const context = {
            currentInvestment: validInv,
            geo: extractModuleContext.extractGeoPoint(validInv),
            district: validInv.district,
          };

          return (
            <div data-component="DetailRightPanel" className="usi-scroll" style={{ height: '100%', overflowY: detailMode === 'C' ? 'hidden' : 'auto', padding: '24px', display: 'flex', flexDirection: 'column' }}>
              <HeroBand 
                inv={validInv} 
                showMap={true} 
                detailMode={detailMode} 
                onModeChange={setDetailMode} 
                moduleContext={context}
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
                    moduleContext={context}
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
