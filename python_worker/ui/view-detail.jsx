// view-detail.jsx — widok inwestycji (rdzeń: HeroBand, ModeC, DetailRightPanel)
// Komponenty galerii → view-detail-gallery.jsx
// Hook i panel ocen → view-detail-ratings.jsx

function Row({ k, v, mono }) {
  return (
    <div data-component="Row">
      <div className="usi-small" style={{ marginBottom: 1 }}>{k}</div>
      <div className={mono ? 'usi-mono' : ''} style={{ fontWeight: 500 }}>{v}</div>
    </div>
  );
}

function MetadataBlock({ inv }) {
  return (
    <div data-component="MetadataBlock">
      <div className="usi-tiny" style={{ marginBottom: 8 }}>Metadane</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 16px', fontSize: 13 }}>
        {inv.address && <Row k="Adres" v={inv.address} />}
        {inv.units > 0 && <Row k="Mieszkania" v={inv.units} />}
        <Row k="Termin" v={inv.delivery} />
        {inv.price_avg > 0 && <Row k="Cena śr." v={`${inv.price_avg.toLocaleString('pl-PL')} zł/m²`} mono />}
        <Row k="Zdjęcia" v={inv.photos ? inv.photos.length : 0} mono />
        {inv.folder_path && (
          <div style={{ gridColumn: 'span 2', marginTop: 4 }}>
            <div className="usi-small" style={{ marginBottom: 1 }}>Ścieżka folderu</div>
            <div className="usi-mono" style={{ fontSize: 11, wordBreak: 'break-all', opacity: 0.8 }}>{inv.folder_path}</div>
          </div>
        )}
      </div>
      {inv.amenities && inv.amenities.length > 0 && (
        <>
          <div className="usi-tiny" style={{ margin: '14px 0 6px' }}>Udogodnienia</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {inv.amenities.map(a => <span key={a} className="usi-pill">{a}</span>)}
          </div>
        </>
      )}
      {inv.amenities_score > 0 && (
        <>
          <div className="usi-tiny" style={{ margin: '12px 0 4px' }}>Wyróżniki</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
            {(inv.amenities_matched || []).map(m => (
              <span key={m.label} className="usi-pill"
                style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                {m.label}
                <span style={{ fontSize: 10, fontWeight: 700, opacity: 0.65 }}>+{m.hm_udo}</span>
              </span>
            ))}
          </div>
          <div style={{ marginTop: 6, fontSize: 12, color: 'var(--usi-ink-3)' }}>
            Suma: <strong>{inv.amenities_score} pkt</strong>
            {inv.suggested_udogodnienia != null && (
              <> → sugestia Udogodnienia: <strong style={{ color: 'var(--usi-ink)' }}>{inv.suggested_udogodnienia}</strong></>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function SourceLinks({ inv }) {
  const links = inv.source_links || [{ source: inv.source, url: inv.source_url }];
  return (
    <div data-component="SourceLinks" style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
      {links.map((link, i) => (
        <a key={i} className="usi-btn sm" href={link.url} target="_blank" rel="noopener">
          <SourceBadge source={link.source} /> Źródło <Icon name="arrow" size={11} />
        </a>
      ))}
      {inv.website && (
        <a className="usi-btn sm" href={inv.website} target="_blank" rel="noopener">
          www <Icon name="arrow" size={11} />
        </a>
      )}
      {inv.coords && inv.coords[0] !== 0 && (
        <a className="usi-btn sm" href={`https://www.google.com/maps/@${inv.coords[0]},${inv.coords[1]},780m/`} target="_blank" rel="noopener">
          <Icon name="map" size={11} /> Maps
        </a>
      )}
    </div>
  );
}

function HeroBand({ inv, showMap }) {
  return (
    <div data-component="HeroBand" style={{ display: 'grid', gridTemplateColumns: showMap && inv.coords && inv.coords[0] !== 0 ? '1fr 280px' : '1fr', gap: 16, padding: '16px 24px 0', flexShrink: 0 }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
          <h1 className="usi-h1" style={{ margin: 0 }}>{inv.name}</h1>
          <span className="usi-body" style={{ color: 'var(--usi-ink-3)' }}>{inv.developer}</span>
          <div style={{ flex: 1 }} />
          <SourceLinks inv={inv} />
        </div>
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: 'var(--usi-ink-3)' }}>
          {inv.address && <span>📍 {inv.address}</span>}
          {inv.units > 0 && <span className="usi-mono">{inv.units} mieszk.</span>}
          {inv.price_avg > 0 && <span className="usi-mono">{inv.price_avg.toLocaleString('pl-PL')} zł/m²</span>}
          <span className="usi-mono">{inv.delivery}</span>
          {inv.amenities && inv.amenities.length > 0 && <span>{inv.amenities.length} udogodnień</span>}
        </div>
      </div>
      {showMap && inv.coords && inv.coords[0] !== 0 && (
        <MiniMap coords={inv.coords} label={inv.district} height={70}
          hereUrl={inv.here_map_url} hereUrlDark={inv.here_map_url_dark} />
      )}
    </div>
  );
}

// ─── Tryb C: galeria full-width + sticky pasek ocen na dole ──
function ModeC({ inv, density = 4, ratingVariant, showMap, marked, onToggleMark, onLightbox,
    ratings = {}, handleRating, comment = '', handleComment, saved = false, focusedCat = -1, onFocusedCatChange }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div data-component="ModeC" style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      <HeroBand inv={inv} showMap={showMap} />
      <SlideShow photos={inv.photos || []} marked={marked} onToggleMark={onToggleMark}
        onLightbox={onLightbox} style={{ marginTop: 16 }} />
      <div style={{
        position: 'sticky', bottom: 0,
        background: 'var(--usi-surface)',
        borderTop: '.5px solid var(--usi-border)',
        boxShadow: '0 -8px 24px rgba(0,0,0,0.04)',
        padding: '12px 24px',
        flexShrink: 0,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div style={{ display: 'flex', gap: 16, flex: 1, flexWrap: 'wrap' }}>
            {USI_CATEGORIES.map((cat, idx) => (
              <div key={cat.key} onClick={() => onFocusedCatChange && onFocusedCatChange(idx)}
                style={{
                  display: 'flex', flexDirection: 'column', gap: 4,
                  background: idx === focusedCat ? 'rgba(0,0,0,0.05)' : 'transparent',
                  borderRadius: 6, padding: '3px 6px', margin: '0 -6px',
                  cursor: 'default', transition: 'background .12s',
                }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                  <span style={{ width: 5, height: 5, borderRadius: '50%', background: cat.color }} />
                  <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--usi-ink-2)' }}>{cat.key}</span>
                </div>
                <CategoryRating category={cat} value={ratings[cat.key] ?? null}
                  onChange={v => handleRating(cat.key, v)} variant={ratingVariant} size="sm" />
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, paddingLeft: 16, borderLeft: '.5px solid var(--usi-border)', flexShrink: 0 }}>
            {(() => { const score = ocenaLog({ ratings }); return (<>
              <ProgressRing value={score ?? 0} max={4} size={32} stroke={3} color="var(--usi-accent)" />
              <div>
                <div style={{ fontSize: 12, fontWeight: 600 }}>
                  {score !== null ? score.toFixed(2) : '—'}
                  <span style={{ fontWeight: 400, color: 'var(--usi-ink-3)' }}> / 4</span>
                </div>
                <UsiStarScore score={score} />
                <div className="usi-small" style={{ display: 'inline-flex', alignItems: 'center', gap: 4, color: saved ? 'var(--usi-success)' : 'var(--usi-ink-4)', transition: 'color .3s', marginTop: 1 }}>
                  <Icon name="check" size={10} /> {saved ? 'Zapisano' : 'Auto-zapis'}
                </div>
              </div>
            </>); })()}

            <button className="usi-btn sm ghost" onClick={() => setExpanded(e => !e)}>
              {expanded ? 'Zwiń' : 'Komentarz'}
            </button>
          </div>
        </div>
        {expanded && (
          <textarea className="usi-input usi-textarea" placeholder="Komentarz globalny…"
            value={comment} onChange={handleComment}
            style={{ marginTop: 10, minHeight: 64 }} />
        )}
      </div>
    </div>
  );
}

// ─── Widok inwestycji: 3 kolumny 50/25/25 ────────────────────
function DetailRightPanel({ inv, invIndex = 0, invTotal = 1, onBack, onNav, onPrev, onNext, density = 5, ratingVariant = 'circles', showMap = true, dark, onToggleTheme }) {
  const [marked, setMarked] = React.useState(new Set());
  const [hiddenPhotos, setHiddenPhotos] = React.useState(new Set());
  const [lightbox, setLightbox] = React.useState(null);
  const [deleteMsg, setDeleteMsg] = React.useState('');
  const [navOpen, setNavOpen] = React.useState(false);
  const [detailMode, setDetailMode] = React.useState('A');
  const [focusedCat, setFocusedCat] = React.useState(-1);
  const { ratings, setRatings, comment, setComment, status, setStatus, saved, handleRating, handleComment, handleStatus } = useRatings(inv);

  React.useEffect(() => {
    setMarked(new Set());
    setHiddenPhotos(new Set());
    setDeleteMsg('');
    setFocusedCat(-1);
  }, [inv.slug]);

  // Keyboard shortcuts for ratings: 1-6 select category, -/= adjust rating
  React.useEffect(() => {
    const CATS = USI_CATEGORIES.map(c => c.key);
    const handler = (e) => {
      if (lightbox != null) return;
      const tag = e.target.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;
      if (e.key >= '1' && e.key <= '6') {
        e.preventDefault();
        setFocusedCat(parseInt(e.key) - 1);
      } else if ((e.key === '-' || e.key === '_') && focusedCat >= 0) {
        e.preventDefault(); e.stopPropagation();
        const cat = CATS[focusedCat];
        handleRating(cat, Math.max(0, (ratings[cat] || 0) - 1));
      } else if ((e.key === '=' || e.key === '+') && focusedCat >= 0) {
        e.preventDefault(); e.stopPropagation();
        const cat = CATS[focusedCat];
        handleRating(cat, Math.min(4, (ratings[cat] || 0) + 1));
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [lightbox, focusedCat, ratings]);

  const toggleMark = (i) => {
    const s = new Set(marked);
    s.has(i) ? s.delete(i) : s.add(i);
    setMarked(s);
  };

  const handleSaveDelete = () => {
    const paths = [...marked].map(i => inv.photos[i]).filter(Boolean);
    fetch(`/api/mark-delete/${inv.developer_slug}/${inv.investment_slug}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ paths }),
    })
      .then(() => {
        setHiddenPhotos(prev => new Set([...prev, ...paths]));
        setMarked(new Set());
        setDeleteMsg(`Ukryto ${paths.length} zdjęć`);
        setTimeout(() => setDeleteMsg(''), 3000);
      })
      .catch(() => {});
  };

  const visiblePhotos = (inv.photos || []).filter(p => !hiddenPhotos.has(p));

  const toolbar = (
    <div style={{
      display: 'flex', alignItems: 'center', gap: 10,
      padding: '10px 24px', borderBottom: '.5px solid var(--usi-border)',
      background: 'var(--usi-surface)', flexShrink: 0, fontSize: 13,
      position: 'relative'
    }}>
      <NavMenuButton onClick={() => setNavOpen(true)} />
      <button className="usi-btn ghost" onClick={onBack}><Icon name="chevronLeft" /> Powrót</button>
      <span className="usi-small">{invIndex + 1} z {invTotal}</span>
      <div style={{ flex: 1 }} />
      {deleteMsg && (
        <span className="usi-small" style={{ color: 'var(--usi-success)', display: 'inline-flex', alignItems: 'center', gap: 5 }}>
          <Icon name="check" size={11} /> {deleteMsg}
        </span>
      )}
      {marked.size > 0 ? (
        <>
          <span className="usi-pill danger">
            <Icon name="trash" size={11} /> {marked.size} do usunięcia
          </span>
          <button className="usi-btn ghost sm" onClick={() => setMarked(new Set())} title="Cofnij wszystkie">
            <Icon name="undo" size={12} /> Cofnij
          </button>
          <button className="usi-btn sm danger" onClick={handleSaveDelete}>
            <Icon name="trash" size={12} /> Zatwierdź ({marked.size})
          </button>
        </>
      ) : (
        <span className="usi-small" style={{ display: 'inline-flex', alignItems: 'center', gap: 5, color: 'var(--usi-ink-4)' }}>
          <Icon name="info" size={12} /> Kliknij <Icon name="trash" size={11} /> przy zdjęciu, by oznaczyć
        </span>
      )}
      <div style={{
        display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2,
        border: '.5px solid var(--usi-border)',
      }}>
        {['A', 'C'].map(m => (
          <button key={m} onClick={() => setDetailMode(m)}
            style={{
              border: 'none', borderRadius: 6,
              background: detailMode === m ? 'var(--usi-surface)' : 'transparent',
              color: detailMode === m ? 'var(--usi-ink)' : 'var(--usi-ink-3)',
              fontWeight: 600, fontSize: 12, cursor: 'pointer', fontFamily: 'inherit',
              padding: '3px 10px', height: 26,
              boxShadow: detailMode === m ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
              transition: 'all .12s',
            }}>{m}</button>
        ))}
      </div>
      <button className="usi-btn ghost icon" onClick={onPrev} title="Poprzednia"><Icon name="chevronLeft" /></button>
      <button className="usi-btn ghost icon" onClick={onNext} title="Następna"><Icon name="chevron" /></button>
      {navOpen && <NavDrawer current="detail" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav && onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
    </div>
  );

  return (
    <div data-component="DetailRightPanel" className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {toolbar}

      {detailMode === 'A' ? (
        <>
          <HeroBand inv={inv} showMap={showMap} />
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr', flex: 1, overflow: 'hidden', marginTop: 16 }}>
            <div style={{ padding: '0 8px 24px 24px', overflow: 'auto' }} className="usi-scroll">
              <Gallery inv={{...inv, photos: visiblePhotos}} columns={density} marked={marked} onToggleMark={toggleMark} onLightbox={setLightbox} />
            </div>
            <aside style={{
              borderLeft: '.5px solid var(--usi-border)',
              background: 'var(--usi-surface)',
              padding: '16px 18px',
              overflow: 'auto',
              display: 'flex', flexDirection: 'column', gap: 16,
            }} className="usi-scroll">
              <RatingsPanel inv={inv} variant={ratingVariant}
                ratings={ratings} handleRating={handleRating}
                comment={comment} handleComment={handleComment}
                status={status} handleStatus={handleStatus} saved={saved}
                focusedCat={focusedCat} onFocusedCatChange={setFocusedCat} />
            </aside>
            <aside style={{
              borderLeft: '.5px solid var(--usi-border)',
              background: 'var(--usi-surface)',
              padding: '16px 18px',
              overflow: 'auto',
              display: 'flex', flexDirection: 'column', gap: 16,
            }} className="usi-scroll">
              <MetadataBlock inv={inv} />
            </aside>
          </div>
        </>
      ) : (
        <ModeC inv={{...inv, photos: visiblePhotos}} density={density + 1} ratingVariant={ratingVariant} showMap={showMap}
          marked={marked} onToggleMark={toggleMark} onLightbox={setLightbox}
          ratings={ratings} handleRating={handleRating}
          comment={comment} handleComment={handleComment} saved={saved}
          focusedCat={focusedCat} onFocusedCatChange={setFocusedCat} />
      )}

      {lightbox != null && <Lightbox inv={{...inv, photos: visiblePhotos}} index={lightbox} onClose={() => setLightbox(null)} />}
    </div>
  );
}

Object.assign(window, { DetailRightPanel, MetadataBlock });
