// DetailViewC.jsx — widok szczegółowy tryb C (Media)

(function() {
  const { React, usiRegister, SlideShow, RatingsPanel } = window;

  const ModeC = ({ inv, marked, onToggleMark, onLightbox, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange }) => {
    const [showRatings, setShowRatings] = React.useState(false);

    return (
      <div data-component="ModeC" style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', margin: '0 -24px -24px' }}>
        <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
          <SlideShow 
              photos={inv.photos || []} 
              marked={marked} 
              onToggleMark={onToggleMark} 
              onLightbox={onLightbox} 
              style={{ height: '100%' }}
          />
        </div>
        
        <div data-component="ModeC-Footer" style={{ 
          background: 'var(--usi-surface)', 
          borderTop: '.5px solid var(--usi-border)',
          padding: showRatings ? '16px 24px' : '8px 24px',
          maxHeight: showRatings ? '60%' : 'auto',
          overflow: 'auto',
          transition: 'all .3s ease'
        }} className="usi-scroll">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: showRatings ? 12 : 0 }}>
              <div className="usi-tiny" style={{ fontWeight: 700, color: 'var(--usi-accent)' }}>MEDIA & OCENY</div>
              <button className="usi-btn sm ghost" onClick={() => setShowRatings(!showRatings)}>
                  {showRatings ? 'Ukryj panel' : 'Pokaż panel ocen'}
              </button>
          </div>
          
          {showRatings && (
              <RatingsPanel 
                  inv={inv} ratings={ratings} handleRating={handleRating} 
                  comment={comment} handleComment={handleComment}
                  status={status} handleStatus={handleStatus}
                  saved={saved} focusedCat={focusedCat}
                  onFocusedCatChange={onFocusedCatChange}
              />
          )}
        </div>
      </div>
    );
  };
  usiRegister('ModeC', ModeC);
})();
