const { React } = window;
const { 
  Icon, 
  Spinner,
  NavDrawer,
  NavMenuButton
} = window;

window.ViewDownload = function ViewDownload({ dark, onNav, onToggleTheme }) {
  const [portal, setPortal] = React.useState('rp');
  const [identifier, setIdentifier] = React.useState('');
  const [selectedDev, setSelectedDev] = React.useState('');
  const [developers, setDevelopers] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [showOnlyNew, setShowOnlyNew] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [successMsg, setSuccessMsg] = React.useState('');
  const [registering, setRegistering] = React.useState({}); // { [idx]: true }
  const [navOpen, setNavOpen] = React.useState(false);
  const [activePortals, setActivePortals] = React.useState({ rp: true, oto: true, to: true });
  const [batchProgress, setBatchProgress] = React.useState(null); // { current, total }

  React.useEffect(() => {
    fetch('/api/developers')
      .then(r => r.json())
      .then(setDevelopers)
      .catch(console.error);
  }, []);

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
        setResults(data);
        
        // Auto-detect portal from URL
        if (identifier.includes('otodom.pl')) setPortal('oto');
        else if (identifier.includes('rynekpierwotny.pl')) setPortal('rp');
        else if (identifier.includes('tabelaofert.pl')) setPortal('to');

        // Auto-select developer if name matches
        if (data.length > 0) {
          const combinedNames = data.map(i => i.name).join(' ').toLowerCase();
          const found = developers.find(d => {
            const slug = d.toLowerCase().replace(/-/g, ' ');
            return combinedNames.includes(slug) || combinedNames.includes(d.toLowerCase());
          });
          if (found) setSelectedDev(found);
        }

      } else {
        setError(data.error || 'Błąd podczas wyszukiwania');
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
      if (activePortals.rp) promises.push(fetch('/api/discovery/rp').then(r => r.ok ? r.json() : []));
      if (activePortals.oto) promises.push(fetch('/api/discovery/oto').then(r => r.ok ? r.json() : []));
      if (activePortals.to) promises.push(fetch('/api/discovery/to').then(r => r.ok ? r.json() : []));
      
      const results = await Promise.all(promises);
      const combined = results.flat();
      
      setResults(combined);
      setShowOnlyNew(true); // Default to showing only new after global scan
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

    const toDownload = results.filter(r => r.is_new && !r.registered);
    if (toDownload.length === 0) {
      setError('Brak nowych inwestycji do pobrania');
      return;
    }

    setLoading(true);
    setBatchProgress({ current: 0, total: toDownload.length, itemName: 'Przygotowanie...' });
    
    let successCount = 0;
    for (let i = 0; i < toDownload.length; i++) {
      const item = toDownload[i];
      setBatchProgress({ current: i + 1, total: toDownload.length, itemName: item.name });
      
      try {
        // Detect portal from URL or item if available
        let itemPortal = 'rp';
        if (item.url?.includes('otodom.pl')) itemPortal = 'oto';
        else if (item.url?.includes('tabelaofert.pl')) itemPortal = 'to';
        else if (item.portal) itemPortal = item.portal; // if backend provided it

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
        setError(data.error || 'Błąd podczas rejestracji');
      }
    } catch (err) {
      setError('Błąd połączenia');
    } finally {
      setRegistering(prev => ({ ...prev, [idx]: false }));
    }
  };

  const filteredResults = showOnlyNew ? results.filter(r => r.is_new) : results;

  const Chip = ({ label, active, onClick, color, source }) => (
    <button
      onClick={() => onClick()}
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
      {source && <window.SourceBadge source={source} />}
      <span style={{ marginLeft: source ? 6 : 0 }}>{label}</span>
    </button>
  );

  const ProgressBar = ({ current, total, label }) => {
    const percent = Math.round((current / total) * 100) || 0;
    return (
      <div data-component="ProgressBar" style={{ 
        flex: 1, minWidth: 200, display: 'flex', flexDirection: 'column', gap: 4 
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, fontWeight: 800, color: 'var(--usi-ink-3)', textTransform: 'uppercase' }}>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 300 }}>
            {label || 'Pobieranie...'}
          </span>
          <span>{current} / {total} ({percent}%)</span>
        </div>
        <div style={{ height: 6, background: 'var(--usi-surface-3)', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{ 
            height: '100%', width: `${percent}%`, background: 'var(--usi-success)', 
            transition: 'width 0.3s ease-out' 
          }} />
        </div>
      </div>
    );
  };

  return (
    <div className="usi-app" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', background: 'var(--usi-bg)' }}>
      {/* Toolbar - System Style */}
      <div data-component="ListToolbar" style={{
        display: 'flex', flexDirection: 'column',
        borderBottom: '.5px solid var(--usi-border)',
        background: 'var(--usi-surface)', flexShrink: 0,
        boxShadow: '0 2px 6px rgba(0,0,0,0.03)'
      }}>
        {/* Toolbar Top: Global Nav, Search, Portal Select */}
        <div data-component="ListToolbar-Top" style={{
          display: 'flex', alignItems: 'center', gap: 12,
          padding: '14px 24px', flexWrap: 'wrap', rowGap: 12,
          position: 'relative'
        }}>
          <div data-component="ListToolbar-Nav" style={{ display: 'flex', alignItems: 'center', gap: 12, flexShrink: 0 }}>
            <NavMenuButton onClick={() => setNavOpen(true)} />
            <h1 className="usi-h1" style={{ margin: 0, fontSize: 20 }}>Pobieranie</h1>
            <span className="usi-pill outline">{results.length}</span>
          </div>

          <div style={{ flex: 1, minWidth: 20 }} />

          {/* Quick Identifier Input */}
          <div data-component="ListToolbar-Search" style={{ position: 'relative', flex: '1 1 300px', maxWidth: 500, display: 'flex', gap: 8 }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <span style={{ position: 'absolute', left: 10, top: 9, color: 'var(--usi-ink-4)' }}><Icon name="search" /></span>
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

          <div data-component="ListToolbar-Filters" style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
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
                {successMsg}
              </div>
            )}
          </div>
          
          {navOpen && <NavDrawer current="download" onClose={() => setNavOpen(false)} onNav={onNav} dark={dark} onToggleTheme={onToggleTheme} />}
        </div>

        {/* Toolbar Bottom: Batch Controls & Discovery */}
        <div data-component="ListToolbar-Bottom" style={{ display: 'flex', alignItems: 'center', gap: 16, padding: '0 24px 14px', flexWrap: 'wrap' }}>
          <div data-component="Filter-Sources" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Skanuj</span>
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
              {loading && !batchProgress ? <Spinner size={12} stroke={2} /> : 'ZESKANUJ NOWOŚCI'}
            </button>
          </div>

          <div style={{ width: 1, height: 20, background: 'var(--usi-border)' }} />

          {batchProgress ? (
            <ProgressBar 
              current={batchProgress.current} 
              total={batchProgress.total} 
              label={`Pobieranie: ${batchProgress.itemName}`} 
            />
          ) : (
            <div data-component="Batch-Download" style={{ display: 'flex', gap: 12, alignItems: 'center', flex: 1 }}>
              <span style={{ fontSize: 10, fontWeight: 700, color: 'var(--usi-ink-4)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Deweloper</span>
              <select className="usi-input" value={selectedDev} onChange={e => setSelectedDev(e.target.value)} style={{ width: 'auto', height: 28, minWidth: 200, borderRadius: 6, fontSize: 12 }}>
                <option value="">Wybierz z bazy...</option>
                {developers.map(dev => (
                  <option key={dev} value={dev}>{dev}</option>
                ))}
              </select>
              
              <button 
                className="usi-btn success sm" 
                style={{ 
                  height: 28, borderRadius: 14, fontSize: 11, fontWeight: 700,
                  background: 'var(--usi-success)', borderColor: 'var(--usi-success)', color: '#fff'
                }}
                disabled={loading || !selectedDev || results.filter(r => r.is_new && !r.registered).length === 0}
                onClick={handleBatchDownload}
              >
                {`POBIERZ NOWOŚCI (${results.filter(r => r.is_new && !r.registered).length})`}
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Content Area */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '24px 24px 60px' }} className="usi-scroll">
        {error && (
          <div style={{ 
            padding: '12px 16px', borderRadius: 8, background: 'rgba(192, 57, 43, 0.1)', 
            color: 'var(--usi-danger)', marginBottom: 24, fontSize: 13, fontWeight: 600,
            border: '1px solid rgba(192, 57, 43, 0.2)', display: 'flex', alignItems: 'center', gap: 12
          }}>
            <Icon name="close" size={14} /> {error}
          </div>
        )}

        {results.length === 0 && !loading && (
          <div style={{ 
            display: 'flex', flexDirection: 'column', alignItems: 'center', 
            justifyContent: 'center', height: '60%', opacity: 0.3 
          }}>
            <div style={{ marginBottom: 16 }}>
              <Icon name="download" size={48} stroke={1} />
            </div>
            <div className="usi-h2" style={{ marginBottom: 8 }}>Gotowy do pobierania</div>
            <div className="usi-body" style={{ textAlign: 'center', maxWidth: 400 }}>
              Wklej link do oferty lub profilu dewelopera powyżej, <br/>albo zaznacz portale i kliknij "ZESKANUJ NOWOŚCI".
            </div>
          </div>
        )}

        {loading && results.length === 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 100, gap: 16 }}>
            <Spinner size={40} />
            <div className="usi-h3" style={{ opacity: 0.6 }}>Skanowanie źródeł...</div>
          </div>
        )}

        {results.length > 0 && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', 
            gap: 20 
          }}>
            {filteredResults.map((item, idx) => {
              const portalColor = item.portal === 'rp' ? '#C0392B' : (item.portal === 'oto' ? '#002C57' : '#5A4A2A');
              const isRegistering = registering[idx];

              return (
                <window.StandardCard
                  key={idx}
                  title={item.name}
                  subtitle={item.address || 'Brak adresu'}
                  extra={`ID: ${item.id || item.slug}`}
                  disabled={item.registered || isRegistering || !selectedDev}
                  onClick={() => handleRegister(item, idx)}
                  image={
                    item.image ? item.image : (
                      <div style={{ 
                        width: '100%', height: '100%', background: portalColor, 
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'rgba(255,255,255,0.2)'
                      }}>
                        <Icon name={item.portal === 'rp' ? 'building' : (item.portal === 'oto' ? 'grid' : 'search')} size={64} />
                      </div>
                    )
                  }
                  badges={
                    <>
                      <window.SourceBadge source={item.portal} url={item.url} />
                      {item.is_new && (
                        <span className="usi-pill success" style={{ fontSize: 9, padding: '2px 6px', fontWeight: 900 }}>NOWA</span>
                      )}
                    </>
                  }
                  overlay={
                    isRegistering ? <window.Spinner size={24} stroke={2} /> : 
                    (item.registered ? <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Icon name="check" size={18} /> W BAZIE</div> : null)
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

