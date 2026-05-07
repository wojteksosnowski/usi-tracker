// RatingsPanel.jsx — hook useRatings + komponent RatingsPanel

(function() {
  const { React, usiRegister, useDataBus, CategoryRating, UsiStarScore, ocenaLog, Icon, USI_CATEGORIES, USI_STATUSES, useRatings } = window;

  const RatingsPanel = ({ inv, variant = 'circles', focusedCat = -1, onFocusedCatChange,
      ratings = {}, handleRating, comment = '', handleComment, status = 'Brak', handleStatus, saved = false }) => {
    
    const currentInv = { ratings };
    return (
      <div data-component="RatingsPanel" className="usi-ratings-panel">
        <div data-component="RatingsPanel-Categories">
          <div className="usi-tiny usi-ratings-panel-cat-header">Ocena USI</div>
          <div className="usi-ratings-panel-cat-list">
            {USI_CATEGORIES.map((cat, idx) => (
              <div key={cat.key}
                data-component="CategoryRating-Row"
                onClick={() => onFocusedCatChange && onFocusedCatChange(idx)}
                className={`usi-ratings-panel-cat-row ${idx === focusedCat ? 'active' : ''}`}>
                <div className="usi-ratings-panel-cat-info">
                  <span className="usi-ratings-panel-cat-dot" style={{ background: cat.color }} />
                  <span className="usi-body" style={{ fontWeight: 500 }}>{cat.key}</span>
                  {cat.key === 'Udogodnienia'
                    && inv.suggested_udogodnienia != null
                    && (ratings['Udogodnienia'] == null) && (
                    <span className="usi-ratings-panel-cat-suggested">
                      sugest.&nbsp;{inv.suggested_udogodnienia}
                    </span>
                  )}
                </div>
                <CategoryRating category={cat} value={ratings[cat.key] ?? null}
                  onChange={v => handleRating(cat.key, v)} variant={variant} />
              </div>
            ))}
          </div>
        </div>

        {(inv.amenities && inv.amenities.length > 0) || (inv.amenities_score > 0) ? (
          <div data-component="RatingsPanel-Amenities" className="usi-ratings-panel-amenities-section">
            {inv.amenities && inv.amenities.length > 0 && (
              <>
                <div className="usi-tiny" style={{ marginBottom: 6 }}>Udogodnienia</div>
                <div className="usi-ratings-panel-amenities-list" style={{ marginBottom: 12 }}>
                  {inv.amenities.map(a => <span key={a} className="usi-pill">{a}</span>)}
                </div>
              </>
            )}
            {inv.amenities_score > 0 && (
              <>
                <div className="usi-tiny" style={{ marginBottom: 4 }}>Wyróżniki</div>
                <div className="usi-ratings-panel-amenities-list">
                  {(inv.amenities_matched || []).map(m => (
                    <span key={m.label} className="usi-pill"
                      style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                      {m.label}
                      <span style={{ fontSize: 10, fontWeight: 700, opacity: 0.65 }}>+{m.hm_udo}</span>
                    </span>
                  ))}
                </div>
                <div className="usi-ratings-panel-amenities-score">
                  Suma: <strong>{inv.amenities_score} pkt</strong>
                  {inv.suggested_udogodnienia != null && (
                    <> → sugestia: <strong style={{ color: 'var(--usi-ink)' }}>{inv.suggested_udogodnienia}</strong></>
                  )}
                </div>
              </>
            )}
          </div>
        ) : null}

        <div data-component="RatingsPanel-Status">
          <div className="usi-tiny" style={{ marginBottom: 6 }}>Status</div>
          <select className="usi-input usi-ratings-panel-status-select" value={status} onChange={e => handleStatus(e.target.value)}>
            {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
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
          <div className="usi-small usi-ratings-panel-save-status" style={{ color: saved ? 'var(--usi-success)' : 'var(--usi-ink-4)' }}>
            <Icon name="check" size={11} /> {saved ? 'Zapisano' : 'Auto-zapis'}
          </div>
        </div>
      </div>
    );
  };
  usiRegister('RatingsPanel', RatingsPanel);

})();
