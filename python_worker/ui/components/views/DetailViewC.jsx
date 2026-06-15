// DetailViewC.jsx — widok szczegółowy tryb C

(function() {
    const { React, usiRegister, RatingsPanel, Lightbox, resolvePhotoUrl, SourceBadge, Icon } = window;

  const ModeC = ({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, segment, handleSegment, saved, focusedCat, onFocusedCatChange }) => {
    const [lightbox, setLightbox] = React.useState(null);
    const [currentImageIdx, setCurrentImageIdx] = React.useState(0);

    const photos = inv.photos || [];

    // Reset indeksu po zmianie inwestycji
    React.useEffect(() => {
        setCurrentImageIdx(0);
    }, [inv.usi_inv_id]);

    React.useEffect(() => {
      const handler = (e) => {
        if (lightbox != null) return;
        const tag = e.target.tagName;
        if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

        if (e.key === '[') {
          setCurrentImageIdx(prev => Math.max(0, prev - 1));
        } else if (e.key === ']') {
          setCurrentImageIdx(prev => Math.min(photos.length - 1, prev + 1));
        }
      };
      document.addEventListener('keydown', handler);
      return () => document.removeEventListener('keydown', handler);
    }, [lightbox, photos.length]);

    const hasPhotos = photos.length > 0;
    const currentPhoto = hasPhotos ? photos[currentImageIdx] : null;
    const _src = typeof resolvePhotoUrl === 'function' ? resolvePhotoUrl(currentPhoto) : (typeof currentPhoto === 'string' ? currentPhoto : null);

    return (
      <div data-component="ModeC" style={{ display: 'flex', height: '100%', width: '100%' }}>
        
        {/* Kolumna 1: Zdjecie (80%) */}
        <div className="usi-scroll" style={{ width: '80%', paddingRight: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            {hasPhotos ? (
                <div style={{ position: 'relative', width: '100%', height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
                   <img 
                      key={_src}
                      src={_src}
                      style={{ maxWidth: '100%', maxHeight: '85vh', objectFit: 'contain', cursor: 'pointer', borderRadius: '4px' }}
                      alt={`Zdjęcie ${currentImageIdx + 1}`}
                      onClick={() => setLightbox(currentImageIdx)}
                   />
                   <div style={{ position: 'absolute', bottom: '16px', left: '16px', background: 'rgba(0,0,0,0.7)', color: 'white', padding: '6px 12px', borderRadius: '6px', fontSize: '13px', fontWeight: '500' }}>
                       {currentImageIdx + 1} / {photos.length}
                   </div>
                </div>
            ) : (
                <div style={{ color: '#666', marginTop: '20vh' }}>Brak zdjęć w galerii</div>
            )}
            
            <div style={{ marginTop: 'auto', marginBottom: '16px', fontSize: '13px', color: '#888', textAlign: 'center' }}>
                <kbd style={{ background: '#eee', padding: '2px 6px', borderRadius: '3px' }}>[</kbd> poprzednie zdjęcie &nbsp;|&nbsp; 
                <kbd style={{ background: '#eee', padding: '2px 6px', borderRadius: '3px', marginLeft: '6px' }}>]</kbd> następne zdjęcie &nbsp;|&nbsp; 
                <kbd style={{ background: '#eee', padding: '2px 6px', borderRadius: '3px', marginLeft: '6px' }}>←</kbd> <kbd style={{ background: '#eee', padding: '2px 6px', borderRadius: '3px' }}>→</kbd> poprzednia/następna inwestycja
            </div>
        </div>

        {/* Kolumna 2: Oceny (20%) */}
        <div className="detail-ratings-column usi-scroll usi-p-16" style={{ width: '20%', minWidth: '320px', borderLeft: '1px solid var(--usi-border)' }}>
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
              {inv.source_links && inv.source_links.map((link, i) => (
                  <a key={i} className="usi-btn sm ghost" href={link.url} target="_blank" rel="noopener">
                    <SourceBadge source={link.source} /> <Icon name="arrow" size={11} />
                  </a>
              ))}
            </div>
            <RatingsPanel 
                inv={inv} ratings={ratings} handleRating={handleRating} 
                comment={comment} handleComment={handleComment}
                status={status} handleStatus={handleStatus}
                segment={segment} handleSegment={handleSegment}
                saved={saved} focusedCat={focusedCat}
                onFocusedCatChange={onFocusedCatChange}
             />
        </div>

        {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
      </div>
    );
  };
  usiRegister('ModeC', ModeC);
})();
