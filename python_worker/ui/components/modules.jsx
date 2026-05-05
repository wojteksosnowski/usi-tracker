// modules.jsx — Module System architecture

function useDarkMode() {
  const { React } = window;
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
  }, [React]);
  return dark;
}
window.usiRegister('useDarkMode', useDarkMode);

function BaseModule({ title, icon, children, errorFallback, style }) {
  const { React, Icon, ModuleErrorBoundary } = window;
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
window.usiRegister('BaseModule', BaseModule);

const ModuleTypes = {
  RecordSet: 'RecordSet',
  GeoPoint: 'GeoPoint',
  Rating: 'Rating',
  Color: 'Color',
  Number: 'Number',
};
window.usiRegister('ModuleTypes', ModuleTypes);

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
window.usiRegister('ModuleSchemaValidator', ModuleSchemaValidator);

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
window.usiRegister('ModuleWrapper', ModuleWrapper);

function MiniMap({ geo, label, height = 140, points = [], hereUrl = '', hereUrlDark = '', coords, containerWidth }) {
  const { React, useDarkMode } = window;
  const mapCoords = geo ? [geo.lat, geo.lng] : coords;
  React.useEffect(() => {
    if (containerWidth > 0) { console.log(`[MiniMap] containerWidth: ${Math.round(containerWidth)}px`); }
  }, [containerWidth]);
  if (!mapCoords || mapCoords[0] === 0) return null;
  const url = `https://www.google.com/maps/@${mapCoords[0]},${mapCoords[1]},780m/`;
  const isDark = useDarkMode();
  const imgSrc = (isDark && hereUrlDark) ? hereUrlDark : hereUrl;
  return (
    <a data-component="MiniMap" href={url} target="_blank" rel="noopener" title="Otwórz w Google Maps"
      style={{
        display: 'block', position: 'relative', height, width: '100%',
        borderRadius: 10, overflow: 'hidden', textDecoration: 'none',
        background: 'var(--usi-surface-3)',
        border: '.5px solid var(--usi-border)',
      }}>
      {imgSrc ? (
        <img src={imgSrc} alt="Mapa lokalizacji" style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }} />
      ) : (
        <svg viewBox="0 0 300 200" preserveAspectRatio="none" style={{ width: '100%', height: '100%', display: 'block' }}>
          <rect x="0" y="0" width="300" height="200" fill="var(--usi-surface-3)" />
          <path d="M0 40 L80 50 L120 30 L200 35 L300 60 L300 0 L0 0 Z" fill="color-mix(in oklab, #7DB951 18%, transparent)" />
          <path d="M0 160 L40 165 L80 158 L120 170 L160 168 L200 175 L240 170 L300 178 L300 200 L0 200 Z" fill="color-mix(in oklab, #3989C6 18%, transparent)" />
          <g stroke="var(--usi-border-strong)" strokeWidth="1.2" fill="none" opacity="0.6">
            <path d="M-10 95 L310 105" /><path d="M-10 70 L310 75" /><path d="M-10 130 L310 138" />
            <path d="M70 -10 L75 210" /><path d="M150 -10 L160 210" /><path d="M225 -10 L230 210" />
          </g>
          <g transform="translate(150,100)">
            <circle r="14" fill="var(--usi-accent, #E5006D)" opacity="0.18" />
            <circle r="7" fill="var(--usi-accent, #E5006D)" stroke="#fff" strokeWidth="2" />
          </g>
        </svg>
      )}
    </a>
  );
}
window.usiRegister('MiniMap', MiniMap);

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
window.usiRegister('NearbyInvestmentsModule', NearbyInvestmentsModule);

function SkeletonModule({ shouldThrow = false }) {
  const { BaseModule } = window;
  if (shouldThrow) throw new Error("Sztuczny błąd");
  return (
    <BaseModule title="Skeleton Test" icon="box">
      <div className="usi-skeleton-bar usi-pulse" />
    </BaseModule>
  );
}
window.usiRegister('SkeletonModule', SkeletonModule);


