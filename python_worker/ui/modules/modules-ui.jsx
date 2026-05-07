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
    const [saved, setSaved] = React.useState(false);
    const debounceRef = React.useRef(null);

    React.useEffect(() => {
      const cached = _ratingCache.get(inv.slug);
      setRatings(init());
      setComment(cached ? cached.comment : (inv.comment || ''));
      setStatus(cached ? cached.status : (inv.status || 'Brak'));
      setSaved(false);
    }, [inv.slug]);

    const persist = (r, c, s) => {
      request(`/api/ratings/${inv.developer_slug}/${inv.investment_slug}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...r, komentarz: c, status: s }),
      })
        .then(() => {
          _ratingCache.set(inv.slug, { ratings: r, comment: c, status: s });
          setSaved(true);
          setVariable('appStatus', { type: 'success', msg: 'Ocena zapisana' });
          setTimeout(() => setSaved(false), 2000);
        })
        .catch(() => { /* Error handled by useApi */ });
    };

    const handleRating = (key, val) => {
      const next = { ...ratings, [key]: val };
      setRatings(next);
      persist(next, comment, status);
    };

    const handleComment = (e) => {
      const val = e.target.value;
      setComment(val);
      clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => persist(ratings, val, status), 800);
    };

    const handleStatus = (val) => {
      setStatus(val);
      persist(ratings, comment, val);
    };

    return { ratings, setRatings, comment, setComment, status, setStatus, saved, handleRating, handleComment, handleStatus };
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
