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
    const [localReviewed, setLocalReviewed] = React.useState(inv.reviewed);
    const [showReportModal, setShowReportModal] = React.useState(false);
    const { request } = window.useApi ? window.useApi() : { request: fetch };

    React.useEffect(() => {
        setLocalReviewed(inv.reviewed);
    }, [inv.slug, inv.reviewed]);

    const handleApprove = async () => {
        try {
            const data = await request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/review`, { method: 'POST' });
            if (data && data.ok) {
                setLocalReviewed(true);
                setVariable('appStatus', { type: 'success', msg: 'Inwestycja została zatwierdzona.' });
                refetch('investments');
            }
        } catch (err) {
            console.error("Approval failed", err);
        }
    };

    const handleReport = async (note) => {
        if (!note) return;
        try {
            const data = await request(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/report`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ note })
            });
            if (data && data.ok) {
                setVariable('appStatus', { type: 'success', msg: 'Zgłoszenie zostało zapisane.' });
                setShowReportModal(false);
            }
        } catch (err) {
            console.error("Reporting failed", err);
        }
    };

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
          const { Icon } = window;
          const containerClass = `detail-right-panel usi-scroll usi-p-24 ${detailMode === 'C' ? 'usi-overflow-hidden' : 'usi-overflow-auto'}`;
          return (
            <div data-component="DetailRightPanel" className={containerClass}>
              <div className="usi-flex-row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                 <div className="usi-flex-row usi-gap-12">
                    {localReviewed === false && (
                        <button className="usi-btn success" onClick={handleApprove}>
                           <Icon name="check" size={12} /> Zatwierdź nową inwestycję
                        </button>
                    )}
                    <button className="usi-btn ghost" onClick={() => setShowReportModal(true)}>
                        <Icon name="info" size={12} /> Report
                    </button>
                 </div>
                 <div />
              </div>

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

              <ReportModal 
                isOpen={showReportModal} 
                onClose={() => setShowReportModal(false)} 
                onConfirm={handleReport} 
              />

              <style>{`
                .usi-modal-backdrop {
                  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                  background: rgba(0,0,0,0.6);
                  z-index: 10000;
                  display: flex; align-items: center; justify-content: center;
                }
                .usi-modal-content {
                  width: 100%; max-width: 500px;
                  background: var(--usi-surface);
                  padding: 24px;
                  box-shadow: 0 20px 40px rgba(0,0,0,0.4);
                  border-radius: 16px;
                }
              `}</style>
            </div>
          );
        }}
      </DataBoundary>
    );
  }

  function ReportModal({ isOpen, onClose, onConfirm }) {
    const { React } = window;
    const [note, setNote] = React.useState('');
    if (!isOpen) return null;

    return (
      <div className="usi-modal-backdrop" onClick={onClose}>
        <div className="usi-modal-content usi-card" onClick={e => e.stopPropagation()}>
          <h2 className="usi-h2">Zgłoś błąd / notatka</h2>
          <textarea 
            className="usi-input usi-m-t-16" 
            style={{ width: '100%', minHeight: 120, resize: 'vertical', background: 'var(--usi-surface-2)' }}
            placeholder="Opisz co jest nie tak z danymi tej inwestycji..."
            value={note}
            onChange={e => setNote(e.target.value)}
            autoFocus
          />
          <div className="usi-flex-row usi-gap-12 usi-m-t-24" style={{ justifyContent: 'flex-end' }}>
            <button className="usi-btn ghost" onClick={onClose}>Anuluj</button>
            <button className="usi-btn primary" onClick={() => { onConfirm(note); setNote(''); }}>OK</button>
          </div>
        </div>
      </div>
    );
  }


  usiRegister('DetailRightPanel', DetailRightPanel);
})();
