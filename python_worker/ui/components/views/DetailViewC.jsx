// DetailViewC.jsx — widok szczegółowy tryb C (Media + pasek kategorii)

(function() {
  const { React, usiRegister, SlideShow, RatingsPanel, Icon } = window;

  const ModeC = ({ inv, marked, onToggleMark, onLightbox, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange }) => {
    const [panelOpen, setPanelOpen] = React.useState(false);
    const categories = window.USI_CATEGORIES || [];

    const handleCatClick = (key) => {
      if (onFocusedCatChange) onFocusedCatChange(key);
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
            {categories.map(cat => {
              const val = (ratings || {})[cat.key] || 0;
              return (
                <button
                  key={cat.key}
                  className={`mode-c-cat-chip${focusedCat === cat.key ? ' active' : ''}`}
                  onClick={() => handleCatClick(cat.key)}
                  title={cat.key}>
                  <span className="mode-c-cat-dot" style={{ background: cat.color }} />
                  <span className="mode-c-cat-short">{cat.short}</span>
                  <span className="mode-c-cat-val">{val > 0 ? val : '—'}</span>
                </button>
              );
            })}
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
