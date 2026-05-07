// DetailViewC.jsx — widok szczegółowy tryb C (Media)

(function() {
  const { React, usiRegister, SlideShow, RatingsPanel } = window;

  const ModeC = ({ inv, marked, onToggleMark, onLightbox, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange }) => {
    const [showRatings, setShowRatings] = React.useState(false);

    return (
      <div data-component="ModeC" className="mode-c-container">
        <div className="mode-c-main">
          <SlideShow 
              photos={inv.photos || []} 
              marked={marked} 
              onToggleMark={onToggleMark} 
              onLightbox={onLightbox} 
              className="usi-h-full"
          />
        </div>
        
        <div data-component="ModeC-Footer" className="mode-c-footer-panel usi-scroll">
          <div className="mode-c-footer-header">
              <div className="usi-tiny accent">MEDIA & OCENY</div>
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
