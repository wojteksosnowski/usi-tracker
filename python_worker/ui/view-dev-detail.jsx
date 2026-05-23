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
  usi_dev_id,
  onBack,
  onSelectInv,
  onRegisterDiscover,
}) {
  const {
    React, Spinner, Icon,
    StandardCard, SourceBadge, MetadataPanel,
    MAIN_CITIES, useApi, useDataBus
  } = window;
  const [developer, setDeveloper] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [suggesting, setSuggesting] = React.useState(false);
  const [activeJobId, setActiveJobId] = React.useState(null);
  const [filterCity, setFilterCity] = React.useState(null);
  
  const { request } = useApi();
  const { refetch, setVariable } = useDataBus();

  const load = React.useCallback((silent = false) => {
    if (!silent) setLoading(true);
    const endpoint = usi_dev_id
      ? `/api/developer/${dev_slug}?id=${usi_dev_id}`
      : `/api/developer/${dev_slug}`;
    request(endpoint, { noCache: true })
      .then(data => {
        setDeveloper(data);
        if (!silent) setLoading(false);
      })
      .catch(err => {
        console.error("Failed to load developer", err);
        if (!silent) setLoading(false);
      });
  }, [dev_slug, usi_dev_id, request]);

  React.useEffect(() => {
    load();
    // Reset crawler badge when user opens developer detail
    fetch(`/api/crawler/badge-reset/${dev_slug}?id=${usi_dev_id}`, { method: 'POST' }).catch(() => {});
  }, [load, dev_slug]);

  const handleSuggest = () => {
    setSuggesting(true);
    request('/api/developer/suggest', { method: 'POST' })
      .then(() => {
        load(true);
        refetch('developers');
      })
      .finally(() => setSuggesting(false));
  };

  useJobStatus(activeJobId, (finishedJob) => {
    if (finishedJob.status === 'completed') {
      load();
      setVariable('appStatus', { type: 'success', msg: finishedJob.message || 'Zakończono.' });
    } else {
      setVariable('appStatus', { type: 'error', msg: finishedJob.message || 'Wystąpił błąd podczas sprawdzania.' });
    }
    setTimeout(() => setActiveJobId(null), 3000);
  });

  const handleUpdate = React.useCallback(() => {
    if (activeJobId) return;
    request(`/api/developer/${dev_slug}/discover?id=${usi_dev_id}`, { method: 'POST' })
      .then(data => {
        if (data.job_id) setActiveJobId(data.job_id);
      });
  }, [activeJobId, dev_slug, request]);

  React.useEffect(() => {
    if (onRegisterDiscover) onRegisterDiscover(handleUpdate, !!activeJobId);
  }, [handleUpdate, activeJobId, onRegisterDiscover]);

  // Local state for optimistic merge (card jumps immediately without reload)
  const [localSuggestions, setLocalSuggestions] = React.useState([]);
  const [localMerged, setLocalMerged] = React.useState([]);
  const [arrivingSlug, setArrivingSlug] = React.useState(null);

  React.useEffect(() => {
    if (developer) {
      setLocalSuggestions(developer.suggestions || []);
      setLocalMerged(developer.merged_from || []);
    }
  }, [developer]);

  const handleMerge = (suggestion) => {
    const source_id = suggestion.usi_dev_id;
    const source_slug = suggestion.developer_slug;

    // Optimistic: move card immediately from suggestions → connected
    setLocalSuggestions(prev => prev.filter(s => s.usi_dev_id !== source_id));
    const arriving = {
      slug: source_slug,
      name: suggestion.name || source_slug,
      usi_dev_id: source_id,
      portal_mapping: suggestion.portal_mapping || {},
      investments_count: suggestion.investments_count || 0,
      merged_at: new Date().toISOString(),
    };
    setLocalMerged(prev => [arriving, ...prev]);
    setArrivingSlug(source_slug);
    setTimeout(() => setArrivingSlug(null), 600);

    fetch(`/api/developer/${dev_slug}/merge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_id, target_id: usi_dev_id })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        setVariable('appStatus', { type: 'success', msg: 'Połączono profile dewelopera.' });
        load(true); // silent sync — no spinner, keeps optimistic card visible
        refetch('developers'); // remove merged child from global list
      } else {
        // Revert optimistic update
        setLocalMerged(prev => prev.filter(m => m.usi_dev_id !== source_id));
        setLocalSuggestions(prev => [suggestion, ...prev]);
        setVariable('appStatus', { type: 'error', msg: 'Błąd podczas łączenia.' });
      }
    })
    .catch(() => {
      setLocalMerged(prev => prev.filter(m => m.usi_dev_id !== source_id));
      setLocalSuggestions(prev => [suggestion, ...prev]);
      setVariable('appStatus', { type: 'error', msg: 'Błąd sieci podczas łączenia.' });
    });
  };

  const handleUnmerge = (memberId) => {
    const leaving = localMerged.find(m => m.usi_dev_id === memberId);
    setLocalMerged(prev => prev.filter(m => m.usi_dev_id !== memberId));
    fetch(`/api/developer/${dev_slug}/unmerge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_id: memberId, target_id: usi_dev_id })
    })
    .then(r => r.json())
    .then(data => {
      if (data.ok) {
        setVariable('appStatus', { type: 'success', msg: 'Odłączono profil.' });
        load(true);
        refetch('developers');
      } else {
        if (leaving) setLocalMerged(prev => [leaving, ...prev]);
        setVariable('appStatus', { type: 'error', msg: 'Błąd podczas odłączania.' });
      }
    })
    .catch(() => {
      if (leaving) setLocalMerged(prev => [leaving, ...prev]);
      setVariable('appStatus', { type: 'error', msg: 'Błąd sieci podczas odłączania.' });
    });
  };


  const handleDismiss = (suggested_id) => {
    const dismissed = localSuggestions.find(s => s.usi_dev_id === suggested_id);
    setLocalSuggestions(prev => prev.filter(s => s.usi_dev_id !== suggested_id));
    request(`/api/developer/${dev_slug}/dismiss-suggestion`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ target_id: usi_dev_id, usi_dev_id: suggested_id })
    })
    .catch(() => {
      if (dismissed) setLocalSuggestions(prev => [...prev, dismissed]);
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
    ? (developer.investments || []).filter(inv =>
        inv.city === filterCity || (inv.address || '').includes(filterCity))
    : (developer.investments || []);

  return (
    <div data-component="DeveloperDetail">
      <DeveloperHeroBand dev={developer} />

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
            <DeveloperSuggestions 
                suggestions={localSuggestions} 
                onMerge={handleMerge} 
                onDismiss={handleDismiss} 
                onSuggest={handleSuggest}
                loading={suggesting}
            />
            <MergedMembersPanel dev={developer} members={localMerged} arrivingSlug={arrivingSlug} onUnmerge={handleUnmerge} />
            <DeveloperStats dev={developer} onCityClick={setFilterCity} activeCity={filterCity} />
            <WedrowiecStatus dev={developer} />
            <DevEventsLog dev={developer} />
            <DeveloperMetadata dev={developer} />
            <DeveloperPortals dev={developer} />
          </aside>
        </div>
    </div>
  );
}


function DeveloperStats({ dev, onCityClick, activeCity }) {
  const investments = dev.investments || [];
  if (investments.length === 0) return null;

  const cityStats = React.useMemo(() => {
    const stats = {};
    investments.forEach(inv => {
      const city = inv.city || inv.address?.split(',')[0]?.trim() || 'Nieokreślone';
      if (!stats[city]) stats[city] = { count: 0, units: 0, scoreItems: [] };
      stats[city].count += 1;
      stats[city].units += (inv.units || 0);
      if (inv.ratings_score) stats[city].scoreItems.push({ score: inv.ratings_score, units: inv.units || 1 });
    });
    return Object.entries(stats).map(([name, s]) => {
      const totalUnits = s.scoreItems.reduce((a, b) => a + b.units, 0);
      const avgScore = totalUnits > 0
        ? s.scoreItems.reduce((a, b) => a + b.score * b.units, 0) / totalUnits
        : s.scoreItems.length > 0
          ? s.scoreItems.reduce((a, b) => a + b.score, 0) / s.scoreItems.length
          : null;
      return { name, count: s.count, units: s.units, avgScore };
    }).sort((a, b) => b.count - a.count);
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
  const meta = dev.metadata || {};
  const metaItems = [
    meta.address,
    meta.nip && `NIP: ${meta.nip}`,
    meta.krs && `KRS: ${meta.krs}`,
    meta.email,
    meta.phone,
  ].filter(Boolean);

  const logoUrl = `/api/developer/${dev.developer_slug}/logo`;

  return (
    <div data-component="DeveloperHeroBand" className="developer-hero-band" style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 24, alignItems: 'center' }}>
      <div className="developer-hero-content">
        <div data-component="Developer-Avatar" className="developer-avatar" style={{ overflow: 'hidden', background: 'white' }}>
          <img 
            src={logoUrl} 
            onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
            style={{ width: '100%', height: '100%', objectFit: 'contain' }}
            alt=""
          />
          <div style={{ display: 'none', width: '100%', height: '100%', alignItems: 'center', justifyContent: 'center', fontSize: '32px' }}>🏢</div>
        </div>
        <div className="usi-flex-1">
          <div data-component="Developer-TitleRow" className="developer-title-row">
            <h1 data-component="Developer-Name" className="usi-h1" style={{ margin: 0 }}>{dev.name}</h1>
            <span data-component="Developer-ID" className="usi-pill outline usi-mono">{dev.usi_dev_id}</span>
          </div>
          <div data-component="Developer-Slug" className="usi-body usi-text-secondary" style={{ marginBottom: metaItems.length ? 4 : 12 }}>{dev.developer_slug}</div>
          {metaItems.length > 0 && (
            <div className="usi-tiny usi-text-secondary" style={{ marginBottom: 10, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {metaItems.join(' · ')}
            </div>
          )}
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
            <span className="usi-mono usi-tiny">{mapping.to.slug || mapping.to.agency_id || mapping.to.id}</span>
          </div>
        )}
        {!mapping.rp && !mapping.oto && !mapping.to && <div className="usi-tiny">Brak powiązań portalowych</div>}
      </div>
    </div>
  );
}

// ── DevMiniCard — shared card for suggestions and connected-records panels ──
function DevMiniCard({ name, slug, usiId, portalMapping = {}, website, invCount, invList, sub, arriving, footer }) {
  const { SourceBadge } = window;
  const hasRp  = !!portalMapping.rp;
  const hasOto = !!portalMapping.oto;
  const hasTo  = !!portalMapping.to;

  return (
    <div className={`dev-mini-card${arriving ? ' dev-card-arriving' : ''}`}>
      <div className="dev-mini-card-top">
        <div className="dev-mini-card-name usi-body usi-weight-600">{name || slug}</div>
        <div className="dev-mini-card-meta usi-mono usi-tiny usi-text-secondary">
          {slug}{usiId ? ` · ${usiId}` : ''}
          {invCount != null ? ` · ${invCount} inw.` : ''}
        </div>
        {sub && <div className="usi-tiny usi-text-secondary dev-mini-card-sub">{sub}</div>}
      </div>
      <div className="dev-mini-card-bottom">
        <div className="dev-mini-card-badges">
          {hasRp  && <SourceBadge source="rp" />}
          {hasOto && <SourceBadge source="oto" />}
          {hasTo  && <SourceBadge source="to" />}
          {!hasRp && !hasOto && !hasTo && (
            website
              ? <a href={website} target="_blank" rel="noopener" className="usi-tiny usi-text-secondary" style={{ textDecoration: 'underline', maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'inline-block' }} title={website}>{website.replace(/^https?:\/\//, '')}</a>
              : <span className="usi-tiny usi-text-secondary" title="Ten deweloper nie ma powiązań z żadnym portalem" style={{ fontStyle: 'italic' }}>brak portali</span>
          )}
        </div>
        {footer}
      </div>
      {invList && invList.length > 0 && (
        <div className="usi-flex-col usi-gap-2" style={{ marginTop: 6 }}>
          {invList.map((inv, i) => (
            <div key={i} className="usi-tiny usi-text-secondary usi-mono" style={{ paddingLeft: 4 }}>
              · {inv.name || inv.slug}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function DeveloperSuggestions({ suggestions, onMerge, onDismiss, onSuggest, loading }) {
  const { Icon, Spinner } = window;
  if (!suggestions) return null;

  return (
    <div className="usi-card usi-p-16 suggestions-card">
      <div className="usi-flex-row" style={{ justifyContent: 'space-between', alignItems: 'center', marginBottom: suggestions.length > 0 ? 12 : 0 }}>
        <h3 className="dev-panel-header usi-text-accent" style={{ marginBottom: 0 }}>
          <Icon name="sparkle" size={12} /> Sugerowane powiązania
        </h3>
        <button 
          className="usi-btn sm ghost" 
          onClick={onSuggest} 
          disabled={loading}
          title="Szukaj podobnych deweloperów"
        >
          {loading ? <Spinner size={12} /> : <Icon name="search" size={12} />}
        </button>
      </div>

      <div className="usi-flex-col usi-gap-8">
        {suggestions.map(s => (
          <DevMiniCard
            key={s.usi_dev_id}
            name={s.name || s.developer_slug}
            slug={s.developer_slug}
            usiId={s.usi_dev_id}
            portalMapping={s.portal_mapping || {}}
            website={s.website}
            invCount={s.investments_count}
            sub={s.reason}
            footer={
              <div className="usi-flex-row usi-gap-6">
                <button
                  className="usi-btn sm usi-flex-1"
                  onClick={() => onMerge(s)}
                >
                  Połącz
                </button>
                <button
                  className="usi-btn sm ghost"
                  onClick={() => onDismiss(s.usi_dev_id)}
                  title="Ignoruj sugestię"
                >
                  <Icon name="x" size={12} />
                </button>
              </div>
            }
          />
        ))}
      </div>
      
      {suggestions.length === 0 && !loading && (
        <div className="usi-tiny usi-text-secondary" style={{ marginTop: 8 }}>Brak aktywnych sugestii.</div>
      )}
    </div>
  );
}

function MergedMembersPanel({ dev, members, arrivingSlug, onUnmerge }) {
  if (!dev) return null;
  const { Icon } = window;
  const base = dev.base_record || dev;
  
  const total = 1 + (members || []).length;

  return (
    <div className="usi-card usi-p-16">
      <h3 className="dev-panel-header">
        <Icon name="grid" size={12} />
        Skład rekordu ({total})
      </h3>
      <div className="usi-flex-col usi-gap-8">
        <DevMiniCard
          key={`base-${base.developer_slug}`}
          name={base.name}
          slug={base.developer_slug}
          usiId={base.usi_dev_id}
          portalMapping={base.portal_mapping || {}}
          invCount={base.investments_count}
          invList={base.inv_list}
          sub="Profil bazowy"
        />
        {(members || []).map((m, i) => (
          <DevMiniCard
            key={m.usi_dev_id || i}
            name={m.name}
            slug={m.slug}
            usiId={m.usi_dev_id}
            portalMapping={m.portal_mapping || {}}
            website={m.website}
            invCount={m.investments_count}
            invList={m.inv_list}
            arriving={arrivingSlug === m.slug}
            sub={m.merged_at
              ? 'Połączono ' + new Date(m.merged_at).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', year: 'numeric' })
              : 'Połączony rekord'}
            footer={onUnmerge && (
              <button
                className="usi-btn sm ghost"
                title="Odłącz dewelopera"
                onClick={() => onUnmerge(m.usi_dev_id)}
              >
                <Icon name="x" size={12} />
              </button>
            )}
          />
        ))}
      </div>
    </div>
  );
}

function WedrowiecStatus({ dev }) {
  const crawler = dev?.crawler || {};
  const lastVisit = crawler.last_visit;
  const nextVisit = crawler.next_visit;
  const found = crawler.last_new_count ?? null;

  const fmt = iso => iso
    ? new Date(iso).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', year: 'numeric' })
    : '—';

  return (
    <div className="usi-card" style={{ padding: '12px 16px' }}>
      <div className="usi-label" style={{ marginBottom: 6 }}>Wędrowiec</div>
      {!lastVisit ? (
        <div className="usi-tiny usi-text-secondary">
          Brak wizyt
          {nextVisit && <> · planowana {fmt(nextVisit)}</>}
        </div>
      ) : (
        <div className="usi-tiny" style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <span>Ostatnia wizyta: <b>{fmt(lastVisit)}</b></span>
          <span>Znaleziono: <b>{found === 0 ? 'brak nowych' : `${found} nowych`}</b></span>
          <span className="usi-text-secondary">Powrót: {fmt(nextVisit)}</span>
        </div>
      )}
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
