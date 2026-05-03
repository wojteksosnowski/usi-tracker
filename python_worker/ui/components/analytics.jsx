// analytics.jsx — Analytics and Metadata display modules

function CategoryAvgRow({ label, avg, count, color }) {
  const { React, StarRating } = window;
  return (
    <div data-component="CategoryAvg-Row" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 100, fontSize: 13, fontWeight: 500 }}>{label}</div>
      <div style={{ flex: 1, height: 20, background: 'var(--usi-surface-3)', borderRadius: 4, position: 'relative' }}>
        <div style={{
          height: '100%', width: `${(avg / 5) * 100}%`,
          background: color, borderRadius: 4, transition: 'width .4s',
        }} />
        <span className="usi-mono" style={{
          position: 'absolute', right: 8, top: 1, fontSize: 11, fontWeight: 600,
          color: avg > 2.5 ? '#fff' : 'var(--usi-ink)',
        }}>{count > 0 ? avg.toFixed(2) : '—'}</span>
      </div>
      <div style={{ width: 36, textAlign: 'right' }} className="usi-small">n={count}</div>
      {StarRating && <StarRating value={avg} readonly size={14} color={color} />}
    </div>
  );
}

function ProgressBarAnalytics({ rated, partial, total }) {
  if (total === 0) return <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>Brak danych</div>;
  
  return (
    <>
      <div data-component="Progress-Bar" style={{ display: 'flex', height: 36, borderRadius: 6, overflow: 'hidden' }}>
        <div style={{ width: `${rated/total*100}%`, background: 'var(--usi-success)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
          {rated > 0 ? rated : ''}
        </div>
        <div style={{ width: `${partial/total*100}%`, background: 'var(--usi-warn)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 12, fontWeight: 600 }}>
          {partial > 0 ? partial : ''}
        </div>
        <div style={{ flex: 1, background: 'var(--usi-surface-3)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--usi-ink-3)', fontSize: 12, fontWeight: 600 }}>
          {total - rated - partial > 0 ? total - rated - partial : ''}
        </div>
      </div>
      <div style={{ display: 'flex', gap: 14, marginTop: 12, flexWrap: 'wrap' }}>
        <div data-component="Legend" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--usi-success)' }} /> Pełne
        </div>
        <div data-component="Legend" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--usi-warn)' }} /> Częściowe
        </div>
        <div data-component="Legend" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12 }}>
          <span style={{ width: 10, height: 10, borderRadius: 2, background: 'var(--usi-surface-3)' }} /> Nieocenione
        </div>
      </div>
    </>
  );
}

function MetadataPanel({ inv, config }) {
  if (!config) return <div className="usi-tiny">Ładowanie metadanych...</div>;

  const getValue = (obj, path) => {
    return path.split('.').reduce((acc, part) => acc && acc[part], obj);
  };

  const renderValue = (val, type) => {
    if (val === null || val === undefined || val === '') return '—';
    if (type === 'currency' && typeof val === 'number') return `${val.toLocaleString('pl-PL')} zł/m²`;
    if (Array.isArray(val)) return val.length;
    return val;
  };

  const Row = ({ k, v, mono }) => (
    <div data-component="Metadata-Row">
      <div className="usi-small" style={{ marginBottom: 1 }}>{k}</div>
      <div className={mono ? 'usi-mono' : ''} style={{ fontWeight: 500, fontSize: 13 }}>{v}</div>
    </div>
  );

  return (
    <div data-component="MetadataPanel">
      <div className="usi-tiny" style={{ marginBottom: 8 }}>Metadane</div>
      <div data-component="Metadata-Grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 16px' }}>
        {config.map(field => {
          const val = getValue(inv, field.path);
          return <Row key={field.key} k={field.label} v={renderValue(val, field.type)} mono={field.type === 'currency' || field.type === 'count'} />;
        })}
        {inv.folder_path && (
          <div data-component="Metadata-FolderPath" style={{ gridColumn: 'span 2', marginTop: 8 }}>
            <div className="usi-small" style={{ marginBottom: 1 }}>Ścieżka folderu</div>
            <div className="usi-mono" style={{ fontSize: 11, wordBreak: 'break-all', opacity: 0.8 }}>{inv.folder_path}</div>
          </div>
        )}
      </div>
    </div>
  );
}

// Global registration
Object.assign(window, {
  CategoryAvgRow, ProgressBarAnalytics, MetadataPanel
});
