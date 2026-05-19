// DetailViewC.jsx — widok szczegółowy tryb C (Media + pasek kategorii)

(function() {
  const { React, usiRegister, SlideShow, RatingsPanel, CategoryRatingRow, Icon } = window;

  const ModeC = ({ inv, marked, onToggleMark, onLightbox, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange }) => {
    const [panelOpen, setPanelOpen] = React.useState(false);
    const categories = window.USI_CATEGORIES || [];

    const handleCatClick = (idx) => {
      if (onFocusedCatChange) onFocusedCatChange(idx);
      setPanelOpen(true);
    };

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

        <div data-component="ModeC-Footer" className="mode-c-footer-panel">
          <div className="mode-c-catbar">
            {categories.map((cat, idx) => (
              <CategoryRatingRow
                key={cat.key}
                category={cat}
                index={idx}
                focusedIndex={focusedCat}
                onFocus={handleCatClick}
                value={(ratings || {})[cat.key] ?? null}
                onChange={v => handleRating(cat.key, v)}
                variant="circles"
                suggestedValue={cat.key === 'Udogodnienia' ? inv.suggested_udogodnienia : null}
                className="mode-c-footer-row"
              />
            ))}
            <button
              className="mode-c-panel-toggle"
              onClick={() => setPanelOpen(v => !v)}
              title={panelOpen ? 'Zwiń oceny' : 'Rozwiń oceny'}>
              <Icon name={panelOpen ? 'chevronDown' : 'chevronUp'} size={14} />
            </button>
          </div>

          {panelOpen && (
            <div className="mode-c-ratings-wrap usi-scroll">
              <RatingsPanel
                inv={inv} ratings={ratings} handleRating={handleRating}
                comment={comment} handleComment={handleComment}
                status={status} handleStatus={handleStatus}
                saved={saved} focusedCat={focusedCat}
                onFocusedCatChange={onFocusedCatChange}
              />
            </div>
          )}
        </div>
      </div>
    );
  };
  usiRegister('ModeC', ModeC);
})();
