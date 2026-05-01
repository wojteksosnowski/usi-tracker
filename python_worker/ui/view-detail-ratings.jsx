// view-detail-ratings.jsx — hook useRatings + komponent RatingsPanel

// Session-level cache so ratings survive navigation without a full page reload.
const _ratingCache = new Map(); // slug → { ratings, comment, status }

function useRatings(inv) {
  const CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];
  const init = () => {
    const cached = _ratingCache.get(inv.slug);
    const base = cached ? cached.ratings : (inv.ratings || {});
    const r = {};
    CATS.forEach(k => { r[k] = (base[k] ?? null); });
    return r;
  };
  const [ratings, setRatings] = React.useState(init);
  const [comment, setComment] = React.useState(() => {
    const cached = _ratingCache.get(inv.slug);
    return cached ? cached.comment : (inv.comment || '');
  });
  const [status, setStatus] = React.useState(() => {
    const cached = _ratingCache.get(inv.slug);
    return cached ? cached.status : (inv.status || 'Brak');
  });
  const [saved, setSaved] = React.useState(false);
  const debounceRef = React.useRef(null);

  React.useEffect(() => {
    const cached = _ratingCache.get(inv.slug);
    setRatings(init());
    setComment(cached ? cached.comment : (inv.comment || ''));
    setStatus(cached ? cached.status : (inv.status || 'Brak'));
    setSaved(false);
  }, [inv.slug]);

  const persist = (r, c, s) => {
    fetch(`/api/ratings/${inv.developer_slug}/${inv.investment_slug}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...r, komentarz: c, status: s }),
    })
      .then(() => {
        _ratingCache.set(inv.slug, { ratings: r, comment: c, status: s });
        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
      })
      .catch(() => {});
  };

  const handleRating = (key, val) => {
    const next = { ...ratings, [key]: val };
    setRatings(next);
    persist(next, comment, status);
  };

  const handleComment = (e) => {
    const val = e.target.value;
    setComment(val);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => persist(ratings, val, status), 800);
  };

  const handleStatus = (val) => {
    setStatus(val);
    persist(ratings, comment, val);
  };

  return { ratings, setRatings, comment, setComment, status, setStatus, saved, handleRating, handleComment, handleStatus };
}

function RatingsPanel({ inv, variant = 'circles', focusedCat = -1, onFocusedCatChange,
    ratings = {}, handleRating, comment = '', handleComment, status = 'Brak', handleStatus, saved = false }) {
  const currentInv = { ratings };
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
      <div>
        <div className="usi-tiny" style={{ marginBottom: 8 }}>Ocena USI</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          {USI_CATEGORIES.map((cat, idx) => (
            <div key={cat.key}
              onClick={() => onFocusedCatChange && onFocusedCatChange(idx)}
              style={{
                display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12,
                background: idx === focusedCat ? 'rgba(0,0,0,0.05)' : 'transparent',
                borderRadius: 6, padding: '3px 4px', margin: '0 -4px',
                cursor: 'default', transition: 'background .12s',
              }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 110 }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: cat.color, flexShrink: 0 }} />
                <span className="usi-body" style={{ fontWeight: 500 }}>{cat.key}</span>
                {cat.key === 'Udogodnienia'
                  && inv.suggested_udogodnienia != null
                  && (ratings['Udogodnienia'] == null) && (
                  <span style={{ fontSize: 10, color: 'var(--usi-ink-4)', marginLeft: 2 }}>
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
      <div>
        <div className="usi-tiny" style={{ marginBottom: 6 }}>Status</div>
        <select className="usi-input" value={status} onChange={e => handleStatus(e.target.value)}
          style={{ width: '100%', fontSize: 13, height: 32, padding: '0 8px' }}>
          {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <textarea className="usi-input usi-textarea" placeholder="Komentarz globalny…"
        value={comment} onChange={handleComment} style={{ minHeight: 72 }} />
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {(() => { const score = ocenaLog(currentInv); return (<>
            <UsiStarScore score={score} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>
              {score !== null ? score.toFixed(2) : '—'}
              <span style={{ fontWeight: 400, color: 'var(--usi-ink-3)' }}> / 4</span>
            </span>
          </>); })()}
        </div>
        <div className="usi-small" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: saved ? 'var(--usi-success)' : 'var(--usi-ink-4)', transition: 'color .3s' }}>
          <Icon name="check" size={11} /> {saved ? 'Zapisano' : 'Auto-zapis'}
        </div>
      </div>
    </div>
  );
}
