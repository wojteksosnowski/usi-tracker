// view-detail.jsx — widok inwestycji (rdzeń: HeroBand, ModeC, DetailRightPanel)

function SourceLinks({ inv }) {
  const { SourceBadge, Icon } = window;
  const links = inv.source_links || [{ source: inv.source, url: inv.source_url }];
  return (
    <div data-component="SourceLinks" className="source-links" style={{ display: 'flex', gap: 8 }}>
      {links.map((link, i) => (
        <a key={i} className="usi-btn sm ghost" href={link.url} target="_blank" rel="noopener" style={{ padding: '4px 8px' }}>
          <SourceBadge source={link.source} /> <Icon name="arrow" size={11} />
        </a>
      ))}
    </div>
  );
}

function HeroBand({ inv, showMap, moduleContext, detailMode, onModeChange }) {
  const { 
    React, Icon, MiniMap,
    WeightedUsiScore, ModuleWrapper, 
    ocenaLog, ModuleTypes
  } = window;
  const score = ocenaLog(inv);
  const hasMap = showMap && inv.coords && inv.coords[0] !== 0;

  return (
    <div data-component="HeroBand" className="hero-band" style={{
      display: 'grid',
      gridTemplateColumns: hasMap ? '1fr auto 280px' : '1fr auto',
      gap: 24,
      paddingBottom: 24,
      borderBottom: '.5px solid var(--usi-border)',
      marginBottom: 24
    }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 4 }}>
          <h1 className="usi-h1" style={{ margin: 0 }}>{inv.name}</h1>
          <span className="usi-body" style={{ opacity: 0.6 }}>{inv.developer}</span>
        </div>
        <div style={{ display: 'flex', gap: 16, color: 'var(--usi-ink-3)', fontSize: 13, marginBottom: 12 }}>
          {inv.address && <span>📍 {inv.address}</span>}
          {inv.price_avg > 0 && <span className="usi-mono">{inv.price_avg.toLocaleString('pl-PL')} zł/m²</span>}
          <span className="usi-mono">{inv.delivery}</span>
        </div>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
            <SourceLinks inv={inv} />
            <div style={{ width: 1, height: 16, background: 'var(--usi-border)' }} />
            <div style={{ display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2 }}>
                <button className="usi-btn sm ghost" style={{ background: detailMode === 'A' ? 'var(--usi-surface)' : 'transparent', fontSize: 11 }} onClick={() => onModeChange('A')}>Standard</button>
                <button className="usi-btn sm ghost" style={{ background: detailMode === 'C' ? 'var(--usi-surface)' : 'transparent', fontSize: 11 }} onClick={() => onModeChange('C')}>Media</button>
            </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center' }}>
        <WeightedUsiScore score={score} size={56} />
      </div>

      {hasMap && moduleContext && (
        <div style={{ height: 100, borderRadius: 12, overflow: 'hidden', border: '.5px solid var(--usi-border)' }}>
            <MiniMap coords={inv.coords} height="100%" />
        </div>
      )}
    </div>
  );
}

function ModeC({ inv, marked, onToggleMark, onLightbox, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange }) {
  const { React, SlideShow, RatingsPanel } = window;
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
}

function DetailsA({ inv, ratings, handleRating, comment, handleComment, status, handleStatus, saved, focusedCat, onFocusedCatChange, metaConfig, moduleContext }) {
  const { MetadataPanel, RatingsPanel, ModuleWrapper, NearbyInvestmentsModule, ModuleTypes, Gallery } = window;
  const [marked, setMarked] = React.useState(new Set());
  const [lightbox, setLightbox] = React.useState(null);
  
  return (
    <div data-component="DetailsA" style={{ display: 'grid', gridTemplateColumns: '1fr 340px 300px', gap: 24, flex: 1, overflow: 'hidden' }}>
      <div style={{ padding: '0 8px 24px 0', overflow: 'auto' }} className="usi-scroll">
         <Gallery 
            inv={inv} 
            columns={3} 
            marked={marked} 
            onToggleMark={(idx) => {
                const next = new Set(marked);
                if (next.has(idx)) next.delete(idx); else next.add(idx);
                setMarked(next);
            }} 
            onLightbox={setLightbox} 
         />
         <div style={{ height: 24 }} />
         <MetadataPanel inv={inv} config={metaConfig} />
      </div>

      <div style={{ borderLeft: '.5px solid var(--usi-border)', padding: '0 18px', overflow: 'auto' }} className="usi-scroll">
         <RatingsPanel 
            inv={inv} ratings={ratings} handleRating={handleRating} 
            comment={comment} handleComment={handleComment}
            status={status} handleStatus={handleStatus}
            saved={saved} focusedCat={focusedCat}
            onFocusedCatChange={onFocusedCatChange}
         />
      </div>

      <div style={{ borderLeft: '.5px solid var(--usi-border)', padding: '0 0 0 18px', overflow: 'auto' }} className="usi-scroll">
         <ModuleWrapper 
            component={NearbyInvestmentsModule}
            moduleSpec={{
              inputs: { items: { type: ModuleTypes.RecordSet, from: 'nearbyInvestments' } }
            }}
            context={window.useDataBus().bus}
            title="W okolicy"
            icon="map"
            height={400}
         />
      </div>
      {lightbox !== null && <window.Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
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

function NearbyInvestmentsModule({ items = [] }) {
  if (items.length === 0) return <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak innych inwestycji w promieniu 5km.</div>;
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.slice(0, 10).map(i => (
        <div key={i.slug} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
          <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--usi-accent)' }} />
          <div style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{i.name}</div>
          <div className="usi-mono" style={{ opacity: 0.6 }}>{i.distance.toFixed(1)}km</div>
        </div>
      ))}
    </div>
  );
}

function DetailRightPanel({ inv, onBack, onUpdateInv }) {
  const { React, useDataBus, Icon, useRatings, useMetadataConfig, extractModuleContext } = window;
  const [detailMode, setDetailMode] = React.useState('A');
  const [marked, setMarked] = React.useState(new Set());
  const [focusedCat, setFocusedCat] = React.useState(-1);
  
  const { Lightbox, USI_CATEGORIES } = window;
  const [lightbox, setLightbox] = React.useState(null);

  const { ratings, handleRating, comment, handleComment, status, handleStatus, saved } = useRatings(inv);
  const metaConfig = useMetadataConfig();
  const { bus, setVariable } = useDataBus();

  const getModuleContext = React.useCallback(() => {
    return {
      currentInvestment: inv,
      geo: extractModuleContext.extractGeoPoint(inv),
      district: inv.district,
    };
  }, [inv, extractModuleContext]);

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
          return dist <= 5;
        })
        .map(other => ({ 
          ...other, 
          distance: getDistance(lat, lng, other.coords[0], other.coords[1]) 
        }))
        .sort((a, b) => a.distance - b.distance);
      setVariable('nearbyInvestments', nearby);
    }
  }, [inv.slug, bus.visibleInvestments, setVariable]);

  // Keyboard shortcuts
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
        e.preventDefault();
        const cat = CATS[focusedCat];
        handleRating(cat, Math.max(0, (ratings[cat] || 0) - 1));
      } else if ((e.key === '=' || e.key === '+') && focusedCat >= 0) {
        e.preventDefault();
        const cat = CATS[focusedCat];
        handleRating(cat, Math.min(4, (ratings[cat] || 0) + 1));
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [lightbox, focusedCat, ratings, USI_CATEGORIES, handleRating]);

  return (
    <div data-component="DetailRightPanel" className="usi-scroll" style={{ height: '100%', overflowY: detailMode === 'C' ? 'hidden' : 'auto', padding: '24px', display: 'flex', flexDirection: 'column' }}>
      <HeroBand 
        inv={inv} 
        showMap={true} 
        detailMode={detailMode} 
        onModeChange={setDetailMode} 
        moduleContext={getModuleContext()}
      />

      {detailMode === 'C' ? (
        <ModeC 
            inv={inv} 
            marked={marked} 
            onToggleMark={(idx) => {
                const next = new Set(marked);
                if (next.has(idx)) next.delete(idx); else next.add(idx);
                setMarked(next);
            }} 
            onLightbox={setLightbox}
            ratings={ratings}
            handleRating={handleRating}
            comment={comment}
            handleComment={handleComment}
            status={status}
            handleStatus={handleStatus}
            saved={saved}
            focusedCat={focusedCat}
            onFocusedCatChange={setFocusedCat}
        />
      ) : (
        <DetailsA 
            inv={inv}
            ratings={ratings}
            handleRating={handleRating}
            comment={comment}
            handleComment={handleComment}
            status={status}
            handleStatus={handleStatus}
            saved={saved}
            focusedCat={focusedCat}
            onFocusedCatChange={setFocusedCat}
            metaConfig={metaConfig}
            moduleContext={getModuleContext()}
        />
      )}

      {lightbox !== null && <Lightbox inv={inv} index={lightbox} onClose={() => setLightbox(null)} />}
    </div>
  );
}

Object.assign(window, { DetailRightPanel });
