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
  const [error, setError] = React.useState(null);
  const [successMsg, setSuccessMsg] = React.useState('');
  const [registering, setRegistering] = React.useState({}); // { [idx]: true }
  const [navOpen, setNavOpen] = React.useState(false);

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
          const first = data[0];
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

  return (
    <div className="usi-app" style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header / Toolbar */}
      <div style={{ 
        display: 'flex', alignItems: 'center', gap: 12, padding: '14px 24px', 
        background: 'var(--usi-surface)', borderBottom: '1px solid var(--usi-border)',
        flexShrink: 0, position: 'relative'
      }}>
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h1" style={{ margin: 0, fontSize: 20 }}>Pobieranie Inwestycji</h1>
        <div style={{ flex: 1 }} />
        {successMsg && (
          <div style={{ background: 'var(--usi-success)', color: '#fff', padding: '4px 12px', borderRadius: 12, fontSize: 12, fontWeight: 600 }}>
            {successMsg}
          </div>
        )}
        {navOpen && <NavDrawer current="download" onClose={() => setNavOpen(false)} onNav={onNav} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Sidebar */}
        <div style={{ 
          width: 340, borderRight: '1.5px solid var(--usi-border)', 
          display: 'flex', flexDirection: 'column', gap: 24, padding: 24,
          background: 'var(--usi-surface)', flexShrink: 0
        }} className="usi-scroll">
          
          <div>
            <label className="usi-tiny" style={{ display: 'block', marginBottom: 8, fontWeight: 700, color: 'var(--usi-ink-3)' }}>
              LINK LUB IDENTYFIKATOR
            </label>
            <textarea 
              className="usi-input" 
              style={{ height: 80, resize: 'none', paddingTop: 10 }}
              value={identifier} 
              onChange={e => setIdentifier(e.target.value)}
              placeholder="Wklej URL profilu dewelopera, link do oferty lub wpisz ID..."
            />
            <div className="usi-tiny" style={{ marginTop: 8, opacity: 0.7, lineHeight: 1.4 }}>
              System automatycznie rozpozna portal i wyciągnie listę inwestycji.
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12 }}>
             <div style={{ flex: 1 }}>
                <label className="usi-tiny" style={{ display: 'block', marginBottom: 8, fontWeight: 700, color: 'var(--usi-ink-3)' }}>PORTAL</label>
                <select className="usi-input" value={portal} onChange={e => setPortal(e.target.value)}>
                  <option value="rp">RynekPierwotny</option>
                  <option value="oto">Otodom</option>
                  <option value="to">TabelaOfert</option>
                </select>
             </div>
          </div>

          <div style={{ height: 1, background: 'var(--usi-border)' }} />

          <div>
            <label className="usi-tiny" style={{ display: 'block', marginBottom: 8, fontWeight: 700, color: 'var(--usi-ink-3)' }}>
              DEWELOPER (DOCELOWY FOLDER)
            </label>
            <select className="usi-input" value={selectedDev} onChange={e => setSelectedDev(e.target.value)}>
              <option value="">Wybierz z bazy...</option>
              {developers.map(dev => (
                <option key={dev} value={dev}>{dev}</option>
              ))}
            </select>
            <div className="usi-tiny" style={{ marginTop: 8, color: 'var(--usi-accent)', fontWeight: 600 }}>
              Wkrótce: automatyczne tworzenie nowych folderów.
            </div>
          </div>

          <button 
            className="usi-btn primary" 
            style={{ width: '100%', height: 44, marginTop: 10, justifyContent: 'center', fontSize: 14, fontWeight: 700 }}
            disabled={loading || !identifier}
            onClick={handleSearch}
          >
            {loading ? <Spinner size={18} stroke={2} /> : 'ANALIZUJ I SZUKAJ'}
          </button>
        </div>

        {/* Main Content */}
        <div style={{ flex: 1, padding: '32px 40px', overflowY: 'auto', background: 'var(--usi-bg)' }} className="usi-scroll">
          {error && (
            <div style={{ 
              padding: '16px', borderRadius: 12, background: 'rgba(192, 57, 43, 0.1)', 
              color: 'var(--usi-danger)', marginBottom: 32, fontSize: 14, fontWeight: 600,
              border: '1px solid rgba(192, 57, 43, 0.2)', display: 'flex', alignItems: 'center', gap: 12
            }}>
              <Icon name="x" size={18} /> {error}
            </div>
          )}

          {results.length === 0 && !loading && (
            <div style={{ 
              display: 'flex', flexDirection: 'column', alignItems: 'center', 
              justifyContent: 'center', height: '70%', opacity: 0.3 
            }}>
              <div style={{ marginBottom: 20, transform: 'scale(1.5)' }}>
                <Icon name="download" size={48} stroke={1} />
              </div>
              <div className="usi-h2" style={{ marginBottom: 8 }}>Gotowy do pobierania</div>
              <div style={{ textAlign: 'center', maxWidth: 320, lineHeight: 1.5 }}>
                Wklej link do profilu dewelopera lub biura nieruchomości, aby zobaczyć dostępne inwestycje.
              </div>
            </div>
          )}

          {loading && results.length === 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginTop: 120, gap: 20 }}>
              <Spinner size={40} />
              <div className="usi-h3" style={{ opacity: 0.6 }}>Analizowanie źródła...</div>
            </div>
          )}

          {results.length > 0 && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginBottom: 24 }}>
                <div>
                  <div className="usi-tiny" style={{ textTransform: 'uppercase', letterSpacing: '0.1em', color: 'var(--usi-ink-4)', marginBottom: 4 }}>
                    Źródło: {portal.toUpperCase()}
                  </div>
                  <h2 className="usi-h1" style={{ margin: 0 }}>Znalezione inwestycje ({results.length})</h2>
                </div>
              </div>
              
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))', gap: 20 }}>
                {results.map((item, idx) => (
                  <div key={idx} className="usi-card" style={{ 
                    display: 'flex', padding: 20, gap: 16, alignItems: 'flex-start',
                    background: item.registered ? 'var(--usi-surface-2)' : 'var(--usi-surface)',
                    opacity: item.registered ? 0.7 : 1,
                    transition: 'all 0.2s ease',
                    border: item.kind === 'single' ? '2px solid var(--usi-accent)' : '1px solid var(--usi-border)'
                  }}>
                    <div style={{ 
                      width: 48, height: 48, borderRadius: 12, background: 'var(--usi-surface-3)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0
                    }}>
                      <Icon name={item.kind === 'single' ? 'sparkle' : 'grid'} size={20} />
                    </div>

                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 700, fontSize: 16, marginBottom: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {item.name}
                      </div>
                      <div className="usi-mono" style={{ fontSize: 11, color: 'var(--usi-ink-4)', marginBottom: 8 }}>
                        ID: {item.id || item.slug}
                      </div>
                      
                      {item.address && (
                        <div className="usi-small" style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--usi-ink-3)', marginBottom: 12 }}>
                          <Icon name="search" size={12} /> {item.address}
                        </div>
                      )}

                      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        {item.registered ? (
                          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--usi-success)' }}>
                            <Icon name="check" size={16} />
                            <span style={{ fontWeight: 700, fontSize: 13 }}>W BAZIE</span>
                          </div>
                        ) : (
                          <button 
                            className="usi-btn primary sm" 
                            style={{ padding: '6px 16px', borderRadius: 8 }}
                            disabled={registering[idx] || !selectedDev}
                            onClick={() => handleRegister(item, idx)}
                          >
                            {registering[idx] ? <Spinner size={12} stroke={1.5} /> : 'DODAJ DO BAZY'}
                          </button>
                        )}
                        
                        {item.url && (
                          <a href={item.url} target="_blank" rel="noopener" className="usi-small" style={{ color: 'var(--usi-accent)', fontWeight: 600, textDecoration: 'none' }}>
                            ZOBACZ ORYGINAŁ ↗
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
