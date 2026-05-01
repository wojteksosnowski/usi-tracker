// view-dashboard.jsx — dashboard z mapą, wykresami, podsumowaniem

function DashboardGrid({ investments = [], onNav = () => {}, accent, dark, onToggleTheme, hereApiKey }) {
  const [navOpen, setNavOpen] = React.useState(false);
  const total = investments.length;
  const rated = investments.filter(i => ratingStatus(i) === 'done').length;
  const partial = investments.filter(i => ratingStatus(i) === 'partial').length;
  const photos = investments.reduce((a, i) => a + (i.photos ? i.photos.length : 0), 0);
  const toDelete = investments.reduce((a, i) => a + (i.photos_to_delete || 0), 0);
  const avgByCat = USI_CATEGORIES.map(cat => {
    const vs = investments.map(i => ((i.ratings || {})[cat.key] || 0)).filter(v => v > 0);
    return { ...cat, avg: vs.length ? vs.reduce((a, b) => a + b, 0) / vs.length : 0, n: vs.length };
  });
  const ranked = [...investments]
    .filter(i => ratingStatus(i) !== 'none')
    .sort((a, b) => avgRating(b) - avgRating(a));
  const ratedWithAvg = investments.filter(i => avgRating(i) > 0);
  const globalAvg = ratedWithAvg.length
    ? ratedWithAvg.reduce((a, i) => a + avgRating(i), 0) / ratedWithAvg.length
    : 0;

  return (
    <div data-component="DashboardGrid" className="usi-app" style={{ background: 'var(--usi-bg)', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ 
        padding: '16px 24px', display: 'flex', alignItems: 'center', gap: 12, 
        borderBottom: '.5px solid var(--usi-border)', background: 'var(--usi-surface)', 
        flexShrink: 0, position: 'relative' 
      }}>
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h1" style={{ margin: 0 }}>Dashboard</h1>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Stan bazy danych</span>
        <div style={{ flex: 1 }} />
        {navOpen && <NavDrawer current="dashboard" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
      </div>
      <div style={{ padding: 24, display: 'grid', gridTemplateColumns: 'repeat(12, 1fr)', gap: 16, overflow: 'auto', flex: 1 }} className="usi-scroll">
        <KPI title="Inwestycji" value={total} sub="w bazie" col={3} />
        <KPI title="Ocenione" value={rated} sub={`${partial} częściowo`} col={3} accent="var(--usi-success)" />
        <KPI title="Zdjęć" value={photos.toLocaleString('pl-PL')} sub={`${toDelete} do usunięcia`} col={3} />
        <KPI title="Średnia ★" value={globalAvg > 0 ? globalAvg.toFixed(2) : '—'} sub="ze wszystkich" col={3} accent={accent || 'var(--usi-accent)'} />

        <div className="usi-card" style={{ gridColumn: 'span 6', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 16 }}>Średnia ocena per kategoria</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {avgByCat.map(c => (
              <div key={c.key} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{ width: 100, fontSize: 13, fontWeight: 500 }}>{c.key}</div>
                <div style={{ flex: 1, height: 20, background: 'var(--usi-surface-3)', borderRadius: 4, position: 'relative' }}>
                  <div style={{
                    height: '100%', width: `${(c.avg / 5) * 100}%`,
                    background: c.color, borderRadius: 4, transition: 'width .4s',
                  }} />
                  <span className="usi-mono" style={{
                    position: 'absolute', right: 8, top: 1, fontSize: 11, fontWeight: 600,
                    color: c.avg > 2.5 ? '#fff' : 'var(--usi-ink)',
                  }}>{c.n > 0 ? c.avg.toFixed(2) : '—'}</span>
                </div>
                <div style={{ width: 36, textAlign: 'right' }} className="usi-small">n={c.n}</div>
                <StarRating value={c.avg} readonly size={14} color={c.color} />
              </div>
            ))}
          </div>
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 6', padding: 18, display: 'flex', flexDirection: 'column' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', marginBottom: 12 }}>
            <span className="usi-tiny">Rozkład geograficzny</span>
            <span className="usi-small">{total} inwestycji</span>
          </div>
          <DashboardMap investments={investments} accent={accent} dark={dark} apiKey={hereApiKey} />
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 5', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Postęp ocen</div>
          {total > 0 ? (
            <>
              <div style={{ display: 'flex', height: 36, borderRadius: 6, overflow: 'hidden' }}>
                <div style={{ width: `${rated/total*100}%`, background: 'var(--usi-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                  {rated > 0 ? rated : ''}
                </div>
                <div style={{ width: `${partial/total*100}%`, background: '#F39200', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
                  {partial > 0 ? partial : ''}
                </div>
                <div style={{ flex: 1, background: 'var(--usi-surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--usi-ink-3)', fontSize: 12, fontWeight: 600 }}>
                  {total - rated - partial > 0 ? total - rated - partial : ''}
                </div>
              </div>
              <div style={{ display: 'flex', gap: 14, marginTop: 12, flexWrap: 'wrap' }}>
                <Legend color="var(--usi-success)" label="Pełne" />
                <Legend color="#F39200" label="Częściowe" />
                <Legend color="var(--usi-surface-3)" label="Nieocenione" />
              </div>
            </>
          ) : (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak danych</div>
          )}
        </div>

        <div className="usi-card" style={{ gridColumn: 'span 7', padding: 18 }}>
          <div className="usi-tiny" style={{ marginBottom: 12 }}>Top inwestycje wg średniej</div>
          {ranked.length === 0 ? (
            <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak ocenionych inwestycji</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {ranked.slice(0, 5).map((inv, i) => {
                const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
                return (
                  <div key={inv.slug} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                    <span className="usi-mono" style={{ width: 18, color: 'var(--usi-ink-4)', fontSize: 12 }}>{i+1}</span>
                    {thumb
                      ? <img src={thumb} alt="" style={{ width: 36, height: 36, borderRadius: 6, objectFit: 'cover' }} />
                      : <div style={{ width: 36, height: 36, borderRadius: 6, background: 'var(--usi-surface-3)' }} />
                    }
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{inv.name}</div>
                      <div className="usi-small">{inv.developer}</div>
                    </div>
                    <CategoryDots ratings={inv.ratings || {}} size={6} />
                    <span className="usi-mono" style={{ fontWeight: 600, minWidth: 36, textAlign: 'right' }}>★ {avgRating(inv).toFixed(2)}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function KPI({ title, value, sub, col = 3, accent }) {
  return (
    <div data-component="KPI" className="usi-card" style={{ gridColumn: `span ${col}`, padding: 18, position: 'relative', overflow: 'hidden' }}>
      <div className="usi-tiny" style={{ marginBottom: 6 }}>{title}</div>
      <div className="usi-mono" style={{ fontSize: 32, fontWeight: 600, letterSpacing: -0.02, color: accent || 'var(--usi-ink)' }}>{value}</div>
      <div className="usi-small" style={{ marginTop: 2 }}>{sub}</div>
      {accent && <div style={{ position: 'absolute', top: 0, right: 0, width: 4, bottom: 0, background: accent, opacity: 0.5 }} />}
    </div>
  );
}

function Legend({ color, label }) {
  return (
    <span data-component="Legend" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
      <span style={{ width: 10, height: 10, borderRadius: 2, background: color }} /> {label}
    </span>
  );
}

function DashboardMap({ investments = [], accent, dark, apiKey }) {
  const withCoords = investments.filter(i => i.coords && i.coords[0] !== 0);
  
  if (!apiKey || withCoords.length === 0) {
    return (
      <div data-component="DashboardMap" style={{ flex: 1, position: 'relative', minHeight: 240, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--usi-surface-3)', borderRadius: 8 }}>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>
          {!apiKey ? 'Brak klucza API HERE' : 'Brak danych geolokalizacyjnych'}
        </span>
      </div>
    );
  }

  // Budujemy listę punktów dla HERE Map Image API (v3)
  // Format: lat,lon|lat,lon|...|size=small;icon=circle
  // Ograniczamy liczbę punktów do 200, aby nie przekroczyć limitu URL
  const pts = withCoords.slice(0, 200).map(inv => `${inv.coords[0]},${inv.coords[1]}`).join('|');
  const style = dark ? 'explore.night' : 'explore.day';
  
  // Używamy overlay:padding=32 aby punkty nie były przy samej krawędzi
  const src = `https://image.maps.hereapi.com/mia/v3/base/mc/overlay:padding=32/600x300/png?apiKey=${apiKey}&overlay=point:${pts}|size=small;icon=circle&style=${style}&features=pois:disabled&lang=pl`;

  return (
    <div data-component="DashboardMap" style={{ flex: 1, position: 'relative', minHeight: 240, borderRadius: 8, overflow: 'hidden', background: 'var(--usi-surface-3)' }}>
      <img 
        src={src} 
        alt="Mapa inwestycji" 
        style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
        onError={(e) => {
          e.target.style.display = 'none';
          e.target.nextSibling.style.display = 'flex';
        }}
      />
      <div style={{ display: 'none', position: 'absolute', inset: 0, alignItems: 'center', justifyContent: 'center', background: 'var(--usi-surface-3)' }}>
        <span className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Błąd ładowania mapy HERE</span>
      </div>
    </div>
  );
}

Object.assign(window, { DashboardGrid });
