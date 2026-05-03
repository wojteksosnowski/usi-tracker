// view-dev-list.jsx — widok listy deweloperów

function DeveloperListGrid({ 
  developers = [], 
  onSelectDev = () => {}, 
  onNav = () => {},
  dark, onToggleTheme
}) {
  const [search, setSearch] = React.useState('');
  const [activeSources, setActiveSources] = React.useState(new Set(['RP', 'OTO', 'TO']));
  const [activeCities, setActiveCities] = React.useState(new Set());
  
  // Virtualization state
  const containerRef = React.useRef(null);
  const [scrollTop, setScrollTop] = React.useState(0);
  const [dimensions, setDimensions] = React.useState({ 
    width: window.innerWidth, 
    height: window.innerHeight 
  });

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };

  React.useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  const toggleSource = (id, isShift) => {
    setActiveSources(prev => {
      const next = new Set(prev);
      if (isShift) return new Set([id]);
      if (next.has(id)) {
        if (next.size > 1) next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const toggleCity = (city, isShift) => {
    setActiveCities(prev => {
      if (city === null) return new Set();
      const next = new Set(prev);
      if (isShift) return new Set([city]);
      if (next.has(city)) next.delete(city);
      else next.add(city);
      return next;
    });
  };

  const filteredDevelopers = React.useMemo(() => {
    return developers.filter(d => {
      // 1. Search
      if (search) {
        const s = search.toLowerCase();
        const match = (
          d.name.toLowerCase().includes(s) || 
          d.developer_slug.toLowerCase().includes(s) ||
          (d.usi_dev_id && d.usi_dev_id.toLowerCase().includes(s))
        );
        if (!match) return false;
      }

      // 2. Sources
      if (activeSources.size > 0) {
        const mapping = d.portal_mapping || {};
        const hasRp = !!mapping.rp;
        const hasOto = !!mapping.oto;
        const hasTo = !!mapping.to;
        
        let matchSource = false;
        if (activeSources.has('RP') && hasRp) matchSource = true;
        if (activeSources.has('OTO') && hasOto) matchSource = true;
        if (activeSources.has('TO') && hasTo) matchSource = true;
        
        if (!matchSource) return false;
      }

      // 3. Cities (best effort based on metadata or name)
      if (activeCities.size > 0) {
        const metadata = d.metadata || {};
        const address = (metadata.address || '').toLowerCase();
        const foundCity = MAIN_CITIES.find(c => address.includes(c.toLowerCase()) || d.name.toLowerCase().includes(c.toLowerCase()));
        if (!foundCity || !activeCities.has(foundCity)) return false;
      }

      return true;
    });
  }, [developers, search, activeSources, activeCities]);

  const rowHeight = 340;
  const viewHeight = dimensions.height || 800;
  const availableWidth = Math.max(dimensions.width - 48, 320);
  const itemsPerRow = Math.max(1, Math.floor(availableWidth / 220)); 
  const overscanRows = 4;
  
  const totalRows = Math.ceil(filteredDevelopers.length / itemsPerRow);
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscanRows);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewHeight) / rowHeight) + overscanRows);
  
  const visibleItems = filteredDevelopers.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * rowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * rowHeight);

  return (
    <div data-component="DeveloperListGrid" className="usi-app developer-list-container">
      <DeveloperListToolbar
        count={filteredDevelopers.length} total={developers.length}
        search={search} onSearch={setSearch}
        onNav={onNav}
        activeSources={activeSources} onToggleSource={toggleSource}
        activeCities={activeCities} onToggleCity={toggleCity}
        dark={dark} onToggleTheme={onToggleTheme}
      />
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        className="developer-list-content usi-scroll"
      >
        <div style={{ paddingTop, paddingBottom, minHeight: '100%' }}>
          <div className="developer-grid-layout" style={{ 
            gridTemplateColumns: `repeat(${itemsPerRow}, 1fr)`, 
          }}>
            {visibleItems.map(dev => <DeveloperCard key={dev.usi_dev_id} dev={dev} onSelect={() => onSelectDev(dev)} />)}
          </div>
        </div>
        
        {filteredDevelopers.length === 0 && (
          <div className="developer-empty-state">
            <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
            <div className="usi-body">Brak deweloperów pasujących do filtrów</div>
          </div>
        )}
      </div>
    </div>
  );
}

function DeveloperListToolbar({ count, total, search, onSearch, onNav, activeSources, onToggleSource, activeCities, onToggleCity, dark, onToggleTheme }) {
  const [navOpen, setNavOpen] = React.useState(false);

  const Chip = ({ label, active, onClick, color, source }) => (
    <button
      onClick={(e) => onClick(e.shiftKey)}
      data-active={active}
      className="filter-chip"
      style={{
        borderColor: active ? (color || 'var(--usi-accent)') : 'var(--usi-border)',
        background: active ? (color ? color + '15' : 'rgba(229, 0, 109, 0.1)') : 'var(--usi-surface)',
        color: active ? (color || 'var(--usi-accent)') : 'var(--usi-ink-3)',
      }}
    >
      {source && <window.SourceBadge source={source} />}
      <span style={{ marginLeft: source ? 6 : 0 }}>{label}</span>
    </button>
  );

  return (
    <div data-component="DeveloperListToolbar" className="developer-list-toolbar">
      <div className="developer-list-toolbar-top">
        <div className="developer-list-toolbar-title-box">
          <window.NavMenuButton onClick={() => setNavOpen(true)} />
          <h1 className="usi-h1" style={{ margin: 0, fontSize: 20 }}>Deweloperzy</h1>
          <span className="usi-pill outline">{count}{count !== total ? '/' + total : ''}</span>
        </div>
        <div style={{ flex: 1, minWidth: 20 }} />
        <div className="developer-list-toolbar-search">
          <span style={{ position: 'absolute', left: 10, top: 9, color: 'var(--usi-ink-4)' }}><window.Icon name="search" /></span>
          <input className="usi-input" placeholder="Szukaj dewelopera po nazwie lub USI ID…"
            value={search} onChange={e => onSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: 32, borderRadius: 20 }} />
        </div>
        {navOpen && <window.NavDrawer current="developers" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      
      <div data-component="ListToolbar-Bottom" className="developer-list-toolbar-bottom">
        <div data-component="Filter-Sources" className="filter-group">
          <span className="filter-group-label">Źródła</span>
          {SOURCES.map(s => (
            <Chip key={s.id} label={s.label} source={s.id} active={activeSources.has(s.id)} color={s.color} onClick={(isShift) => onToggleSource(s.id, isShift)} />
          ))}
        </div>
        <div className="filter-divider" />
        <div data-component="Filter-Cities" className="filter-group" style={{ flexWrap: 'wrap' }}>
          <span className="filter-group-label">Miasta</span>
          {MAIN_CITIES.map(city => (
            <Chip key={city} label={city} active={activeCities.has(city)} onClick={(isShift) => onToggleCity(city, isShift)} />
          ))}
          {activeCities.size > 0 && (
            <button className="usi-btn ghost sm" onClick={() => onToggleCity(null, true)} style={{ padding: '4px 8px', fontSize: 11 }}>Wyczyść</button>
          )}
        </div>
      </div>
    </div>
  );
}

function DeveloperCard({ dev, onSelect }) {
  const portals = dev.portal_mapping || {};
  const hasRp = !!portals.rp;
  const hasOto = !!portals.oto;
  const hasTo = !!portals.to;

  return (
    <window.StandardCard
      title={dev.name}
      subtitle={dev.usi_dev_id}
      extra={dev.developer_slug}
      onClick={onSelect}
      badges={
        <>
          {hasRp && <window.SourceBadge source="rp" />}
          {hasOto && <window.SourceBadge source="oto" />}
          {hasTo && <window.SourceBadge source="to" />}
        </>
      }
      footerLeft={
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--usi-ink)' }}>
            {dev.investments_count || 0} 
            <small style={{ fontWeight: 400, opacity: 0.6 }}> inwestycji</small>
          </div>
          {dev.website && <div className="usi-tiny" style={{ opacity: 0.6, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{dev.website}</div>}
        </div>
      }
      footerRight={dev.suggestions && dev.suggestions.length > 0 && (
        <div className="usi-pill outline usi-mono" style={{ fontSize: 10, borderColor: 'var(--usi-accent)', color: 'var(--usi-accent)' }}>
          Sugestie: {dev.suggestions.length}
        </div>
      )}
    />
  );
}

Object.assign(window, { DeveloperListGrid });
