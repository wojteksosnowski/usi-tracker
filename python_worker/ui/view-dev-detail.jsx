// view-dev-detail.jsx — widok szczegółowy dewelopera

function useJobStatus(jobId, onFinished) {
  const { React, useApi } = window;
  const [job, setJob] = React.useState(null);
  const { request } = useApi();
  
  React.useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }
    
    const poll = setInterval(() => {
      request(`/api/jobs/${jobId}`, { noCache: true })
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
  }, [jobId, request]);
  
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
    MAIN_CITIES, useApi
  } = window;
  const [developer, setDeveloper] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [navOpen, setNavOpen] = React.useState(false);
  const [activeJobId, setActiveJobId] = React.useState(null);
  const [filterCity, setFilterCity] = React.useState(null);
  
  const { request } = useApi();

  const load = React.useCallback(() => {
    setLoading(true);
    request(`/api/developer/${dev_slug}`)
      .then(data => {
        setDeveloper(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load developer", err);
        setLoading(false);
      });
  }, [dev_slug, request]);

  React.useEffect(() => {
    load();
    // Reset crawler badge when user opens developer detail
    fetch(`/api/crawler/badge-reset/${dev_slug}`, { method: 'POST' }).catch(() => {});
  }, [load]);

  const activeJob = useJobStatus(activeJobId, (finishedJob) => {
    if (finishedJob.status === 'completed') {
      load();
      setTimeout(() => setActiveJobId(null), 3000);
    }
  });

  const handleUpdate = () => {
    if (activeJobId) return;
    request(`/api/developer/${dev_slug}/discover`, { method: 'POST' })
      .then(data => {
        if (data.job_id) setActiveJobId(data.job_id);
      });
  };

  const [mergingSlug, setMergingSlug] = React.useState(null);

  const handleMerge = (source_slug) => {
    if (mergingSlug) return;
    setMergingSlug(source_slug);
    fetch(`/api/developer/${dev_slug}/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_slug })
    })
    .then(r => r.json())
    .then(data => {
      setMergingSlug(null);
      if (data.ok) load();
    })
    .catch(() => setMergingSlug(null));
  };

  const handleDismiss = (usi_dev_id) => {
    request(`/api/developer/${dev_slug}/dismiss-suggestion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ usi_dev_id })
    })
    .then(data => {
      if (data.ok) load();
    });
  };

  if (loading) {
    return (
      <div className="usi-app-loading">
        <Spinner />
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
      <NavMenuButton onClick={() => setNavOpen(true)} />
      <button className="usi-btn ghost" onClick={onBack}><Icon name="chevronLeft" /> Powrót</button>
      <div className="usi-flex-1" />
      <button className="usi-btn ghost sm" onClick={handleUpdate} disabled={!!activeJobId}>
        {activeJobId ? <Spinner size={12} stroke={1.5} /> : <Icon name="sparkle" size={12} />}
        {activeJobId ? ' Zadanie w tle...' : ' Sprawdź nowe inwestycje'}
      </button>
      {navOpen && <NavDrawer current="developers" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
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
                <StandardCard
                  key={inv.slug}
                  title={inv.name}
                  subtitle={inv.district}
                  image={inv.photos?.[0]}
                  onClick={() => onSelectInv(inv)}
                  style={{ height: 240 }}
                  badges={<SourceBadge source={inv.source} />}
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
            <DeveloperSuggestions dev={developer} onMerge={handleMerge} onDismiss={handleDismiss} mergingSlug={mergingSlug} />
            <MergedMembersPanel dev={developer} />
            <DeveloperStats dev={developer} onCityClick={setFilterCity} activeCity={filterCity} />
            <DevEventsLog dev={developer} />
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
            <button className="usi-btn sm ghost" style={{ color: 'var(--usi-bg)', borderColor: 'var(--usi-border-strong)' }} onClick={onClose}>Zamknij</button>
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
    <div className="usi-card usi-p-16">
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
                <div className="usi-weight-600 usi-body">{s.name}</div>
                <div className="usi-tiny usi-text-secondary">{s.count} inw. · {s.units} mieszk.</div>
            </div>
            {s.avgScore && <div className="usi-pill success sm usi-mono">{s.avgScore.toFixed(2)}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}

function DeveloperHeroBand({ dev }) {
  const { Icon, MiniMap } = window;
  const firstInvWithCoords = (dev.investments || []).find(i => i.coords && i.coords[0] !== 0);

  return (
    <div data-component="DeveloperHeroBand" className="developer-hero-band" style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 24, alignItems: 'center' }}>
      <div className="developer-hero-content">
        <div data-component="Developer-Avatar" className="developer-avatar">
          🏢
        </div>
        <div className="usi-flex-1">
          <div data-component="Developer-TitleRow" className="developer-title-row">
            <h1 data-component="Developer-Name" className="usi-h1" style={{ margin: 0 }}>{dev.name}</h1>
            <span data-component="Developer-ID" className="usi-pill outline usi-mono">{dev.usi_dev_id}</span>
          </div>
          <div data-component="Developer-Slug" className="usi-body usi-text-secondary" style={{ marginBottom: 12 }}>{dev.developer_slug}</div>
          <div className="usi-flex-row usi-gap-16">
            {dev.website && (
              <a href={dev.website} target="_blank" rel="noopener" className="usi-btn sm ghost">
                <Icon name="search" size={12} /> Strona www
              </a>
            )}
          </div>
        </div>
      </div>

      {firstInvWithCoords ? (
        <div style={{ height: 120, borderRadius: 12, overflow: 'hidden', border: '.5px solid var(--usi-border)' }}>
            <MiniMap coords={firstInvWithCoords.coords} ratio={3} />
        </div>
      ) : (
        <div className="usi-m-12 usi-flex-center usi-text-secondary usi-tiny" style={{ height: 120, borderRadius: 12, background: 'var(--usi-surface-3)' }}>
            Brak współrzędnych
        </div>
      )}
    </div>
  );
}

function PropertyRow({ label, value, mono }) {
  return (
    <div className="property-row">
      <div className="usi-tiny usi-m-8" style={{ color: 'var(--usi-ink-4)', marginLeft: 0 }}>{label}</div>
      <div className={`usi-body usi-weight-600 ${mono ? 'usi-mono' : ''}`}>{value || '—'}</div>
    </div>
  );
}

function DeveloperMetadata({ dev }) {
  const meta = dev.metadata || {};
  return (
    <div className="usi-card usi-p-16">
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
    <div className="usi-card usi-p-16">
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 16, color: 'var(--usi-ink-4)' }}>Mapowanie Portali</h3>
      <div className="usi-flex-col usi-gap-12">
        {mapping.rp && (
          <div className="usi-flex-row" style={{ justifyContent: 'space-between' }}>
            <SourceBadge source="rp" />
            <span className="usi-mono usi-tiny">{mapping.rp.id || mapping.rp.slug}</span>
          </div>
        )}
        {mapping.oto && (
          <div className="usi-flex-row" style={{ justifyContent: 'space-between' }}>
            <SourceBadge source="oto" />
            <div className="usi-card-footer-right">
               <div className="usi-mono usi-tiny">{mapping.oto.agency_id}</div>
               {mapping.oto.url && <a href={mapping.oto.url} target="_blank" rel="noopener" className="usi-tiny usi-flex-end">Profil Otodom</a>}
            </div>
          </div>
        )}
        {mapping.to && (
          <div className="usi-flex-row" style={{ justifyContent: 'space-between' }}>
            <SourceBadge source="to" />
            <span className="usi-mono usi-tiny">{mapping.to.slug}</span>
          </div>
        )}
        {!mapping.rp && !mapping.oto && !mapping.to && <div className="usi-tiny">Brak powiązań portalowych</div>}
      </div>
    </div>
  );
}

function DeveloperSuggestions({ dev, onMerge, onDismiss, mergingSlug }) {
  if (!dev.suggestions || dev.suggestions.length === 0) return null;
  const { Spinner } = window;

  return (
    <div className="usi-card usi-p-16 suggestions-card">
      <h3 className="usi-h3 usi-text-accent" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12 }}>
        <Icon name="sparkle" size={12} /> Sugerowane powiązania — kliknij kartę aby połączyć
      </h3>
      <div className="usi-flex-col usi-gap-8">
        {dev.suggestions.map(s => {
          const isMerging = mergingSlug === s.developer_slug;
          return (
            <div
              key={s.usi_dev_id}
              className={`suggestion-item dev-suggestion-card${isMerging ? ' merging' : ''}`}
              onClick={() => !mergingSlug && onMerge(s.developer_slug)}
              title="Kliknij aby połączyć z bieżącym deweloperem"
            >
              <div className="usi-flex-row" style={{ alignItems: 'center', gap: 8 }}>
                {isMerging
                  ? <Spinner size={14} stroke={1.5} />
                  : <Icon name="sparkle" size={14} style={{ color: 'var(--usi-accent)', flexShrink: 0 }} />
                }
                <div className="usi-flex-1">
                  <div className="usi-body usi-weight-600">{s.developer_slug}</div>
                  <div className="usi-tiny usi-text-secondary">{s.reason}</div>
                </div>
                <button
                  className="usi-btn sm ghost"
                  style={{ flexShrink: 0 }}
                  onClick={e => { e.stopPropagation(); onDismiss(s.usi_dev_id); }}
                  disabled={!!mergingSlug}
                  title="Ignoruj sugestię"
                >
                  <Icon name="x" size={12} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MergedMembersPanel({ dev }) {
  const merged = dev.merged_from || [];
  if (merged.length === 0) return null;

  return (
    <div className="usi-card usi-p-16">
      <h3 className="usi-h3" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 12, color: 'var(--usi-ink-4)' }}>
        Wchodzące w skład ({merged.length})
      </h3>
      <div className="usi-flex-col usi-gap-6">
        {merged.map((m, i) => (
          <div key={i} className="usi-flex-row" style={{ alignItems: 'center', gap: 8, padding: '6px 0', borderBottom: '0.5px solid var(--usi-border)' }}>
            <div className="usi-flex-1">
              <div className="usi-body">{m.name || m.slug}</div>
              <div className="usi-mono usi-tiny usi-text-secondary">{m.slug}</div>
            </div>
            {m.merged_at && (
              <div className="usi-tiny usi-text-secondary" style={{ flexShrink: 0 }}>
                {new Date(m.merged_at).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short' })}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function DevEventsLog({ dev }) {
  const events = dev.events || [];
  if (events.length === 0) return null;
  const [expanded, setExpanded] = React.useState(false);
  const shown = expanded ? events : events.slice(0, 5);

  const typeLabel = (e) => {
    if (e.type === 'merge_in') return `Połączono: ${e.source_name || e.source_slug}`;
    if (e.type === 'dismiss_suggestion') return `Ignorowano: ${e.dismissed_slug}`;
    if (e.type === 'discover') return `Discover (${e.by}): ${e.found} nowych`;
    return e.type;
  };

  return (
    <div className="usi-card usi-p-16">
      <div className="usi-flex-row" style={{ alignItems: 'center', marginBottom: 10 }}>
        <h3 className="usi-h3 usi-flex-1" style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 0.5, color: 'var(--usi-ink-4)', margin: 0 }}>
          Dziennik zdarzeń
        </h3>
        {events.length > 5 && (
          <button className="usi-btn sm ghost" onClick={() => setExpanded(v => !v)} style={{ fontSize: 11 }}>
            {expanded ? 'Zwiń' : `+${events.length - 5} więcej`}
          </button>
        )}
      </div>
      <div className="usi-flex-col usi-gap-4">
        {shown.map((e, i) => (
          <div key={i} className="usi-flex-row" style={{ gap: 8, alignItems: 'baseline' }}>
            <div className="usi-tiny usi-text-secondary usi-mono" style={{ flexShrink: 0, minWidth: 80 }}>
              {e.at ? new Date(e.at).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—'}
            </div>
            <div className="usi-tiny">{typeLabel(e)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

Object.assign(window, { DeveloperDetail });
