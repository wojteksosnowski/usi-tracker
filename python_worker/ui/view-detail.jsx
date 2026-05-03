// view-detail.jsx — widok inwestycji (rdzeń: HeroBand, ModeC, DetailRightPanel)
// Komponenty galerii → view-detail-gallery.jsx
// Hook i panel ocen → view-detail-ratings.jsx

function SourceLinks({ inv }) {
  const links = inv.source_links || [{ source: inv.source, url: inv.source_url }];
  return (
    <div data-component="SourceLinks" className="source-links">
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

function HeroBand({ inv, showMap, moduleContext }) {
  const score = ocenaLog(inv);
  const hasMap = showMap && inv.coords && inv.coords[0] !== 0;

  // Specyfikacja dla modułu minimapy (Krok B07)
  const miniMapSpec = {
    inputs: {
      geo: { type: ModuleTypes.GeoPoint, required: true },
      label: { type: 'String', required: false, from: 'district' },
      hereUrl: { type: 'String', required: false },
      hereUrlDark: { type: 'String', required: false }
    },
    config: {
      zoom: 14
    }
  };

  return (
    <div data-component="HeroBand" className="hero-band" style={{
      gridTemplateColumns: hasMap ? '1fr auto 280px' : '1fr auto',
    }}>
      <div>
        <div data-component="HeroBand-TitleRow" className="hero-band-title-row">
          <h1 data-component="HeroBand-Title" className="usi-h1 hero-band-title">{inv.name}</h1>
          <span data-component="HeroBand-Developer" className="usi-body hero-band-developer">{inv.developer}</span>
          <div style={{ flex: 1 }} />
          <SourceLinks inv={inv} />
        </div>
        <div data-component="HeroBand-Stats" className="hero-band-stats">
          {inv.address && <span data-component="Stat-Address">📍 {inv.address}</span>}
          {inv.units > 0 && <span data-component="Stat-Units" className="usi-mono">{inv.units} mieszk.</span>}
          {inv.price_avg > 0 && <span data-component="Stat-Price" className="usi-mono">{inv.price_avg.toLocaleString('pl-PL')} zł/m²</span>}
          <span data-component="Stat-Delivery" className="usi-mono">{inv.delivery}</span>
          {inv.amenities && inv.amenities.length > 0 && <span data-component="Stat-Amenities">{inv.amenities.length} udogodnień</span>}
        </div>
      </div>

      <div className="hero-band-score-box">
        <WeightedUsiScore score={score} size={44} />
      </div>

      {hasMap && moduleContext && (
        <ModuleWrapper 
          component={MiniMap} 
          moduleSpec={miniMapSpec} 
          context={moduleContext} 
          height={70} 
        />
      )}
    </div>
  );
}

// ─── Tryb C: galeria full-width + sticky pasek ocen na dole ──
function ModeC({ inv, density = 4, ratingVariant, showMap, marked, onToggleMark, onLightbox,
    ratings = {}, handleRating, comment = '', handleComment, saved = false, focusedCat = -1, onFocusedCatChange, moduleContext }) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <div data-component="ModeC" className="mode-c-container">
      <HeroBand inv={inv} showMap={showMap} moduleContext={moduleContext} />
      <SlideShow photos={inv.photos || []} marked={marked} onToggleMark={onToggleMark}
        onLightbox={onLightbox} style={{ marginTop: 16 }} />
      <div className="mode-c-footer">
        <div className="mode-c-footer-content">
          <div className="mode-c-ratings-strip">
            {USI_CATEGORIES.map((cat, idx) => (
              <div key={cat.key} onClick={() => onFocusedCatChange && onFocusedCatChange(idx)}
                className="mode-c-rating-item"
                style={{
                  background: idx === focusedCat ? 'var(--usi-surface-2)' : 'transparent',
                }}>
                <div className="mode-c-rating-label">
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: cat.color }} />
                  <span style={{ fontSize: 10, fontWeight: 600, color: 'var(--usi-ink-2)' }}>{cat.key}</span>
                </div>
                <CategoryRating category={cat} value={ratings[cat.key] ?? null}
                  onChange={v => handleRating(cat.key, v)} variant={ratingVariant} size="sm" />
              </div>
            ))}
          </div>
          <div className="mode-c-score-box">
            {(() => { const score = ocenaLog({ ratings }); return (<>
              <ProgressRing value={score ?? 0} max={4} size={32} stroke={3} color="var(--usi-accent)" />
              <div className="mode-c-score-info">
                <div style={{ fontSize: 12, fontWeight: 600 }}>
                  {score !== null ? score.toFixed(2) : '—'}
                  <span style={{ fontWeight: 400, color: 'var(--usi-ink-3)' }}> / 4</span>
                </div>
                <UsiStarScore score={score} />
                <div className="usi-small mode-c-save-status" style={{ color: saved ? 'var(--usi-success)' : 'var(--usi-ink-4)' }}>
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

  // Zgodnie z Krok B04 i B05: generowanie kontekstu dla modułów
  const getModuleContext = React.useCallback(() => {
    return {
      currentInvestment: inv,
      geo: extractModuleContext.extractGeoPoint(inv),
      rating: avgRating(inv),
      color: 'var(--usi-accent)',
      district: inv.district,
      hereUrl: inv.here_map_url,
      hereUrlDark: inv.here_map_url_dark
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
    if (s.has(i)) s.delete(i); else s.add(i);
    setMarked(s);
  };

  const handleDeleteMarked = () => {
    if (marked.size === 0) return;
    if (!confirm(`Czy na pewno chcesz oznaczyć ${marked.size} zdjęć do usunięcia?`)) return;
    const slugs = Array.from(marked).map(idx => inv.photos[idx]);
    fetch(`/api/investment/${inv.developer_slug}/${inv.investment_slug}/delete-photos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ photos: slugs })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        setDeleteMsg(`${marked.size} zdjęć oznaczono do usunięcia.`);
        setMarked(new Set());
        setTimeout(() => setDeleteMsg(''), 3000);
      }
    });
  };

  const handleNav = (dir) => {
    if (dir === 'prev') onPrev(); else onNext();
  };

  const toolbar = (
    <div className="detail-toolbar">
      <NavMenuButton onClick={() => setNavOpen(true)} />
      <button className="usi-btn ghost" onClick={onBack}><Icon name="chevronLeft" /> Powrót</button>
      <div className="detail-toolbar-center">
        <div style={{ display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2 }}>
            <button className="usi-btn sm ghost" style={{ background: detailMode === 'A' ? 'var(--usi-surface)' : 'transparent', boxShadow: detailMode === 'A' ? 'var(--usi-shadow-sm)' : 'none' }} onClick={() => setDetailMode('A')}>Tryb A</button>
            <button className="usi-btn sm ghost" style={{ background: detailMode === 'C' ? 'var(--usi-surface)' : 'transparent', boxShadow: detailMode === 'C' ? 'var(--usi-shadow-sm)' : 'none' }} onClick={() => setDetailMode('C')}>Tryb C</button>
        </div>
      </div>
      <div className="detail-toolbar-nav">
        <button className="usi-btn sm ghost icon" onClick={() => handleNav('prev')} title="Poprzednia (strzałka góra)"><Icon name="chevronLeft" style={{ transform: 'rotate(90deg)' }} /></button>
        <span className="usi-small usi-mono detail-toolbar-pagination">{invIndex+1} / {invTotal}</span>
        <button className="usi-btn sm ghost icon" onClick={() => handleNav('next')} title="Następna (strzałka dół)"><Icon name="chevronLeft" style={{ transform: 'rotate(-90deg)' }} /></button>
      </div>
      {navOpen && <NavDrawer current="list" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
    </div>
  );

  if (detailMode === 'C') {
    return (
      <div data-component="DetailRightPanel" className="usi-app detail-right-panel">
        {toolbar}
        <ModeC inv={inv} marked={marked} onToggleMark={toggleMark} 
          onLightbox={idx => setLightbox(idx)}
          ratings={ratings} handleRating={handleRating}
          comment={comment} handleComment={handleComment}
          saved={saved} focusedCat={focusedCat} 
          onFocusedCatChange={setFocusedCat}
          moduleContext={getModuleContext()}
        />
        {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
      </div>
    );
  }

  return (
    <div data-component="DetailRightPanel" className="usi-app detail-right-panel">
      {toolbar}
      
      <HeroBand inv={inv} showMap={showMap} moduleContext={getModuleContext()} />

      {deleteMsg && (
        <div className="detail-msg-banner">
          <Icon name="check" /> {deleteMsg}
        </div>
      )}

      <div className="detail-grid">
        <div className="detail-gallery-column usi-scroll">
          <Gallery inv={inv} marked={marked} onToggleMark={toggleMark} onLightbox={setLightbox} columns={density} />
        </div>

        <div className="detail-ratings-column">
          <div className="detail-column-header">
            <h3 className="usi-h3" style={{ margin: 0 }}>Oceny i Akcje</h3>
            <div style={{ display: 'flex', gap: 6 }}>
                <button className="usi-btn sm ghost" onClick={handleReload} disabled={reloading}>{reloading ? '...' : 'Reload'}</button>
                <button className="usi-btn sm danger" onClick={handleDeleteMarked} disabled={marked.size === 0}>Usuń {marked.size > 0 ? `(${marked.size})` : ''}</button>
            </div>
          </div>
          <div className="detail-column-content usi-scroll">
            <RatingsPanel inv={inv} ratings={ratings} handleRating={handleRating} 
              comment={comment} handleComment={handleComment}
              status={status} handleStatus={handleStatus}
              saved={saved} focusedCat={focusedCat}
              onFocusedCatChange={setFocusedCat}
            />
          </div>
        </div>

        <aside className="detail-meta-column">
          <div className="detail-column-header">
            <h3 className="usi-h3" style={{ margin: 0 }}>Szczegóły</h3>
          </div>
          <div className="detail-column-content usi-scroll">
            <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
              <MetadataPanel inv={inv} config={metaConfig} />
              
              {inv.coords && (
                 <ModuleWrapper 
                   component={NearbyInvestmentsModule}
                   moduleSpec={{
                     inputs: { items: { type: ModuleTypes.RecordSet, from: 'nearbyInvestments' } }
                   }}
                   context={bus}
                   title="W okolicy"
                   icon="map"
                   height={240}
                 />
              )}
            </div>
          </div>
        </aside>
      </div>

      {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
    </div>
  );
}

function NearbyInvestmentsModule({ items = [] }) {
  if (items.length === 0) return <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak innych inwestycji w promieniu 5km.</div>;
  return (
    <div className="nearby-investments-list">
      {items.slice(0, 10).map(i => (
        <div key={i.slug} className="nearby-investment-item">
          <div className="nearby-investment-dot" />
          <div className="nearby-investment-name">{i.name}</div>
          <div className="usi-mono nearby-investment-distance">{i.distance.toFixed(1)}km</div>
        </div>
      ))}
    </div>
  );
}

Object.assign(window, { DetailRightPanel });
