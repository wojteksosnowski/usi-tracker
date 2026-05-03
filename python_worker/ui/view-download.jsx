const { React } = window;

window.ViewDownload = function ViewDownload({ dark, onNav, onToggleTheme }) {
  // Extract components inside to ensure they are available on window
  const { 
    Icon, 
    Spinner,
    NavDrawer,
    NavMenuButton,
    SourceBadge,
    StandardCard
  } = window;

  const [portal, setPortal] = React.useState('rp');
  const [identifier, setIdentifier] = React.useState('');
  const [selectedDev, setSelectedDev] = React.useState('');
  
  // Use shared hook for developers
  const devHook = window.useDevelopers ? window.useDevelopers() : { developers: [] };
  const developers = Array.isArray(devHook.developers) ? devHook.developers : [];
  
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [showOnlyNew, setShowOnlyNew] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [successMsg, setSuccessMsg] = React.useState('');
  const [registering, setRegistering] = React.useState({}); // { [idx]: true }
  const [navOpen, setNavOpen] = React.useState(false);
  const [activePortals, setActivePortals] = React.useState({ rp: true, oto: true, to: true });
  const [batchProgress, setBatchProgress] = React.useState(null); // { current, total }

  const handleSearch = async () => {
    if (!identifier) return;
    setLoading(true);
    setError(null);
    setResults([]);
    setShowOnlyNew(false);
    try {
      const response = await fetch(`/api/discovery/${portal}?id=${encodeURIComponent(identifier)}`);
      const data = await response.json();
      if (response.ok) {
        const items = Array.isArray(data) ? data : [];
        setResults(items);
        
        // Auto-detect portal from URL
        if (identifier.includes('otodom.pl')) setPortal('oto');
        else if (identifier.includes('rynekpierwotny.pl')) setPortal('rp');
        else if (identifier.includes('tabelaofert.pl')) setPortal('to');

        // Auto-select developer if name matches
        if (items.length > 0) {
          const combinedNames = items.map(i => i.name || '').join(' ').toLowerCase();
          const found = developers.find(d => {
            if (!d) return false;
            const name = typeof d === 'string' ? d : (d.name || '');
            const slug = typeof d === 'string' ? d.toLowerCase().replace(/-/g, ' ') : (d.developer_slug || '').replace(/-/g, ' ');
            return combinedNames.includes(slug) || combinedNames.includes(name.toLowerCase());
          });
          if (found) setSelectedDev(typeof found === 'string' ? found : (found.developer_slug || ''));
        }

      } else {
        const errTxt = typeof data.error === 'string' ? data.error : 'Błąd podczas wyszukiwania';
        setError(errTxt);
      }
    } catch (err) {
      setError('Błąd połączenia z serwerem');
    } finally {
      setLoading(false);
    }
  };

  const handleGlobalScan = async () => {
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const promises = [];
      if (activePortals.rp) promises.push(fetch('/api/discovery/rp').then(r => r.ok ? r.json() : []).catch(() => []));
      if (activePortals.oto) promises.push(fetch('/api/discovery/oto').then(r => r.ok ? r.json() : []).catch(() => []));
      if (activePortals.to) promises.push(fetch('/api/discovery/to').then(r => r.ok ? r.json() : []).catch(() => []));
      
      const res = await Promise.all(promises);
      const combined = res.flat().filter(Boolean);
      
      setResults(combined);
      setShowOnlyNew(true); 
    } catch (err) {
      setError('Błąd połączenia podczas skanowania globalnego');
    } finally {
      setLoading(false);
    }
  };

  const handleBatchDownload = async () => {
    if (!selectedDev) {
      setError('Wybierz dewelopera przed masowym pobieraniem');
      return;
    }

    const toDownload = results.filter(r => r && r.is_new && !r.registered);
    if (toDownload.length === 0) {
      setError('Brak nowych inwestycji do pobrania');
      return;
    }

    setLoading(true);
    setBatchProgress({ current: 0, total: toDownload.length, itemName: 'Przygotowanie...' });
    
    let successCount = 0;
    for (let i = 0; i < toDownload.length; i++) {
      const item = toDownload[i];
      const itemName = typeof item.name === 'string' ? item.name : 'Inwestycja';
      setBatchProgress({ current: i + 1, total: toDownload.length, itemName: itemName });
      
      try {
        let itemPortal = 'rp';
        if (item.url?.includes('otodom.pl')) itemPortal = 'oto';
        else if (item.url?.includes('tabelaofert.pl')) itemPortal = 'to';
        else if (item.portal) itemPortal = item.portal; 

        const response = await fetch('/api/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            portal: itemPortal,
            dev_slug: selectedDev,
            inv_slug: item.slug,
            name: item.name,
            id: item.id,
            url: item.url
          })
        });
        
        if (response.ok) {
          successCount++;
          setResults(prev => prev.map(it => it.id === item.id ? { ...it, registered: true } : it));
        }
      } catch (err) {
        console.error(`Failed to download ${item.name}`, err);
      }
    }

    setSuccessMsg(`Pomyślnie pobrano ${successCount} nowości.`);
    setTimeout(() => setSuccessMsg(''), 5000);
    setLoading(false);
    setBatchProgress(null);
  };

  const handleRegister = async (item, idx) => {
    if (!selectedDev) {
      setError('Wybierz dewelopera przed rejestracją');
      return;
    }

    setRegistering(prev => ({ ...prev, [idx]: true }));
    try {
      const response = await fetch('/api/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          portal,
          dev_slug: selectedDev,
          inv_slug: item.slug,
          name: item.name,
          id: item.id,
          url: item.url
        })
      });
      const data = await response.json();
      if (response.ok) {
        setSuccessMsg(`Zarejestrowano pomyślnie: ${item.name}`);
        setResults(prev => prev.map((it, i) => i === idx ? { ...it, registered: true } : it));
        setTimeout(() => setSuccessMsg(''), 4000);
      } else {
        const errTxt = typeof data.error === 'string' ? data.error : 'Błąd podczas rejestracji';
        setError(errTxt);
      }
    } catch (err) {
      setError('Błąd połączenia');
    } finally {
      setRegistering(prev => ({ ...prev, [idx]: false }));
    }
  };

  const filteredResults = Array.isArray(results) 
    ? (showOnlyNew ? results.filter(r => r && r.is_new) : results.filter(Boolean))
    : [];

  const safeRender = (val, fallback = '') => {
    if (typeof val === 'string' || typeof val === 'number') return val;
    return fallback;
  };

  const Chip = ({ label, active, onClick, color, source }) => (
    <button
      onClick={() => onClick()}
      data-active={active}
      className="filter-chip"
      style={{
        borderColor: active ? (color || 'var(--usi-accent)') : 'var(--usi-border)',
        background: active ? (color ? color + '15' : 'rgba(229, 0, 109, 0.1)') : 'var(--usi-surface)',
        color: active ? (color || 'var(--usi-accent)') : 'var(--usi-ink-3)',
      }}
    >
      {source && SourceBadge && <SourceBadge source={source} />}
      <span style={{ marginLeft: source ? 6 : 0 }}>{safeRender(label)}</span>
    </button>
  );

  const ProgressBar = ({ current, total, label }) => {
    const percent = total > 0 ? Math.round((current / total) * 100) : 0;
    return (
      <div data-component="ProgressBar" className="progress-bar-container">
        <div className="progress-bar-info">
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
            {safeRender(label, 'Pobieranie...')}
          </span>
          <span>{current} / {total} ({percent}%)</span>
        </div>
        <div className="progress-bar-bg">
          <div className="progress-bar-fill" style={{ width: `${percent}%` }} />
        </div>
      </div>
    );
  };

  return (
    <div data-component="ViewDownload" className="usi-app download-view-container">
      {/* Toolbar - System Style */}
      <div data-component="ListToolbar" className="download-toolbar">
        {/* Toolbar Top: Global Nav, Search, Portal Select */}
        <div data-component="ListToolbar-Top" className="download-toolbar-top">
          <div data-component="ListToolbar-Nav" style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            {NavMenuButton && <NavMenuButton onClick={() => setNavOpen(true)} />}
            <h1 className="usi-h1" style={{ margin: 0, fontSize: 20 }}>Pobieranie</h1>
            <span className="usi-pill outline">{results.length}</span>
          </div>

          <div style={{ flex: 1, minWidth: 20 }} />

          {/* Quick Identifier Input */}
          <div data-component="ListToolbar-Search" className="download-search-box">
            <div style={{ position: 'relative', flex: 1 }}>
              <span style={{ position: 'absolute', left: 10, top: 9, color: 'var(--usi-ink-4)' }}>{Icon && <Icon name="search" />}</span>
              <input 
                className="usi-input" 
                placeholder="Wklej URL lub ID inwestycji/dewelopera..."
                value={identifier} 
                onChange={e => setIdentifier(e.target.value)}
                style={{ width: '100%', paddingLeft: 32, borderRadius: 20, height: 34 }} 
              />
            </div>
            <select 
              className="usi-input" 
              value={portal} 
              onChange={e => setPortal(e.target.value)}
              style={{ width: 'auto', height: 34, borderRadius: 20, fontSize: 12, fontWeight: 600 }}
            >
              <option value="rp">RP</option>
              <option value="oto">OTO</option>
              <option value="to">TO</option>
            </select>
            <button 
              className="usi-btn primary" 
              style={{ height: 34, borderRadius: 20, padding: '0 16px', fontSize: 12, fontWeight: 700 }}
              disabled={loading || !identifier}
              onClick={handleSearch}
            >
              ANALIZUJ
            </button>
          </div>

          <div data-component="ListToolbar-Filters" className="download-filters-box">
            <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 11, fontWeight: 700, color: 'var(--usi-ink-3)', textTransform: 'uppercase' }}>
              <input 
                type="checkbox" 
                checked={showOnlyNew} 
                onChange={e => setShowOnlyNew(e.target.checked)}
                style={{ width: 14, height: 14 }}
              />
              Tylko nowe
            </label>
            {successMsg && (
              <div style={{ background: 'var(--usi-success)', color: '#fff', padding: '4px 12px', borderRadius: 12, fontSize: 11, fontWeight: 700 }}>
                {safeRender(successMsg)}
              </div>
            )}
          </div>
          
          {navOpen && NavDrawer && <NavDrawer current="download" onClose={() => setNavOpen(false)} onNav={onNav} dark={dark} onToggleTheme={onToggleTheme} />}
        </div>

        {/* Toolbar Bottom: Batch Controls & Discovery */}
        <div data-component="ListToolbar-Bottom" className="download-toolbar-bottom">
          <div data-component="Filter-Sources" className="filter-group">
            <span className="filter-group-label">Skanuj</span>
            {['rp', 'oto', 'to'].map(p => (
              <Chip 
                key={p} 
                label={p === 'rp' ? 'RynekPierwotny' : p === 'oto' ? 'Otodom' : 'TabelaOfert'} 
                active={activePortals[p]} 
                onClick={() => setActivePortals(prev => ({ ...prev, [p]: !prev[p] }))} 
                color={p === 'rp' ? '#E5006D' : p === 'oto' ? '#00e5a1' : '#2980b9'}
              />
            ))}
            <button 
              className="usi-btn primary sm" 
              style={{ height: 28, borderRadius: 14, fontSize: 11, padding: '0 12px' }}
              disabled={loading || !Object.values(activePortals).some(v => v)}
              onClick={handleGlobalScan}
            >
              {loading && !batchProgress && Spinner ? <Spinner size={12} stroke={2} /> : 'ZESKANUJ NOWOŚCI'}
            </button>
          </div>

          <div className="filter-divider" />

          {batchProgress ? (
            <ProgressBar 
              current={batchProgress.current} 
              total={batchProgress.total} 
              label={`Pobieranie: ${batchProgress.itemName}`} 
            />
          ) : (
            <div data-component="Batch-Download" className="download-batch-box">
              <span className="filter-group-label">Deweloper</span>
              <select className="usi-input" value={selectedDev} onChange={e => setSelectedDev(e.target.value)} style={{ width: 'auto', height: 28, minWidth: 200, borderRadius: 6, fontSize: 12 }}>
                <option value="">Wybierz z bazy...</option>
                {developers.map(dev => {
                  if (!dev) return null;
                  const val = typeof dev === 'string' ? dev : (dev.developer_slug || '');
                  const label = typeof dev === 'string' ? dev : (dev.name || '');
                  return <option key={val} value={val}>{safeRender(label, val)}</option>;
                })}
              </select>
              
              <button 
                className="usi-btn success sm" 
                style={{ 
                  height: 28, borderRadius: 14, fontSize: 11, fontWeight: 700,
                  color: '#fff'
                }}
                disabled={loading || !selectedDev || results.filter(r => r && r.is_new && !r.registered).length === 0}
                onClick={handleBatchDownload}
              >
                {`POBIERZ NOWOŚCI (${results.filter(r => r && r.is_new && !r.registered).length})`}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="download-content usi-scroll">
        {error && (
          <div className="download-error-banner">
            {Icon && <Icon name="close" size={14} />} {safeRender(error)}
          </div>
        )}

        {results.length === 0 && !loading && (
          <div className="download-empty-state">
            <div style={{ marginBottom: 16 }}>
              {Icon && <Icon name="download" size={48} stroke={1} />}
            </div>
            <div className="usi-h2" style={{ marginBottom: 8 }}>Gotowy do pobierania</div>
            <div className="usi-body" style={{ textAlign: 'center', maxWidth: 400 }}>
              Wklej link do oferty lub profilu dewelopera powyżej, <br/>albo zaznacz portale i kliknij "ZESKANUJ NOWOŚCI".
            </div>
          </div>
        )}

        {loading && results.length === 0 && (
          <div className="usi-app-loading" style={{ height: 'auto', marginTop: 100 }}>
            {Spinner && <Spinner size={40} />}
            <div className="usi-h3" style={{ opacity: 0.6, marginTop: 16 }}>Skanowanie źródeł...</div>
          </div>
        )}

        {results.length > 0 && (
          <div className="download-grid-layout">
            {filteredResults.map((item, idx) => {
              if (!item) return null;
              const portalColor = item.portal === 'rp' ? '#C0392B' : (item.portal === 'oto' ? '#002C57' : '#5A4A2A');
              const isRegistering = registering[idx];

              return (
                <StandardCard
                  key={idx}
                  title={safeRender(item.name, 'Brak nazwy')}
                  subtitle={safeRender(item.address, 'Brak adresu')}
                  extra={`ID: ${safeRender(item.id || item.slug, '??')}`}
                  disabled={item.registered || isRegistering || !selectedDev}
                  onClick={() => handleRegister(item, idx)}
                  image={
                    item.image && typeof item.image === 'string' ? item.image : (
                      <div style={{ 
                        width: '100%', height: '100%', background: portalColor, 
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'rgba(255,255,255,0.2)'
                      }}>
                        {Icon && <Icon name={item.portal === 'rp' ? 'building' : (item.portal === 'oto' ? 'grid' : 'search')} size={64} />}
                      </div>
                    )
                  }
                  badges={
                    <>
                      {SourceBadge && <SourceBadge source={item.portal} url={item.url} />}
                      {item.is_new && (
                        <span className="usi-pill success" style={{ fontSize: 9, padding: '2px 6px', fontWeight: 900 }}>NOWA</span>
                      )}
                    </>
                  }
                  overlay={
                    isRegistering ? (Spinner && <Spinner size={24} stroke={2} />) : 
                    (item.registered ? <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>{Icon && <Icon name="check" size={18} />} W BAZIE</div> : null)
                  }
                  footerLeft={
                    !item.registered && !isRegistering && selectedDev && (
                      <div className="usi-tiny" style={{ color: 'var(--usi-accent)' }}>KLIKNIJ ABY DODAĆ</div>
                    )
                  }
                />
              );
            })}
          </div>
        )}
        
        {filteredResults.length === 0 && results.length > 0 && (
          <div style={{ textAlign: 'center', padding: '60px 0', opacity: 0.5 }}>
             Nie znaleziono nowych inwestycji. Wyłącz "Tylko nowe", aby zobaczyć wszystkie.
          </div>
        )}
      </div>
    </div>
  );
};
