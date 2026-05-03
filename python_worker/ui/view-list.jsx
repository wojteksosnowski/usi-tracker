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
    <div data-component="ListGrid" className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <ListToolbar 
        mode={mode} onModeChange={setMode} 
        count={filteredInvestments.length} total={investments.length} 
        search={search} onSearch={onSearch}
        developers={developers}
        filterDev={filterDev} onFilterDev={onFilterDev}
        filterStatus={filterStatus} onFilterStatus={onFilterStatus}
        onNav={onNav}
        activeSources={activeSources} onToggleSource={toggleSource}
        activeCities={activeCities} onToggleCity={toggleCity}
        dark={dark} onToggleTheme={onToggleTheme}
      />
      
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        style={{ padding: '0 24px 32px', overflow: 'auto', flex: 1, position: 'relative' }}
        className="usi-scroll"
      >
        <div style={{ height: paddingTop }} />
        <div style={{ 
            display: mode === 'grid' ? 'grid' : 'block', 
            gridTemplateColumns: mode === 'grid' ? `repeat(${itemsPerRow}, 1fr)` : 'none',
            gap: 16,
        }}>
          {mode === 'grid' ? (
            visibleItems.map(inv => <ListCard key={inv.slug} inv={inv} onSelect={() => onSelectInv(inv)} />)
          ) : (
            <ListTableContent investments={visibleItems} onSelectInv={onSelectInv} />
          )}
        </div>
        <div style={{ height: paddingBottom }} />
        
        {filteredInvestments.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--usi-ink-4)', padding: '60px 0' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
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
    <div data-component="ListToolbar" style={{
      display: 'flex', flexDirection: 'column',
      borderBottom: '.5px solid var(--usi-border)',
      background: 'var(--usi-surface)', flexShrink: 0,
      boxShadow: '0 2px 6px rgba(0,0,0,0.03)'
    }}>
      <div data-component="ListToolbar-Top" style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '16px 24px', flexWrap: 'wrap', rowGap: 12,
        position: 'relative'
      }}>
        <div data-component="ListToolbar-Nav" style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
          <NavMenuButton onClick={() => setNavOpen(true)} />
          <h1 data-component="ListToolbar-Title" className="usi-h2" style={{ margin: 0 }}>Inwestycje</h1>
          <span data-component="ListToolbar-Count" className="usi-pill outline">{count}{count !== total ? '/' + total : ''}</span>
        </div>
        <div style={{ flex: 1, minWidth: 20 }} />
        <div data-component="ListToolbar-Search" style={{ position: 'relative', flex: '1 1 200px', maxWidth: 400 }}>
          <span style={{ position: 'absolute', left: 10, top: 9, color: 'var(--usi-ink-4)' }}><Icon name="search" /></span>
          <input data-component="Search-Input" className="usi-input" placeholder="Szukaj inwestycji, dewelopera, dzielnicy…"
            value={search} onChange={e => onSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: 32, borderRadius: 20 }} />
        </div>
        <div data-component="ListToolbar-Filters" style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <select data-component="Filter-Developer" className="usi-input" style={{ width: 'auto', height: 34, minWidth: 160, borderRadius: 8 }}
            value={filterDev} onChange={e => onFilterDev(e.target.value)}>
            <option value="">Wszyscy deweloperzy</option>
            {developers.map(d => {
              const val = typeof d === 'string' ? d : (d.developer_slug || d.name);
              const label = typeof d === 'string' ? d : d.name;
              return <option key={val} value={val}>{label}</option>;
            })}
          </select>
          <select data-component="Filter-Status" className="usi-input" style={{ width: 'auto', height: 34, borderRadius: 8 }}
            value={filterStatus} onChange={e => onFilterStatus(e.target.value)}>
            <option value="">Wszystkie statusy</option>
            {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <div data-component="ModeToggle" style={{ display: 'flex', gap: 2, padding: 2, background: 'var(--usi-surface-3)', borderRadius: 8 }}>
            <button className="usi-btn icon sm" title="Siatka kart" aria-pressed={mode === 'grid'}
              onClick={() => onModeChange('grid')}
              style={{
                background: mode === 'grid' ? 'var(--usi-surface)' : 'transparent', border: 'none',
                color: mode === 'grid' ? 'var(--usi-ink)' : 'var(--usi-ink-3)',
                boxShadow: mode === 'grid' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                borderRadius: 6
              }}><Icon name="grid" /></button>
            <button className="usi-btn icon sm" title="Tabela" aria-pressed={mode === 'table'}
              onClick={() => onModeChange('table')}
              style={{
                background: mode === 'table' ? 'var(--usi-surface)' : 'transparent', border: 'none',
                color: mode === 'table' ? 'var(--usi-ink)' : 'var(--usi-ink-3)',
                boxShadow: mode === 'table' ? '0 1px 2px rgba(0,0,0,0.06)' : 'none',
                borderRadius: 6
              }}><Icon name="list" /></button>
          </div>
        </div>
        {navOpen && <NavDrawer current="list" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      <div data-component="ListToolbar-Bottom" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '0 24px 14px', flexWrap: 'wrap' }}>
        <div data-component="Filter-Sources" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Źródła</span>
          {SOURCES.map(s => (
            <FilterChip key={s.id} label={s.label} source={s.id} active={activeSources.has(s.id)} color={s.color} onClick={(isShift) => onToggleSource(s.id, isShift)} />
          ))}
        </div>
        <div style={{ width: 1, height: 20, background: 'var(--usi-border)' }} />
        <div data-component="Filter-Cities" style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Miasta</span>
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
          <Icon name="star" size={12} />
          <span className="usi-mono" style={{ fontWeight: 600 }}>{avg.toFixed(2)}</span>
        </div>
      }
    />
  );
}

function ListTableContent({ investments = [], onSelectInv }) {
  return (
    <div data-component="ListTableContent" className="usi-card" style={{ overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: 'var(--usi-surface-2)', borderBottom: '1px solid var(--usi-border)', textAlign: 'left' }}>
            <th style={{ padding: '12px', width: 60 }}></th>
            <th style={{ padding: '12px' }}>Inwestycja</th>
            <th style={{ padding: '12px' }}>Deweloper</th>
            <th style={{ padding: '12px' }}>Dzielnica</th>
            <th style={{ padding: '12px', textAlign: 'right' }}>Ocena</th>
          </tr>
        </thead>
        <tbody>
          {investments.map(inv => {
            const score = ocenaLog(inv);
            const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
            return (
              <tr key={inv.slug} style={{ borderBottom: '.5px solid var(--usi-border)', cursor: 'pointer' }} onClick={() => onSelectInv(inv)}>
                <td style={{ padding: '8px 12px' }}>
                  {thumb ? <img src={thumb} alt="" style={{ width: 36, height: 36, objectFit: 'cover', borderRadius: 4 }} /> : <div style={{ width: 36, height: 36, borderRadius: 4, background: 'var(--usi-surface-3)' }} />}
                </td>
                <td style={{ padding: '8px 12px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <SourceBadge source={inv.source} />
                    <span style={{ fontWeight: 600 }}>{inv.name}</span>
                  </div>
                </td>
                <td style={{ padding: '8px 12px' }}>{inv.developer}</td>
                <td style={{ padding: '8px 12px', color: 'var(--usi-ink-3)' }}>{inv.district}</td>
                <td style={{ padding: '8px 12px', textAlign: 'right' }}>
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
