// view-library.jsx — Gallery of all available modules

(function() {
  const { React, usiRegister, ModuleRegistry, ModuleErrorBoundary, BaseModule, useDataBus } = window;

  function ModuleGalleryItem({ name, component: Component, spec }) {
    const { ModuleKnobs, useDataBus } = window;
    const { bus } = useDataBus();
    const [props, setProps] = React.useState(
      Object.entries(spec?.props || {}).reduce((acc, [k, v]) => {
        acc[k] = v.default;
        return acc;
      }, {})
    );

    const handleKnobChange = (key, val) => {
      setProps(prev => ({ ...prev, [key]: val }));
    };

    return (
      <div data-component="ModuleGalleryItem" className="usi-card" style={{ padding: 24, display: 'flex', flexDirection: 'column', gap: 20, background: 'var(--usi-surface-2)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', borderBottom: '0.5px solid var(--usi-border)', paddingBottom: 12 }}>
          <div>
            <h3 className="usi-h3" style={{ margin: 0, color: 'var(--usi-accent)' }}>{name}</h3>
            <div className="usi-tiny" style={{ opacity: 0.6 }}>ModuleRegistry Component</div>
          </div>
          <div className="usi-pill sm info">Spec: {spec ? 'YES' : 'NO'}</div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: 24 }}>
          <div className="usi-flex-column usi-gap-16">
            <div className="usi-small" style={{ fontWeight: 600 }}>PARAMETRY (KNOBS)</div>
            {spec ? (
              <ModuleKnobs spec={spec} props={props} onChange={handleKnobChange} />
            ) : (
              <div className="usi-small" style={{ color: 'var(--usi-ink-4)', fontStyle: 'italic' }}>Brak specyfikacji parametrów.</div>
            )}
            
            <div className="usi-small" style={{ fontWeight: 600, marginTop: 12 }}>TECHNICZNE</div>
            <div className="usi-mono" style={{ fontSize: 10, background: 'var(--usi-surface-3)', padding: 8, borderRadius: 6, border: '0.5px solid var(--usi-border)' }}>
              type: "{name}"<br/>
              props: {JSON.stringify(props, null, 2)}
            </div>
          </div>

          <div className="usi-flex-column usi-gap-16">
            <div className="usi-small" style={{ fontWeight: 600 }}>PODGLĄD (PREVIEW)</div>
            <div style={{ minHeight: 100, border: '1px dashed var(--usi-border)', borderRadius: 12, padding: 4, background: 'var(--usi-surface)' }}>
              <ModuleErrorBoundary>
                <Component {...props} data={bus?.visibleInvestments || []} />
              </ModuleErrorBoundary>
            </div>
          </div>
        </div>
      </div>
    );
  }

  function ViewLibrary() {
    const modules = ModuleRegistry.list();
    const [filter, setFilter] = React.useState('');

    const filtered = modules.filter(m => m.toLowerCase().includes(filter.toLowerCase()));

    return (
      <div data-component="ViewLibrary" className="usi-scroll" style={{ height: '100%', overflowY: 'auto', padding: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div>
            <h1 className="usi-h1" style={{ margin: 0 }}>Biblioteka Modułów</h1>
            <p className="usi-body" style={{ color: 'var(--usi-ink-3)', marginTop: 4 }}>
              Podgląd i testowanie wszystkich komponentów zarejestrowanych w systemie USI Module Registry.
            </p>
          </div>
          <div style={{ width: 300 }}>
             <input 
               type="text" 
               className="usi-input" 
               placeholder="Szukaj modułu..." 
               value={filter}
               onChange={e => setFilter(e.target.value)}
             />
          </div>
        </div>

        <div className="usi-flex-column usi-gap-32">
          {filtered.map(name => {
            const component = ModuleRegistry.get(name);
            return (
              <ModuleGalleryItem 
                key={name} 
                name={name} 
                component={component} 
                spec={component.__spec} 
              />
            );
          })}
        </div>

        {filtered.length === 0 && (
          <div className="usi-app-empty">Nie znaleziono modułów pasujących do "{filter}"</div>
        )}

        <div style={{ marginTop: 64, borderTop: '1px solid var(--usi-border)', paddingTop: 24, opacity: 0.5 }}>
           <div className="usi-small">System USI Tracker — Komunikacja techniczna komponentów</div>
        </div>
      </div>
    );
  }

  usiRegister('ViewLibrary', ViewLibrary);
})();
