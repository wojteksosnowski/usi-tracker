// RatingsPanel.jsx — hook useRatings + komponent RatingsPanel

(function() {
  const { React, usiRegister, useDataBus, CategoryRating, CategoryRatingRow, UsiStarScore, ocenaLog, Icon, USI_CATEGORIES, USI_STATUSES, useRatings } = window;

  const RatingsPanel = ({ inv, variant = 'circles', focusedCat = -1, onFocusedCatChange,
      ratings = {}, handleRating, comment = '', handleComment, status = 'Brak', handleStatus,
      segment = '', handleSegment, saved = false }) => {
    
    const currentInv = { ratings };
    return (
      <div data-component="RatingsPanel" className="usi-ratings-panel">
        <div data-component="RatingsPanel-Categories">
          <div className="usi-tiny usi-ratings-panel-cat-header">Ocena USI</div>
          <div className="usi-ratings-panel-cat-list">
            {USI_CATEGORIES.map((cat, idx) => (
              <CategoryRatingRow
                key={cat.key}
                category={cat}
                index={idx}
                focusedIndex={focusedCat}
                onFocus={onFocusedCatChange}
                value={ratings[cat.key] ?? null}
                onChange={v => handleRating(cat.key, v)}
                variant={variant}
                suggestedValue={cat.key === 'Udogodnienia' ? inv.suggested_udogodnienia : null}
              />
            ))}
          </div>
        </div>

        {(inv.amenities && inv.amenities.length > 0) || (inv.amenities_score > 0) ? (
          <div data-component="RatingsPanel-Amenities" className="usi-ratings-panel-amenities-section">
            {inv.amenities && inv.amenities.length > 0 && (
              <>
                <div className="usi-tiny usi-m-b-6">Udogodnienia</div>
                <div className="usi-ratings-panel-amenities-list usi-m-b-12">
                  {inv.amenities.map(a => <span key={a} className="usi-pill">{a}</span>)}
                </div>
              </>
            )}
            {inv.amenities_score > 0 && (
              <>
                <div className="usi-tiny usi-m-b-4">Wyróżniki</div>
                <div className="usi-ratings-panel-amenities-list">
                  {(inv.amenities_matched || []).map(m => (
                    <span key={m.label} className="usi-pill">
                      {m.label}
                      <span className="usi-pill-score">+{m.hm_udo}</span>
                    </span>
                  ))}
                </div>
                <div className="usi-ratings-panel-amenities-score">
                  Suma: <strong>{inv.amenities_score} pkt</strong>
                  {inv.suggested_udogodnienia != null && (
                    <> → sugestia: <strong className="usi-ink">{inv.suggested_udogodnienia}</strong></>
                  )}
                </div>
              </>
            )}
          </div>
        ) : null}

        <div data-component="RatingsPanel-Status" className="usi-flex-row usi-gap-12">
          <div className="usi-flex-1">
            <div className="usi-tiny usi-m-b-6">Status</div>
            <select className="usi-input usi-ratings-panel-status-select" value={status} onChange={e => handleStatus(e.target.value)}>
              {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          {(() => {
            const { useConfig } = window;
            const config = useConfig();
            return config?.segments && (
              <div className="usi-flex-1">
                <div className="usi-tiny usi-m-b-6">Segment</div>
                <select className="usi-input usi-ratings-panel-status-select" value={segment} onChange={e => handleSegment(e.target.value)}>
                  <option value="">(Wykryty)</option>
                  {config.segments.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            );
          })()}
        </div>
        <textarea data-component="RatingsPanel-Comment" className="usi-input usi-textarea usi-ratings-panel-comment" placeholder="Komentarz globalny…"
          value={comment} onChange={handleComment} />
        <div data-component="RatingsPanel-Footer" className="usi-ratings-panel-footer">
          <div className="usi-ratings-panel-score-box">
            {(() => { const score = ocenaLog(currentInv); return (<>
              <UsiStarScore score={score} />
              <span className="usi-ratings-panel-score-value">
                {score !== null ? score.toFixed(2) : '—'}
                <span className="usi-ratings-panel-score-max"> / 4</span>
              </span>
            </>); })()}
          </div>
          <div className={`usi-small usi-ratings-panel-save-status ${saved ? 'saved' : ''}`}>
            <Icon name="check" size={11} /> {saved ? 'Zapisano' : 'Auto-zapis'}
          </div>
        </div>
      </div>
    );
  };
  usiRegister('RatingsPanel', RatingsPanel);

})();
