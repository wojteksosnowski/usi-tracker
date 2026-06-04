// modules-ui.jsx — UI utility and Container modules

(function() {
  const { React, usiRegister, ModuleRegistry, ModuleErrorBoundary, LocalModuleContext, BaseModule, validateModuleSpec, useApi, useDataBus } = window;

  // ─── Ratings Logic (Centralized from data.jsx and RatingsPanel.jsx) ───
  const _CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];
  usiRegister('USI_CATEGORIES_KEYS', _CATS);

  const ratedCount = (inv) =>
    _CATS.filter(k => ((inv.ratings || {})[k] ?? null) !== null).length;
  usiRegister('ratedCount', ratedCount);

  const avgRating = (inv) => {
    const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
    return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
  };
  usiRegister('avgRating', avgRating);

  const ratingStatus = (inv) => {
    const c = ratedCount(inv);
    if (c === 0) return 'none';
    if (c < 6) return 'partial';
    return 'done';
  };
  usiRegister('ratingStatus', ratingStatus);

  const ocenaLog = (inv) => {
    const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
    if (vals.length === 0) return null;
    const sum = vals.reduce((acc, v) => acc + Math.exp(v), 0);
    return Math.log(sum) - Math.log(vals.length);
  };
  usiRegister('ocenaLog', ocenaLog);

  // Session-level cache so ratings survive navigation without a full page reload.
  const _ratingCache = new Map();

  const useRatings = (inv) => {
    const { request } = useApi();
    const { setVariable } = useDataBus();
    
    const init = () => {
      const cached = _ratingCache.get(inv.slug);
      const base = cached ? cached.ratings : (inv.ratings || {});
      const r = {};
      _CATS.forEach(k => { r[k] = (base[k] ?? null); });
      return r;
    };

    const [ratings, setRatings] = React.useState(init);
    const [comment, setComment] = React.useState(() => {
      const cached = _ratingCache.get(inv.slug);
      return cached ? cached.comment : (inv.comment || '');
    });
    const [status, setStatus] = React.useState(() => {
      const cached = _ratingCache.get(inv.slug);
      return cached ? cached.status : (inv.status || 'Brak');
    });
    const [segment, setSegment] = React.useState(() => {
      const cached = _ratingCache.get(inv.slug);
      return cached ? cached.segment : (inv.specifications?.segment || '');
    });
    const [saved, setSaved] = React.useState(false);
    const debounceRef = React.useRef(null);

    React.useEffect(() => {
      const cached = _ratingCache.get(inv.slug);
      setRatings(init());
      setComment(cached ? cached.comment : (inv.comment || ''));
      setStatus(cached ? cached.status : (inv.status || 'Brak'));
      setSegment(cached ? cached.segment : (inv.specifications?.segment || ''));
      setSaved(false);
    }, [inv.slug, JSON.stringify(inv.ratings)]);

    const persist = (r, c, s, seg) => {
      const targetId = inv.usi_inv_id || inv.id;
      if (!targetId) {
        if (setVariable) setVariable('appStatus', { type: 'error', msg: 'Brak ID inwestycji' });
        return;
      }
      request(`/api/ratings/${targetId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...r, komentarz: c, status: s, Segment: seg }),
      })
        .then(() => {
          _ratingCache.set(inv.slug, { ratings: r, comment: c, status: s, segment: seg });
          setSaved(true);
          setVariable('appStatus', { type: 'success', msg: 'Ocena zapisana' });
          
          // Update status and ratings in the global bus so MetadataPanel etc. refresh immediately
          setVariable('investments', prev => {
            if (!Array.isArray(prev)) return prev;
            return prev.map(item => {
              if (item.usi_inv_id === inv.usi_inv_id) {
                const updatedSpec = { ...item.specifications, segment: seg };
                return { ...item, status: s, ratings: { ...r, komentarz: c, status: s, Segment: seg }, comment: c, specifications: updatedSpec, segment: seg };
              }
              return item;
            });
          });
          
          setTimeout(() => setSaved(false), 2000);
        })
        .catch(() => { /* Error handled by useApi */ });
    };

    const handleRating = (key, val) => {
      const next = { ...ratings, [key]: val };
      setRatings(next);
      persist(next, comment, status, segment);
    };

    const handleComment = (e) => {
      const val = e.target.value;
      setComment(val);
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => persist(ratings, val, status, segment), 800);
    };

    const handleStatus = (val) => {
      setStatus(val);
      persist(ratings, comment, val, segment);
    };

    const handleSegment = (val) => {
      setSegment(val);
      persist(ratings, comment, status, val);
    };

    return { ratings, setRatings, comment, setComment, status, setStatus, segment, setSegment, saved, handleRating, handleComment, handleStatus, handleSegment };
  };
  usiRegister('useRatings', useRatings);

  function NearbyInvestmentsModule({ items = [] }) {
    if (items.length === 0) return <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak innych inwestycji w promieniu 5km.</div>;
    return (
      <div className="usi-distance-list">
        {items.slice(0, 10).map(i => (
          <div key={i.slug} className="usi-distance-item">
            <div className="usi-distance-dot" />
            <div className="usi-distance-name">{i.name}</div>
            <div className="usi-mono usi-distance-km">{i.distance.toFixed(1)}km</div>
          </div>
        ))}
      </div>
    );
  }
  usiRegister('NearbyInvestmentsModule', NearbyInvestmentsModule);

  // ─── POI Module ───────────────────────────────────────────────────────────
  const POI_CATEGORY_LABELS = {
    food:          { label: 'Jedzenie',       icon: 'utensils'     },
    entertainment: { label: 'Rozrywka',       icon: 'star'         },
    outdoor:       { label: 'Tereny zielone', icon: 'map'          },
    transport:     { label: 'Transport',      icon: 'navigation'   },
    shopping:      { label: 'Zakupy',         icon: 'package'      },
    education:     { label: 'Edukacja',       icon: 'book'         },
    health:        { label: 'Zdrowie',        icon: 'heart'        },
  };

  function PoiModule({ inv }) {
    const [state, setState] = React.useState('idle'); // idle | loading | done | error | no-coords
    const [data, setData] = React.useState(null);
    const devSlug = inv?.developer_slug;
    const invSlug = inv?.investment_slug;

    const load = React.useCallback((forceRefresh = false) => {
      if (!devSlug || !invSlug) return;
      setState('loading');
      const base = `/api/poi/${investment.usi_inv_id}`;
      const url = forceRefresh ? base + '/fetch' : base;
      const opts = forceRefresh ? { method: 'POST' } : {};
      fetch(url, opts)
        .then(async res => {
          if (res.status === 404) { setState('idle'); return; }
          if (res.status === 422) { setState('no-coords'); return; }
          if (!res.ok) { setState('error'); return; }
          const d = await res.json();
          setData(d);
          setState('done');
        })
        .catch(() => setState('error'));
    }, [devSlug, invSlug]);

    React.useEffect(() => { load(false); }, [load]);

    const grouped = React.useMemo(() => {
      if (!data?.here_places) return {};
      const g = {};
      for (const p of data.here_places) {
        if (!g[p.category]) g[p.category] = [];
        g[p.category].push(p);
      }
      return g;
    }, [data]);

    const fetchedAt = data?.fetched_at
      ? new Date(data.fetched_at).toLocaleDateString('pl-PL', { day: 'numeric', month: 'short', year: 'numeric' })
      : null;

    return (
      <BaseModule title="Punkty zainteresowania" icon="map">
        {state === 'loading' && (
          <div className="usi-app-loading"><window.Spinner size={20} /></div>
        )}
        {state === 'no-coords' && (
          <div className="usi-empty-state"><div className="usi-small usi-text-secondary">Brak współrzędnych dla tej inwestycji.</div></div>
        )}
        {state === 'error' && (
          <div className="usi-empty-state"><div className="usi-small usi-text-secondary">Błąd pobierania POI.</div></div>
        )}
        {state === 'idle' && (
          <div className="usi-poi-empty">
            <div className="usi-small usi-text-secondary" style={{ marginBottom: 12 }}>Brak danych o punktach w okolicy.</div>
            <button className="usi-btn usi-btn-primary usi-small" onClick={() => load(true)}>
              Pobierz POI
            </button>
          </div>
        )}
        {state === 'done' && data && (
          <div className="usi-poi-content">
            <div className="usi-poi-header">
              {fetchedAt && <span className="usi-tiny usi-text-secondary">Dane z {fetchedAt}</span>}
              <button className="usi-btn usi-btn-ghost usi-tiny" onClick={() => load(true)} style={{ marginLeft: 'auto' }}>
                Odśwież
              </button>
            </div>

            {Object.entries(grouped).map(([cat, places]) => {
              const meta = POI_CATEGORY_LABELS[cat] || { label: cat, icon: 'map' };
              return (
                <div key={cat} className="usi-poi-group">
                  <div className="usi-poi-group-header">
                    <Icon name={meta.icon} size={13} />
                    <span className="usi-tiny" style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>{meta.label}</span>
                  </div>
                  {places.map((p, i) => (
                    <div key={i} className="usi-poi-item">
                      <div className="usi-poi-item-name usi-small">{p.name}</div>
                      <div className="usi-poi-item-dist usi-mono usi-tiny">{p.distance}m</div>
                    </div>
                  ))}
                </div>
              );
            })}

            {data.wiki_articles?.length > 0 && (
              <div className="usi-poi-group">
                <div className="usi-poi-group-header">
                  <Icon name="book" size={13} />
                  <span className="usi-tiny" style={{ fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>Wikipedia</span>
                </div>
                {data.wiki_articles.map((a, i) => (
                  <div key={i} className="usi-poi-item">
                    <a href={a.url} target="_blank" rel="noreferrer" className="usi-poi-item-name usi-small usi-link">{a.title}</a>
                    <div className="usi-poi-item-dist usi-mono usi-tiny">{Math.round(a.distance)}m</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </BaseModule>
    );
  }
  ModuleRegistry.register('PoiModule', PoiModule);
  usiRegister('PoiModule', PoiModule);

  function SkeletonModule({ shouldThrow = false }) {
    if (shouldThrow) throw new Error("Sztuczny błąd");
    return (
      <BaseModule title="Skeleton Test" icon="box">
        <div className="usi-skeleton-bar usi-pulse" />
      </BaseModule>
    );
  }
  usiRegister('SkeletonModule', SkeletonModule);

  function ContainerModule({ data, modules = [], filter, title, icon }) {
    const filteredData = React.useMemo(() => {
      if (!filter || !Array.isArray(data)) return data;
      return data.filter(inv => {
        for (const [k, v] of Object.entries(filter)) {
          if (inv[k] !== v) return false;
        }
        return true;
      });
    }, [data, filter]);

    return (
      <BaseModule title={title} icon={icon} className="usi-container-module">
        <LocalModuleContext.Provider value={filteredData}>
          <div className="usi-flex-column usi-gap-24 usi-container-module-content">
            {modules.map((mod, idx) => {
               const ModComponent = ModuleRegistry.get(mod.type);
               if (!ModComponent) return <div key={idx} className="usi-pill error">Nieznany moduł: {mod.type}</div>;
               
               const val = validateModuleSpec(ModComponent, mod);
               if (!val.valid) {
                 return <div key={idx} className="usi-pill error">Błąd konfiguracji {mod.type}: {val.errors.join(', ')}</div>;
               }

               return (
                 <ModuleErrorBoundary key={idx}>
                   <ModComponent data={filteredData} {...(mod.props || {})} modules={mod.modules} />
                 </ModuleErrorBoundary>
               );
            })}
          </div>
        </LocalModuleContext.Provider>
      </BaseModule>
    );
  }
  ModuleRegistry.register('ContainerModule', ContainerModule);
  usiRegister('ContainerModule', ContainerModule);

})();
