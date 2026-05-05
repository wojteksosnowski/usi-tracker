// modules-core.jsx — Module System engine and base components

(function() {
  const { React, usiRegister } = window;

  function useDarkMode() {
    const [dark, setDark] = React.useState(
      document.documentElement.dataset.dark === '1'
    );
    React.useEffect(() => {
      const obs = new MutationObserver(() =>
        setDark(document.documentElement.dataset.dark === '1')
      );
      obs.observe(document.documentElement, {
        attributes: true, attributeFilter: ['data-dark'],
      });
      return () => obs.disconnect();
    }, []);
    return dark;
  }
  usiRegister('useDarkMode', useDarkMode);

  const globalApiCache = new Map();

  function useApi() {
    const { React } = window;
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);

    const request = React.useCallback(async (url, options = {}) => {
      setLoading(true);
      setError(null);

      const isGet = !options.method || options.method.toUpperCase() === 'GET';
      const useCache = isGet && !options.noCache;

      if (useCache && globalApiCache.has(url)) {
        setLoading(false);
        return globalApiCache.get(url);
      }

      try {
        const res = await fetch(url, options);
        if (!res.ok) {
          throw new Error(`Błąd API: ${res.status} ${res.statusText}`);
        }
        const data = await res.json();

        if (useCache) {
          globalApiCache.set(url, data);
        }
        return data;
      } catch (err) {
        setError(err.message);
        // Safely try to notify via DataBus if available
        if (window.useDataBus) {
          try {
            const { setVariable } = window.useDataBus();
            if (setVariable) {
              setVariable('appStatus', { type: 'error', msg: err.message });
            }
          } catch(e) {}
        }
        throw err;
      } finally {
        setLoading(false);
      }
    }, []);

    const clearCache = React.useCallback((url) => {
      if (url) globalApiCache.delete(url);
      else globalApiCache.clear();
    }, []);

    return { request, loading, error, clearCache };
  }
  usiRegister('useApi', useApi);

  function BaseModule({ title, icon, children, errorFallback, style }) {
    const { Icon, ModuleErrorBoundary } = window;
    const containerRef = React.useRef(null);
    const [containerWidth, setContainerWidth] = React.useState(0);

    React.useEffect(() => {
      if (!containerRef.current) return;
      const observer = new ResizeObserver((entries) => {
        for (let entry of entries) {
          window.requestAnimationFrame(() => {
            setContainerWidth(entry.contentRect.width);
          });
        }
      });
      observer.observe(containerRef.current);
      return () => observer.disconnect();
    }, []);

    const enhancedChildren = React.Children.map(children, child => {
      if (React.isValidElement(child)) {
        return React.cloneElement(child, { containerWidth });
      }
      return child;
    });

    return (
      <div ref={containerRef} className="usi-card module-card" style={style}>
        {title && (
          <div className="module-header">
            {icon && <Icon name={icon} size={16} color="var(--usi-ink-3)" />}
            <span className="usi-h3" style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--usi-ink-2)' }}>{title}</span>
          </div>
        )}
        <div className="module-content">
          <ModuleErrorBoundary fallback={errorFallback}>
            {enhancedChildren}
          </ModuleErrorBoundary>
        </div>
      </div>
    );
  }
  usiRegister('BaseModule', BaseModule);

  const ModuleTypes = {
    RecordSet: 'RecordSet',
    GeoPoint: 'GeoPoint',
    Rating: 'Rating',
    Color: 'Color',
    Number: 'Number',
  };
  usiRegister('ModuleTypes', ModuleTypes);

  class ModuleSchemaValidator {
    static validate(schema, data) {
      const result = { valid: true, errors: [], aliasedData: {} };
      for (const [key, spec] of Object.entries(schema)) {
        const sourceKey = spec.from || key;
        const value = data[sourceKey];
        if (value === undefined && spec.required) {
          result.valid = false;
          result.errors.push(`Missing required field: ${sourceKey} for module input: ${key}`);
        } else if (value !== undefined) {
          if (spec.type === ModuleTypes.GeoPoint && (typeof value.lat !== 'number' || typeof value.lng !== 'number')) {
            result.valid = false; result.errors.push(`Invalid GeoPoint for ${sourceKey}`);
          } else if (spec.type === ModuleTypes.RecordSet && !Array.isArray(value)) {
            result.valid = false; result.errors.push(`Invalid RecordSet for ${sourceKey}`);
          }
          result.aliasedData[key] = value;
        }
      }
      return result;
    }
  }
  usiRegister('ModuleSchemaValidator', ModuleSchemaValidator);

  function validateModuleSpec(component, modConfig) {
    const spec = component?.__spec;
    const result = { valid: true, errors: [] };
    if (!spec || !spec.props) return result;
    
    const props = modConfig.props || {};
    for (const [key, propSpec] of Object.entries(spec.props)) {
      if (propSpec.required && props[key] === undefined) {
        result.valid = false;
        result.errors.push(`Brak wymaganego parametru: ${propSpec.label || key}`);
      }
    }
    return result;
  }
  usiRegister('validateModuleSpec', validateModuleSpec);

  const PropEditors = {
    String: ({ value, onChange }) => <input type="text" className="usi-input sm" value={value || ''} onChange={e => onChange(e.target.value)} />,
    Number: ({ value, onChange }) => <input type="number" className="usi-input sm" value={value || 0} onChange={e => onChange(Number(e.target.value))} />,
    Boolean: ({ value, onChange }) => <input type="checkbox" checked={value || false} onChange={e => onChange(e.target.checked)} />,
    Color: ({ value, onChange }) => <input type="color" value={value || '#000000'} style={{ height: 24, padding: 0, border: 'none', background: 'none', cursor: 'pointer' }} onChange={e => onChange(e.target.value)} />,
    Select: ({ value, onChange, options = [] }) => (
      <select className="usi-input sm" value={value || ''} onChange={e => onChange(e.target.value)}>
        {options.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
      </select>
    ),
    Range: ({ value, onChange, min = 0, max = 100, step = 1 }) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <input type="range" min={min} max={max} step={step} value={value || min} onChange={e => onChange(Number(e.target.value))} style={{ flex: 1 }} />
        <span className="usi-mono" style={{ fontSize: 10, width: 24 }}>{value}</span>
      </div>
    )
  };

  function ModuleKnobs({ spec, props, onChange }) {
    if (!spec || !spec.props) return null;
    return (
      <div className="usi-flex-column usi-gap-12" style={{ padding: 16, background: 'var(--usi-surface-3)', border: '1px solid var(--usi-border)', borderRadius: 10 }}>
        <div className="usi-small" style={{ fontWeight: 600, textTransform: 'uppercase', fontSize: 10, letterSpacing: '0.05em', opacity: 0.7 }}>Konfiguracja modułu</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
          {Object.entries(spec.props).map(([key, propSpec]) => {
            const Editor = PropEditors[propSpec.type] || PropEditors.String;
            const val = props[key] !== undefined ? props[key] : propSpec.default;
            return (
              <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span className="usi-small" style={{ fontSize: 10, color: 'var(--usi-ink-3)' }}>{propSpec.label || key}</span>
                <Editor 
                  value={val} 
                  onChange={v => onChange(key, v)} 
                  options={propSpec.options}
                  min={propSpec.min}
                  max={propSpec.max}
                  step={propSpec.step}
                />
              </div>
            );
          })}
        </div>
      </div>
    );
  }
  usiRegister('ModuleKnobs', ModuleKnobs);

  function ModuleWrapper({ component: Component, moduleSpec, context, title, icon, height }) {
    const { ModuleSchemaValidator, BaseModule } = window;
    const validation = ModuleSchemaValidator.validate(moduleSpec.inputs, context);
    if (!validation.valid) {
      return (
        <BaseModule title={title} icon={icon}>
          <div style={{ color: 'var(--usi-danger)', fontSize: 12 }}>
            {validation.errors.map((err, i) => <div key={i}>{err}</div>)}
          </div>
        </BaseModule>
      );
    }
    return (
      <BaseModule title={title} icon={icon}>
        <Component {...validation.aliasedData} height={height} />
      </BaseModule>
    );
  }
  usiRegister('ModuleWrapper', ModuleWrapper);

})();
