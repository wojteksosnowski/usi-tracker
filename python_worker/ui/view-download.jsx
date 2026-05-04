window.ViewDownload = function ViewDownload() {
  const {
    React, Icon, Spinner, SourceBadge, StandardCard, useDevelopers
  } = window;

  const { developers = [] } = useDevelopers ? useDevelopers() : {};

  const [portal, setPortal] = React.useState('rp');
  const [identifier, setIdentifier] = React.useState('');
  const [selectedDev, setSelectedDev] = React.useState('');
  
  const [loading, setLoading] = React.useState(false);
  const [results, setResults] = React.useState([]);
  const [showOnlyNew, setShowOnlyNew] = React.useState(false);
  const [error, setError] = React.useState(null);
  const [registering, setRegistering] = React.useState({});
  const [activePortals, setActivePortals] = React.useState({ rp: true, oto: true, to: true });

  const handleSearch = async () => {
    if (!identifier) return;
    setLoading(true);
    setError(null);
    setResults([]);
    try {
      const response = await fetch(`/api/discovery/${portal}?id=${encodeURIComponent(identifier)}`);
      const data = await response.json();
      if (response.ok) {
        setResults(Array.isArray(data) ? data : []);
      } else {
        setError(data.error || 'Błąd wyszukiwania');
      }
    } catch (err) {
      setError('Błąd połączenia');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (res) => {
    if (!selectedDev) return;
    setRegistering(prev => ({ ...prev, [res.url]: true }));
    try {
      const response = await fetch('/api/investment/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          developer_slug: selectedDev,
          url: res.url,
          portal: res.source || portal
        })
      });
      const data = await response.json();
      if (response.ok) {
        setResults(prev => prev.map(r => r.url === res.url ? { ...r, registered: true } : r));
      } else {
        alert(data.error || 'Błąd rejestracji');
      }
    } catch (err) {
      alert('Błąd połączenia');
    } finally {
      setRegistering(prev => ({ ...prev, [res.url]: false }));
    }
  };

  const visibleResults = results.filter(r => r && (!showOnlyNew || r.is_new));

  return (
    <div data-component="ViewDownload" className="usi-app download-view-content" style={{ height: '100%', display: 'flex', flexDirection: 'column', background: 'var(--usi-bg)' }}>
      <div style={{ padding: '16px 24px', background: 'var(--usi-surface)', borderBottom: '.5px solid var(--usi-border)', display: 'flex', flexWrap: 'wrap', gap: 16, alignItems: 'center' }}>
        <div style={{ display: 'flex', gap: 12, flex: 1, minWidth: 300 }}>
          <div style={{ flex: 1, position: 'relative' }}>
             <Icon name="search" size={14} style={{ position: 'absolute', left: 12, top: 11, color: 'var(--usi-ink-4)' }} />
             <input className="usi-input" placeholder="Wklej URL inwestycji..." value={identifier} onChange={e => setIdentifier(e.target.value)} style={{ paddingLeft: 36, height: 36, borderRadius: 18, background: 'var(--usi-surface-2)' }} />
          </div>
          <select className="usi-input" value={portal} onChange={e => setPortal(e.target.value)} style={{ width: 140, height: 36, borderRadius: 18, background: 'var(--usi-surface-2)' }}>
            <option value="rp">RynekPierwotny</option>
            <option value="oto">Otodom</option>
            <option value="to">TabelaOfert</option>
          </select>
          <button className="usi-btn" onClick={handleSearch} disabled={loading} style={{ height: 36, borderRadius: 18, padding: '0 24px' }}>
            {loading ? <Spinner size={16} /> : 'Szukaj'}
          </button>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
           <select className="usi-input" value={selectedDev} onChange={e => setSelectedDev(e.target.value)} style={{ width: 240, height: 36, borderRadius: 18, background: 'var(--usi-surface-2)' }}>
              <option value="">Wybierz dewelopera do zapisu...</option>
              {developers.map(d => <option key={d.developer_slug} value={d.developer_slug}>{d.name}</option>)}
           </select>
           <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 13, fontWeight: 500 }}>
             <input type="checkbox" checked={showOnlyNew} onChange={e => setShowOnlyNew(e.target.checked)} />
             Tylko nowe
           </label>
        </div>
      </div>

      <div className="usi-scroll" style={{ flex: 1, overflowY: 'auto', padding: '24px' }}>
        {error && <div className="usi-pill error" style={{ marginBottom: 24, padding: '12px 16px' }}>{error}</div>}
        
        {visibleResults.length === 0 && !loading && !error && (
            <div className="usi-app-empty" style={{ height: '50%', display: 'flex', flexDirection: 'column', justifyContent: 'center', opacity: 0.5 }}>
                <Icon name="sparkle" size={48} style={{ marginBottom: 16 }} />
                <div className="usi-body">Wprowadź URL inwestycji, aby rozpocząć proces Discovery</div>
            </div>
        )}

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '20px' }}>
          {visibleResults.map((res, idx) => (
            <StandardCard
              key={idx}
              title={res.name}
              subtitle={res.developer}
              extra={res.district}
              badges={<SourceBadge source={res.source || portal} />}
              footerRight={
                <button 
                  className={`usi-btn sm ${res.registered ? 'success' : ''}`} 
                  disabled={!selectedDev || res.registered || registering[res.url]}
                  onClick={() => handleRegister(res)}
                >
                  {registering[res.url] ? <Spinner size={12} stroke={1.5} /> : (res.registered ? 'Pobrano' : 'Pobierz')}
                </button>
              }
            />
          ))}
        </div>
      </div>
    </div>
  );
};
