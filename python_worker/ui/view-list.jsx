// view-list.jsx — widok listy inwestycji

function ListGrid({ 
  investments = [], 
  filteredInvestments = [],
  onSelectInv = () => {}, 
  onNav = () => {},
  search, onSearch,
  filterDev, onFilterDev,
  filterStatus, onFilterStatus,
  activeSources, onSetActiveSources,
  activeCities, onSetActiveCities,
  dark, onToggleTheme
}) {
  const [mode, setMode] = React.useState('grid');
  
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

  // Zgodnie z Krok B04 i B05: generowanie kontekstu dla modułów
  const getModuleContext = React.useCallback(() => {
    return {
      visibleInvestments: filteredInvestments,
      sumApartments: extractModuleContext.sumApartments(filteredInvestments),
      avgRating: extractModuleContext.avgListRating(filteredInvestments),
      statsByQuarter: extractModuleContext.aggregateByQuarter(filteredInvestments)
    };
  }, [filteredInvestments]);

  React.useEffect(() => {
    console.log("[ListGrid] getModuleContext() generated:", getModuleContext());
  }, [getModuleContext]);

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

  const developers = React.useMemo(() => {
    const s = new Set();
    investments.forEach(i => { if (i.developer) s.add(i.developer); });
    return Array.from(s).sort();
  }, [investments]);

  const toggleSource = (id, isShift) => {
    onSetActiveSources(prev => {
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
    onSetActiveCities(prev => {
      if (city === null) return new Set();
      const next = new Set(prev);
      if (isShift) return new Set([city]);
      if (next.has(city)) next.delete(city);
      else next.add(city);
      return next;
    });
  };

  // Virtualization logic
  const rowHeight = mode === 'grid' ? 340 : 56;
  const viewHeight = dimensions.height || 800;
  const availableWidth = Math.max(dimensions.width - 48, 320);
  const itemsPerRow = mode === 'grid' ? Math.max(1, Math.floor(availableWidth / 220)) : 1; 
  const overscanRows = 4;
  
  const totalRows = Math.ceil(filteredInvestments.length / itemsPerRow);
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscanRows);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewHeight) / rowHeight) + overscanRows);
  
  const visibleItems = filteredInvestments.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * rowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * rowHeight);

  return (
    <div data-component="ListGrid" className="usi-app list-grid-container">
      <ListToolbar 
        mode={mode} onModeChange={setMode} 
        count={filteredInvestments.length} total={investments.length} 
        search={search} onSearch={onSearch}
        developers={developers}
        filterDev={filterDev} onFilterDev={setFilterDev}
        filterStatus={filterStatus} onFilterStatus={setFilterStatus}
        onNav={onNav}
        activeSources={activeSources} onToggleSource={toggleSource}
        activeCities={activeCities} onToggleCity={toggleCity}
        dark={dark} onToggleTheme={onToggleTheme}
      />
      
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        className="list-content-scroll usi-scroll"
      >
        <div style={{ height: paddingTop }} />
        <div className="list-grid-layout" style={{ 
            display: mode === 'grid' ? 'grid' : 'block', 
            gridTemplateColumns: mode === 'grid' ? `repeat(${itemsPerRow}, 1fr)` : 'none'
        }}>
          {mode === 'grid' ? (
            visibleItems.map(inv => <ListCard key={inv.slug} inv={inv} onSelect={() => onSelectInv(inv)} />)
          ) : (
            <ListTableContent investments={visibleItems} onSelectInv={onSelectInv} />
          )}
        </div>
        <div style={{ height: paddingBottom }} />
        
        {filteredInvestments.length === 0 && (
          <div className="list-empty-state">
            <div className="list-empty-icon">🔍</div>
            <div className="usi-body">Brak wyników dla podanych filtrów</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ListToolbar({ mode, onModeChange, count, total, search, onSearch, developers, filterDev, onFilterDev, filterStatus, onFilterStatus, onNav, activeSources, onToggleSource, activeCities, onToggleCity, dark, onToggleTheme }) {
  const [navOpen, setNavOpen] = React.useState(false);

  return (
    <div data-component="ListToolbar" className="list-toolbar">
      <div data-component="ListToolbar-Top" className="list-toolbar-top">
        <div data-component="ListToolbar-Nav" className="list-toolbar-nav">
          <NavMenuButton onClick={() => setNavOpen(true)} />
          <h1 data-component="ListToolbar-Title" className="usi-h2 list-toolbar-title">Inwestycje</h1>
          <span data-component="ListToolbar-Count" className="usi-pill outline">{count}{count !== total ? '/' + total : ''}</span>
        </div>
        <div style={{ flex: 1, minWidth: 20 }} />
        <div data-component="ListToolbar-Search" className="list-toolbar-search">
          <span className="list-toolbar-search-icon"><Icon name="search" /></span>
          <input data-component="Search-Input" className="usi-input list-toolbar-search-input" placeholder="Szukaj inwestycji, dewelopera, dzielnicy…"
            value={search} onChange={e => onSearch(e.target.value)} />
        </div>
        <div data-component="ListToolbar-Filters" className="list-toolbar-filters">
          <select data-component="Filter-Developer" className="usi-input filter-select-dev"
            value={filterDev} onChange={e => onFilterDev(e.target.value)}>
            <option value="">Wszyscy deweloperzy</option>
            {developers.map(d => {
              const val = typeof d === 'string' ? d : (d.developer_slug || d.name);
              const label = typeof d === 'string' ? d : d.name;
              return <option key={val} value={val}>{label}</option>;
            })}
          </select>
          <select data-component="Filter-Status" className="usi-input filter-select-status"
            value={filterStatus} onChange={e => onFilterStatus(e.target.value)}>
            <option value="">Wszystkie statusy</option>
            {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <div data-component="ModeToggle" className="mode-toggle">
            <button className="usi-btn icon sm mode-toggle-btn" title="Siatka kart" aria-pressed={mode === 'grid'}
              onClick={() => onModeChange('grid')}><Icon name="grid" /></button>
            <button className="usi-btn icon sm mode-toggle-btn" title="Tabela" aria-pressed={mode === 'table'}
              onClick={() => onModeChange('table')}><Icon name="list" /></button>
          </div>
        </div>
        {navOpen && <NavDrawer current="list" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      <div data-component="ListToolbar-Bottom" className="list-toolbar-bottom">
        <div data-component="Filter-Sources" className="filter-group">
          <span className="filter-group-label">Źródła</span>
          {SOURCES.map(s => (
            <FilterChip key={s.id} label={s.label} source={s.id} active={activeSources.has(s.id)} color={s.color} onClick={(isShift) => onToggleSource(s.id, isShift)} />
          ))}
        </div>
        <div className="filter-divider" />
        <div data-component="Filter-Cities" className="filter-group">
          <span className="filter-group-label">Miasta</span>
          {MAIN_CITIES.map(city => (
            <FilterChip key={city} label={city} active={activeCities.has(city)} onClick={(isShift) => onToggleCity(city, isShift)} />
          ))}
          {activeCities.size > 0 && (
            <button className="usi-btn ghost sm" onClick={() => onToggleCity(null, true)} style={{ padding: '4px 8px', fontSize: 11 }}>Wyczyść</button>
          )}
        </div>
      </div>
    </div>
  );
}

function ListCard({ inv, onSelect }) {
  const score = ocenaLog(inv);
  const avg = avgRating(inv);
  const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;

  return (
    <StandardCard
      data-component="ListCard"
      image={thumb}
      title={inv.name}
      subtitle={inv.developer}
      extra={inv.district}
      onClick={onSelect}
      badges={<SourceBadge source={inv.source} />}
      footerLeft={<CategoryStripe ratings={inv.ratings || {}} />}
      footerRight={
        <div className="list-card-avg-box">
          <Icon name="star" size={12} />
          <span className="usi-mono" style={{ fontWeight: 600 }}>{avg.toFixed(2)}</span>
        </div>
      }
    />
  );
}

function ListTableContent({ investments = [], onSelectInv }) {
  return (
    <div data-component="ListTableContent" className="usi-card list-table-container">
      <table className="list-table">
        <thead className="list-table-head">
          <tr>
            <th className="list-table-th" style={{ width: 60 }}></th>
            <th className="list-table-th">Inwestycja</th>
            <th className="list-table-th">Deweloper</th>
            <th className="list-table-th">Dzielnica</th>
            <th className="list-table-th" style={{ textAlign: 'right' }}>Ocena</th>
          </tr>
        </thead>
        <tbody>
          {investments.map(inv => {
            const score = ocenaLog(inv);
            const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
            return (
              <tr key={inv.slug} className="list-table-tr" onClick={() => onSelectInv(inv)}>
                <td className="list-table-td">
                  {thumb ? <img src={thumb} alt="" className="list-table-thumb" /> : <div className="list-table-thumb-empty" />}
                </td>
                <td className="list-table-td">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <SourceBadge source={inv.source} />
                    <span style={{ fontWeight: 600 }}>{inv.name}</span>
                  </div>
                </td>
                <td className="list-table-td">{inv.developer}</td>
                <td className="list-table-td" style={{ color: 'var(--usi-ink-3)' }}>{inv.district}</td>
                <td className="list-table-td" style={{ textAlign: 'right' }}>
                  {score !== null ? <span className="usi-pill success usi-mono">{score.toFixed(2)}</span> : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { ListGrid, ListTableContent });
