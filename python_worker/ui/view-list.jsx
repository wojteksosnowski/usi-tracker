// view-list.jsx — widok listy inwestycji

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin'];
const SOURCES = [
  { id: 'RP', label: 'RynekPierwotny', color: '#0052FF' },
  { id: 'OTO', label: 'Otodom', color: '#00E676' },
  { id: 'TO', label: 'TabelaOfert', color: '#FF9800' }
];

function ListGrid({ investments = [], onSelectInv = () => {}, onNav = () => {} }) {
  const [mode, setMode] = React.useState('grid');
  const [search, setSearch] = React.useState('');
  const [filterDev, setFilterDev] = React.useState('');
  const [filterStatus, setFilterStatus] = React.useState('');
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

  const developers = React.useMemo(() => {
    const s = new Set();
    investments.forEach(i => { if (i.developer) s.add(i.developer); });
    return Array.from(s).sort();
  }, [investments]);

  const filtered = React.useMemo(() => {
    return investments.filter(inv => {
      if (search) {
        const s = search.toLowerCase();
        const match = (inv.name?.toLowerCase().includes(s) ||
                     inv.developer?.toLowerCase().includes(s) ||
                     inv.district?.toLowerCase().includes(s) ||
                     inv.address?.toLowerCase().includes(s));
        if (!match) return false;
      }
      if (filterDev && inv.developer !== filterDev) return false;
      if (filterStatus && inv.status !== filterStatus) return false;
      if (activeSources.size > 0 && inv.source && !activeSources.has(inv.source.toUpperCase())) return false;
      if (activeCities.size > 0) {
        const addr = (inv.address || '').toLowerCase();
        const foundCity = MAIN_CITIES.find(c => addr.includes(c.toLowerCase()));
        if (!foundCity || !activeCities.has(foundCity)) return false;
      }
      return true;
    });
  }, [investments, search, filterDev, filterStatus, activeSources, activeCities]);

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

  // Virtualization logic
  const rowHeight = mode === 'grid' ? 340 : 56;
  const viewHeight = dimensions.height || 800;
  const availableWidth = Math.max(dimensions.width - 48, 320);
  const itemsPerRow = mode === 'grid' ? Math.max(1, Math.floor(availableWidth / 220)) : 1; 
  const overscanRows = 4;
  
  const totalRows = Math.ceil(filtered.length / itemsPerRow);
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscanRows);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewHeight) / rowHeight) + overscanRows);
  
  const visibleItems = filtered.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * rowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * rowHeight);

  return (
    <div className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <ListToolbar
        mode={mode} onModeChange={setMode}
        count={filtered.length} total={investments.length}
        search={search} onSearch={setSearch}
        developers={developers} filterDev={filterDev} onFilterDev={setFilterDev}
        filterStatus={filterStatus} onFilterStatus={setFilterStatus}
        onNav={onNav}
        activeSources={activeSources} onToggleSource={toggleSource}
        activeCities={activeCities} onToggleCity={toggleCity}
      />
      <div 
        ref={containerRef}
        onScroll={handleScroll}
        style={{ padding: '0 24px 32px', overflow: 'auto', flex: 1, position: 'relative' }} 
        className="usi-scroll"
      >
        <div style={{ paddingTop, paddingBottom, minHeight: '100%' }}>
          {mode === 'grid' ? (
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: `repeat(${itemsPerRow}, 1fr)`, 
              gap: 16,
              paddingTop: 20
            }}>
              {visibleItems.map(inv => <ListCard key={inv.slug} inv={inv} onSelect={() => onSelectInv(inv)} />)}
            </div>
          ) : (
            <div style={{ paddingTop: 16 }}>
              <ListTableContent investments={visibleItems} onSelectInv={onSelectInv} />
            </div>
          )}
        </div>
        
        {filtered.length === 0 && (
          <div style={{ textAlign: 'center', color: 'var(--usi-ink-4)', padding: '60px 0' }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
            <div className="usi-body">Brak wyników dla podanych filtrów</div>
          </div>
        )}
      </div>
    </div>
  );
}

function ListToolbar({ mode, onModeChange, count, total, search, onSearch, developers, filterDev, onFilterDev, filterStatus, onFilterStatus, onNav, activeSources, onToggleSource, activeCities, onToggleCity }) {
  const [navOpen, setNavOpen] = React.useState(false);

  const Chip = ({ label, active, onClick, color, source }) => (
    <button
      onClick={(e) => onClick(e.shiftKey)}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '6px 12px',
        borderRadius: '16px',
        fontSize: '11px',
        fontWeight: 700,
        cursor: 'pointer',
        border: '1.5px solid ' + (active ? (color || 'var(--usi-accent)') : 'var(--usi-border)'),
        background: active ? (color ? color + '15' : 'var(--usi-accent-10)') : 'var(--usi-surface)',
        color: active ? (color || 'var(--usi-accent)') : 'var(--usi-ink-3)',
        transition: 'all 0.15s ease',
        boxShadow: active ? '0 2px 4px rgba(0,0,0,0.06)' : 'none',
        outline: 'none',
        textTransform: 'uppercase',
        letterSpacing: '0.02em'
      }}
    >
      {source && <SourceBadge source={source} />}
      <span style={{ marginLeft: source ? 6 : 0 }}>{label}</span>
    </button>
  );

  return (
    <div style={{
      display: 'flex', flexDirection: 'column',
      borderBottom: '.5px solid var(--usi-border)',
      background: 'var(--usi-surface)', flexShrink: 0,
      boxShadow: '0 2px 6px rgba(0,0,0,0.03)'
    }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 12,
        padding: '14px 24px', flexWrap: 'wrap', rowGap: 12
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
          <NavMenuButton onClick={() => setNavOpen(true)} />
          <h1 className="usi-h1" style={{ margin: 0, fontSize: 20 }}>Inwestycje</h1>
          <span className="usi-pill outline">{count}{count !== total ? '/' + total : ''}</span>
        </div>
        <div style={{ flex: 1, minWidth: 20 }} />
        <div style={{ position: 'relative', flex: '1 1 200px', maxWidth: 400 }}>
          <span style={{ position: 'absolute', left: 10, top: 9, color: 'var(--usi-ink-4)' }}><Icon name="search" /></span>
          <input className="usi-input" placeholder="Szukaj inwestycji, dewelopera, dzielnicy…"
            value={search} onChange={e => onSearch(e.target.value)}
            style={{ width: '100%', paddingLeft: 32, borderRadius: 20 }} />
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center' }}>
          <select className="usi-input" style={{ width: 'auto', height: 34, minWidth: 160, borderRadius: 8 }}
            value={filterDev} onChange={e => onFilterDev(e.target.value)}>
            <option value="">Wszyscy deweloperzy</option>
            {developers.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
          <select className="usi-input" style={{ width: 'auto', height: 34, borderRadius: 8 }}
            value={filterStatus} onChange={e => onFilterStatus(e.target.value)}>
            <option value="">Wszystkie statusy</option>
            {USI_STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <div style={{ display: 'flex', gap: 2, padding: 2, background: 'var(--usi-surface-3)', borderRadius: 8 }}>
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
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '0 24px 14px', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Źródła</span>
          {SOURCES.map(s => (
            <Chip key={s.id} label={s.label} source={s.id} active={activeSources.has(s.id)} color={s.color} onClick={(isShift) => onToggleSource(s.id, isShift)} />
          ))}
        </div>
        <div style={{ width: 1, height: 20, background: 'var(--usi-border)' }} />
        <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Miasta</span>
          {MAIN_CITIES.map(city => (
            <Chip key={city} label={city} active={activeCities.has(city)} onClick={(isShift) => onToggleCity(city, isShift)} />
          ))}
          {activeCities.size > 0 && (
            <button className="usi-btn ghost sm" onClick={() => onToggleCity(null, true)} style={{ padding: '4px 8px', fontSize: 11 }}>Wyczyść</button>
          )}
        </div>
      </div>
      {navOpen && <NavDrawer current="list" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} />}
    </div>
  );
}

function ListCard({ inv, onSelect }) {
  const score = ocenaLog(inv);
  const avg = avgRating(inv);
  const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
  return (
    <article className="usi-card" onClick={onSelect} style={{ display: 'flex', flexDirection: 'column', cursor: 'pointer', height: 320, background: 'var(--usi-surface)' }}>
      <div style={{ position: 'relative', height: 160, background: 'var(--usi-surface-3)', overflow: 'hidden' }}>
        {thumb ? <img src={thumb} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover' }} /> : <div style={{ width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--usi-ink-4)', fontSize: 32 }}>📷</div>}
        <div style={{ position: 'absolute', top: 10, left: 10, display: 'flex', gap: 6 }}>
          <SourceBadge source={inv.source} />
        </div>
      </div>
      <div style={{ padding: '12px 14px', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          <h3 className="usi-h3" style={{ margin: 0, marginBottom: 2, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inv.name}</h3>
          <div className="usi-small" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{inv.developer}</div>
          <div className="usi-tiny" style={{ marginTop: 4, opacity: 0.7 }}>{inv.district}</div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--usi-ink)' }}>{inv.price_avg > 0 ? (inv.price_avg / 1000).toFixed(1) + 'k' : '—'} <small style={{ fontWeight: 400, opacity: 0.6 }}>zł/m²</small></div>
            <div className="usi-tiny" style={{ opacity: 0.6 }}>{inv.delivery}</div>
          </div>
          {score !== null && (
            <div style={{ textAlign: 'right' }}>
              <div className="usi-pill success usi-mono" style={{ fontSize: 11, fontWeight: 700 }}>{score.toFixed(2)}</div>
              {avg > 0 && <div style={{ fontSize: 10, fontWeight: 600, color: 'var(--usi-accent)', marginTop: 2 }}>★ {avg.toFixed(1)}</div>}
            </div>
          )}
        </div>
      </div>
    </article>
  );
}

function ListTableContent({ investments = [], onSelectInv = () => {} }) {
  return (
    <div className="usi-card flat" style={{ background: 'var(--usi-surface)', borderRadius: 12, overflow: 'hidden' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
        <thead>
          <tr style={{ background: 'var(--usi-surface-2)' }}>
            <th className="usi-tiny" style={{ padding: '11px 12px', textAlign: 'left', borderBottom: '.5px solid var(--usi-border)' }}></th>
            <th className="usi-tiny" style={{ padding: '11px 12px', textAlign: 'left', borderBottom: '.5px solid var(--usi-border)' }}>Inwestycja</th>
            <th className="usi-tiny" style={{ padding: '11px 12px', textAlign: 'left', borderBottom: '.5px solid var(--usi-border)' }}>Deweloper</th>
            <th className="usi-tiny" style={{ padding: '11px 12px', textAlign: 'left', borderBottom: '.5px solid var(--usi-border)' }}>Lokalizacja</th>
            <th className="usi-tiny" style={{ padding: '11px 12px', textAlign: 'right', borderBottom: '.5px solid var(--usi-border)' }}>Wynik</th>
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
