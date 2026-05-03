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

function MetadataBlock({ inv, config }) {
  if (!config) return <div className="usi-tiny">Ładowanie metadanych...</div>;

  const getValue = (obj, path) => {
    return path.split('.').reduce((acc, part) => acc && acc[part], obj);
  };

  const renderValue = (val, type) => {
    if (val === null || val === undefined || val === '') return '—';
    if (type === 'currency' && typeof val === 'number') return `${val.toLocaleString('pl-PL')} zł/m²`;
    if (Array.isArray(val)) return val.length;
    return val;
  };

  return (
    <div data-component="MetadataBlock">
      <div className="usi-tiny" style={{ marginBottom: 8 }}>Metadane</div>
      <div data-component="MetadataBlock-Grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px 16px', fontSize: 13 }}>
        {config.map(field => {
          const val = getValue(inv, field.path);
          return <Row key={field.key} k={field.label} v={renderValue(val, field.type)} mono={field.type === 'currency' || field.type === 'count'} />;
        })}
        {inv.folder_path && (
          <div data-component="MetadataBlock-FolderPath" style={{ gridColumn: 'span 2', marginTop: 4 }}>
            <div className="usi-small" style={{ marginBottom: 1 }}>Ścieżka folderu</div>
            <div className="usi-mono" style={{ fontSize: 11, wordBreak: 'break-all', opacity: 0.8 }}>{inv.folder_path}</div>
          </div>
        )}
      </div>
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
  const score = ocenaLog(inv);
  const hasMap = showMap && inv.coords && inv.coords[0] !== 0;
  return (
    <div data-component="HeroBand" style={{
      display: 'grid',
      gridTemplateColumns: hasMap ? '1fr auto 280px' : '1fr auto',
      gap: 24, padding: '16px 24px 0', flexShrink: 0,
      alignItems: 'center'
    }}>
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

      <div style={{ display: 'flex', justifyContent: 'center', padding: '0 16px' }}>
        <WeightedUsiScore score={score} size={44} />
      </div>

      {hasMap && (
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

// ... existing ...

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

// ─── Widok inwestycji: 3 kolumny 50/25/25 ────────────────────
function DetailRightPanel({ inv, invIndex = 0, invTotal = 1, onBack, onNav, onUpdateInv, onPrev, onNext, density = 5, ratingVariant = 'circles', showMap = true, dark, onToggleTheme }) {
  const [marked, setMarked] = React.useState(new Set());
  const [hiddenPhotos, setHiddenPhotos] = React.useState(new Set());
  const [lightbox, setLightbox] = React.useState(null);
  const [deleteMsg, setDeleteMsg] = React.useState('');
  const [navOpen, setNavOpen] = React.useState(false);
  const [detailMode, setDetailMode] = React.useState('A');
  const [focusedCat, setFocusedCat] = React.useState(-1);
  const [reloading, setReloading] = React.useState(false);
  const { ratings, setRatings, comment, setComment, status, setStatus, saved, handleRating, handleComment, handleStatus } = useRatings(inv);
  const metaConfig = useMetadataConfig();
  const { bus, setVariable } = useDataBus();

  // Zgodnie z Krok B04: generowanie kontekstu dla modułów
  const getModuleContext = React.useCallback(() => {
    return {
      currentInvestment: inv,
      geo: inv.coords && inv.coords[0] !== 0 ? { lat: inv.coords[0], lng: inv.coords[1] } : null,
      rating: avgRating(inv),
      color: 'var(--usi-accent)'
    };
  }, [inv]);

  React.useEffect(() => {
    console.log("[DetailRightPanel] getModuleContext() generated:", getModuleContext());
  }, [getModuleContext]);

  React.useEffect(() => {
    setVariable('currentInvestment', inv);
    
    if (inv.coords && inv.coords[0] !== 0) {
      const [lat, lng] = inv.coords;
      const visible = bus.visibleInvestments || [];
      const nearby = visible
        .filter(other => {
          if (other.slug === inv.slug) return false;
          if (!other.coords || other.coords[0] === 0) return false;
          const dist = getDistance(lat, lng, other.coords[0], other.coords[1]);
          return dist <= 5; // 5 km radius
        })
        .map(other => ({ 
          ...other, 
          distance: getDistance(lat, lng, other.coords[0], other.coords[1]) 
        }))
        .sort((a, b) => a.distance - b.distance);
      
      setVariable('nearbyInvestments', nearby);
    } else {
      setVariable('nearbyInvestments', []);
    }
  }, [inv.slug, bus.visibleInvestments, setVariable]);

  // Global unmount cleanup
  React.useEffect(() => {
    return () => {
      setVariable('currentInvestment', null);
      setVariable('nearbyInvestments', []);
    };
  }, [setVariable]);

  React.useEffect(() => {
    setMarked(new Set());
    setHiddenPhotos(new Set());
    setDeleteMsg('');
    setFocusedCat(-1);
    setReloading(false);
  }, [inv.slug]);

  const handleReload = () => {
    setReloading(true);
    fetch(`/api/reload-investment/${inv.developer_slug}/${inv.investment_slug}`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data.ok && data.investment) {
          onUpdateInv && onUpdateInv(data.investment);
          setDeleteMsg('Dane zaktualizowane');
          setTimeout(() => setDeleteMsg(''), 3000);
        } else {
          alert("Błąd przeładowania: " + (data.error || "Nieznany błąd"));
        }
      })
      .catch(e => alert("Błąd połączenia: " + e.message))
      .finally(() => setReloading(false));
  };

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
      <button className="usi-btn ghost sm" onClick={handleReload} disabled={reloading} title="Pobierz świeże dane od dostawcy">
        {reloading ? <Spinner size={12} stroke={1.5} /> : <Icon name="sparkle" size={12} />}
        {reloading ? ' Pobieranie...' : ' Przeładuj'}
      </button>
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
              <MetadataBlock inv={inv} config={metaConfig} />
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
