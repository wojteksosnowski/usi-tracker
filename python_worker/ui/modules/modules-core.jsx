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
    const { React, useDataBus } = window;
    const [loading, setLoading] = React.useState(false);
    const [error, setError] = React.useState(null);
    const { setVariable } = useDataBus ? useDataBus() : { setVariable: null };

    const request = React.useCallback(async (url, options = {}) => {
      setLoading(true);
      setError(null);

      const isGet = !options.method || options.method.toUpperCase() === 'GET';
      // Never cache per-investment data — it changes on navigation and stale cache
      // causes wrong hero photo and "investment is not defined" errors.
      const noCacheUrl = url.match(/\/api\/investment\/[^/]+\/data/) || url.match(/\/api\/investment\/[^/]+$/);
      const useCache = isGet && !options.noCache && !noCacheUrl;

      if (useCache && globalApiCache.has(url)) {
        setLoading(false);
        return globalApiCache.get(url);
      }

      try {
        const res = await fetch(url, options);
        if (!res.ok) {
          let errorMsg = `Błąd API: ${res.status} ${res.statusText}`;
          try {
            const errData = await res.json();
            if (errData && errData.error) {
              errorMsg += ` - ${errData.error}`;
            }
          } catch (e) {
            // Ignore
          }
          throw new Error(errorMsg);
        }
        const data = await res.json();

        if (useCache) {
          globalApiCache.set(url, data);
        }
        return data;
      } catch (err) {
        const isAbort = err.name === 'AbortError' || err.message?.includes('aborted');
        setError(err.message);
        // Use setVariable from the outer scope (safely captured when hook was initialized)
        if (setVariable && !isAbort) {
          setVariable('appStatus', { type: 'error', msg: err.message });
        }
        throw err;
      } finally {
        setLoading(false);
      }
    }, [setVariable]);

    const clearCache = React.useCallback((url) => {
      if (url) globalApiCache.delete(url);
      else globalApiCache.clear();
    }, []);

    return { request, loading, error, clearCache };
  }
  usiRegister('useApi', useApi);

  function BaseModule({ title, icon, children, errorFallback, style, headerAction }) {
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
          <div className="module-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              {icon && <Icon name={icon} size={16} color="var(--usi-ink-3)" />}
              <span className="usi-h3 usi-base-module-title">{title}</span>
            </div>
            {headerAction && <div>{headerAction}</div>}
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

  function ModuleWrapper({ component: Component, moduleSpec, context, title, icon, height, headerAction, ...rest }) {
    const { ModuleSchemaValidator, BaseModule } = window;
    const validation = ModuleSchemaValidator.validate(moduleSpec.inputs, context);
    if (!validation.valid) {
      return (
        <BaseModule title={title} icon={icon} headerAction={headerAction}>
          <div className="usi-module-wrapper-error">
            {validation.errors.map((err, i) => <div key={i}>{err}</div>)}
          </div>
        </BaseModule>
      );
    }
    return (
      <BaseModule title={title} icon={icon} headerAction={headerAction}>
        <Component {...validation.aliasedData} height={height} {...rest} />
      </BaseModule>
    );
  }
  usiRegister('ModuleWrapper', ModuleWrapper);

})();
