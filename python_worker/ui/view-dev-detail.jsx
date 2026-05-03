// view-dev-detail.jsx — widok szczegółowy dewelopera

function useJobStatus(jobId, onFinished) {
  const { React } = window;
  const [job, setJob] = React.useState(null);
  
  React.useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }
    
    const poll = setInterval(() => {
      fetch(`/api/jobs/${jobId}`)
        .then(r => r.json())
        .then(data => {
          setJob(data);
          if (data.status === 'completed' || data.status === 'failed') {
            clearInterval(poll);
            if (onFinished) onFinished(data);
          }
        })
        .catch(() => clearInterval(poll));
    }, 1000);
    
    return () => clearInterval(poll);
  }, [jobId]);
  
  return job;
}

function DeveloperDetail({ 
  dev_slug, 
  onBack, 
  onNav, 
  onSelectInv,
  dark, 
  onToggleTheme 
}) {
  const {
    React, Spinner, NavMenuButton, Icon,
    NavDrawer, StandardCard, SourceBadge, MetadataPanel,
    MAIN_CITIES
  } = window;
  const [developer, setDeveloper] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [navOpen, setNavOpen] = React.useState(false);
  const [activeJobId, setActiveJobId] = React.useState(null);
  const [filterCity, setFilterCity] = React.useState(null);

  const load = React.useCallback(() => {
    setLoading(true);
    fetch(`/api/developer/${dev_slug}`)
      .then(r => r.json())
      .then(data => {
        setDeveloper(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load developer", err);
        setLoading(false);
      });
  }, [dev_slug]);

  React.useEffect(() => {
    load();
  }, [load]);

  const activeJob = useJobStatus(activeJobId, (finishedJob) => {
    if (finishedJob.status === 'completed') {
      load();
      setTimeout(() => setActiveJobId(null), 3000);
    }
  });

  const handleUpdate = () => {
    if (activeJobId) return;
    fetch(`/api/developer/${dev_slug}/discover`, { method: 'POST' })
      .then(r => r.json())
      .then(data => {
        if (data.job_id) setActiveJobId(data.job_id);
      });
  };

  const handleMerge = (source_slug) => {
    if (!confirm(`Czy na pewno chcesz połączyć dewelopera '${source_slug}' z bieżącym? Wszystkie inwestycje zostaną przeniesione.`)) return;
    fetch(`/api/developer/${dev_slug}/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_slug })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) load();
      else alert("Błąd połączenia rekordów.");
    });
  };

  const handleDismiss = (usi_dev_id) => {
    fetch(`/api/developer/${dev_slug}/dismiss-suggestion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usi_dev_id })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) load();
    });
  };

  if (loading) {
    return (
      <div className="usi-app-loading">
        <window.Spinner />
      </div>
    );
  }

  if (!developer) {
    return (
      <div className="usi-app-empty">
        <h2 className="usi-h2">Nie znaleziono dewelopera</h2>
        <button className="usi-btn" onClick={onBack}>Powrót</button>
      </div>
    );
  }

  const filteredInvestments = filterCity 
    ? (developer.investments || []).filter(inv => (inv.address || '').includes(filterCity))
    : (developer.investments || []);

  const toolbar = (
    <div className="developer-detail-toolbar">
      <window.NavMenuButton onClick={() => setNavOpen(true)} />
      <button className="usi-btn ghost" onClick={onBack}><window.Icon name="chevronLeft" /> Powrót</button>
      <div style={{ flex: 1 }} />
      <button className="usi-btn ghost sm" onClick={handleUpdate} disabled={!!activeJobId}>
        {activeJobId ? <window.Spinner size={12} stroke={1.5} /> : <window.Icon name="sparkle" size={12} />}
        {activeJobId ? ' Zadanie w tle...' : ' Sprawdź nowe inwestycje'}
      </button>
      {navOpen && <window.NavDrawer current="developers" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
    </div>
  );

  return (
    <div data-component="DeveloperDetail" className="usi-app developer-detail-container">
      {toolbar}
      <div className="usi-scroll" style={{ flex: 1 }}>
        <DeveloperHeroBand dev={developer} />
        
        {activeJob && <JobStatusOverlay job={activeJob} onClose={() => setActiveJobId(null)} />}

        <div className="developer-main-content">
          <section>
            <div className="developer-investments-header">
                <h2 className="usi-h2" style={{ margin: 0 }}>Inwestycje ({filteredInvestments.length})</h2>
                {filterCity && (
                    <button className="usi-btn ghost sm" onClick={() => setFilterCity(null)}>Pokaż wszystkie miasta</button>
                )}
            </div>
            
            <div className="developer-investments-grid">
              {filteredInvestments.map(inv => (
                <window.StandardCard
                  key={inv.slug}
                  title={inv.name}
                  subtitle={inv.district}
                  image={inv.photos?.[0]}
                  onClick={() => onSelectInv(inv)}
                  style={{ height: 240 }}
                  badges={<window.SourceBadge source={inv.source} />}
                  footerLeft={<div className="usi-tiny">{inv.delivery}</div>}
                  footerRight={inv.ratings_score && <div className="usi-pill success sm">{inv.ratings_score.toFixed(2)}</div>}
                />
              ))}
            </div>
            {filteredInvestments.length === 0 && (
              <div className="usi-card flat developer-empty-state">
                Brak inwestycji spełniających kryteria.
              </div>
            )}
          </section>

          <aside className="developer-sidebar">
            <DeveloperSuggestions dev={developer} onMerge={handleMerge} onDismiss={handleDismiss} />
            <DeveloperStats dev={developer} onCityClick={setFilterCity} activeCity={filterCity} />
            <DeveloperMetadata dev={developer} />
            <DeveloperPortals dev={developer} />
          </aside>
        </div>
      </div>
    </div>
  );
}

function JobStatusOverlay({ job, onClose }) {
  const isFinished = job.status === 'completed' || job.status === 'failed';
  const progress = (job.progress / job.total) * 100;

  return (
    <div className="job-status-overlay" style={{ 
        background: job.status === 'failed' ? 'var(--usi-danger)' : 'var(--usi-accent)', 
    }}>
        <div className="job-progress-container">
            <div className="job-progress-info">
                <span>{job.name} — {job.message}</span>
                <span>{Math.round(progress)}%</span>
            </div>
            <div className="job-progress-bar-bg">
                <div className="job-progress-bar-fill" style={{ width: `${progress}%` }} />
            </div>
        </div>
        {isFinished && (
            <button className="usi-btn sm ghost" style={{ color: '#fff', borderColor: 'rgba(255,255,255,0.4)' }} onClick={onClose}>Zamknij</button>
        )}
    </div>
  );
}

function DeveloperStats({ dev, onCityClick, activeCity }) {
  const investments = dev.investments || [];
  if (investments.length === 0) return null;

  const cityStats = React.useMemo(() => {
    const stats = {};
    investments.forEach(inv => {
      const city = inv.address?.split(',')[0]?.trim() || 'Nieokreślone';
      if (!stats[city]) stats[city] = { count: 0, units: 0, scores: [] };
      stats[city].count += 1;
      stats[city].units += (inv.units || 0);
      if (inv.ratings_score) stats[city].scores.push(inv.ratings_score);
    });
    return Object.entries(stats).map(([name, s]) => ({
      name,
      ...s,
      avgScore: s.scores.length ? s.scores.reduce((a, b) => a + b, 0) / s.scores.length : null
    })).sort((a, b) => b.count - a.count);
  }, [investments]);

  return (
    <div className="usi-card" style={{ padding: 16 }}>
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16, color: 'var(--usi-ink-4)' }}>Zasięg inwestycji</h3>
      <div className="stats-list">
        {cityStats.map(s => (
          <div 
            key={s.name} 
            onClick={() => onCityClick(s.name === activeCity ? null : s.name)}
            data-active={s.name === activeCity}
            className="stats-item"
          >
            <div>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{s.name}</div>
                <div className="usi-tiny" style={{ opacity: 0.6 }}>{s.count} inw. · {s.units} mieszk.</div>
            </div>
            {s.avgScore && <div className="usi-pill success sm usi-mono">{s.avgScore.toFixed(2)}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function DeveloperHeroBand({ dev }) {
  return (
    <div data-component="DeveloperHeroBand" className="developer-hero-band">
      <div className="developer-hero-content">
        <div data-component="Developer-Avatar" className="developer-avatar">
          🏢
        </div>
        <div style={{ flex: 1 }}>
          <div data-component="Developer-TitleRow" className="developer-title-row">
            <h1 data-component="Developer-Name" className="usi-h1" style={{ margin: 0 }}>{dev.name}</h1>
            <span data-component="Developer-ID" className="usi-pill outline usi-mono">{dev.usi_dev_id}</span>
          </div>
          <div data-component="Developer-Slug" className="usi-body" style={{ color: 'var(--usi-ink-3)', marginBottom: 12 }}>{dev.developer_slug}</div>
          <div style={{ display: 'flex', gap: 16 }}>
            {dev.website && (
              <a href={dev.website} target="_blank" rel="noopener" className="usi-btn sm ghost">
                <window.Icon name="search" size={12} /> Strona www
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function PropertyRow({ label, value, mono }) {
  return (
    <div className="property-row">
      <div className="usi-tiny" style={{ color: 'var(--usi-ink-4)', marginBottom: 2 }}>{label}</div>
      <div style={{ fontWeight: 500, fontSize: 13 }} className={mono ? 'usi-mono' : ''}>{value || '—'}</div>
    </div>
  );
}

function DeveloperMetadata({ dev }) {
  const meta = dev.metadata || {};
  return (
    <div className="usi-card" style={{ padding: 16 }}>
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16, color: 'var(--usi-ink-4)' }}>Dane Firmy</h3>
      <PropertyRow label="Adres siedziby" value={meta.address} />
      <PropertyRow label="NIP" value={meta.nip} mono />
      <PropertyRow label="KRS" value={meta.krs} mono />
      <PropertyRow label="Email" value={meta.email} />
      <PropertyRow label="Telefon" value={meta.phone} />
    </div>
  );
}

function DeveloperPortals({ dev }) {
  const mapping = dev.portal_mapping || {};
  return (
    <div className="usi-card" style={{ padding: 16 }}>
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16, color: 'var(--usi-ink-4)' }}>Mapowanie Portali</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {mapping.rp && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <window.SourceBadge source="rp" />
            <span className="usi-mono" style={{ fontSize: 11 }}>{mapping.rp.id || mapping.rp.slug}</span>
          </div>
        )}
        {mapping.oto && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <window.SourceBadge source="oto" />
            <div style={{ textAlign: 'right' }}>
               <div className="usi-mono" style={{ fontSize: 11 }}>{mapping.oto.agency_id}</div>
               {mapping.oto.url && <a href={mapping.oto.url} target="_blank" rel="noopener" className="usi-tiny" style={{ display: 'block' }}>Profil Otodom</a>}
            </div>
          </div>
        )}
        {mapping.to && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <window.SourceBadge source="to" />
            <span className="usi-mono" style={{ fontSize: 11 }}>{mapping.to.slug}</span>
          </div>
        )}
        {!mapping.rp && !mapping.oto && !mapping.to && <div className="usi-tiny">Brak powiązań portalowych</div>}
      </div>
    </div>
  );
}

function DeveloperSuggestions({ dev, onMerge, onDismiss }) {
  if (!dev.suggestions || dev.suggestions.length === 0) return null;

  return (
    <div className="usi-card" style={{ padding: 16, border: '1px solid var(--usi-accent)', background: 'var(--usi-surface-2)' }}>
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12, color: 'var(--usi-accent)' }}>
        <window.Icon name="sparkle" size={12} /> Sugerowane Powiązania
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
        {dev.suggestions.map(s => (
          <div key={s.usi_dev_id} style={{ background: 'var(--usi-surface)', padding: 10, borderRadius: 8, border: '.5px solid var(--usi-border)' }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 2 }}>{s.developer_slug}</div>
            <div className="usi-tiny" style={{ color: 'var(--usi-ink-4)', marginBottom: 8 }}>{s.reason}</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="usi-btn sm" style={{ flex: 1 }} onClick={() => onMerge(s.developer_slug)}>Połącz</button>
              <button className="usi-btn sm ghost" onClick={() => onDismiss(s.usi_dev_id)}>Ignoruj</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { DeveloperDetail });
