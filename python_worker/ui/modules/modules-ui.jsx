// modules-ui.jsx — UI utility and Container modules

(function() {
  const { React, usiRegister, ModuleRegistry, ModuleErrorBoundary, LocalModuleContext, BaseModule, validateModuleSpec } = window;

  function NearbyInvestmentsModule({ items = [] }) {
    if (items.length === 0) return <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak innych inwestycji w promieniu 5km.</div>;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {items.slice(0, 10).map(i => (
          <div key={i.slug} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--usi-accent)' }} />
            <div style={{ flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{i.name}</div>
            <div className="usi-mono" style={{ opacity: 0.6 }}>{i.distance.toFixed(1)}km</div>
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
      <BaseModule title={title} icon={icon} style={{ background: 'var(--usi-surface-2)', border: '1px solid var(--usi-border)' }}>
        <LocalModuleContext.Provider value={filteredData}>
          <div className="usi-flex-column usi-gap-24" style={{ padding: '4px 0' }}>
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
