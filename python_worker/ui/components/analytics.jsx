// analytics.jsx — Analytics and Metadata display modules

(function() {
  const { React, usiRegister, useDataBus } = window;

  const CategoryAvgRow = ({ label, avg, count, color }) => {
    const StarRating = window.StarRating;
    return (
      <div data-component="CategoryAvg-Row" className="usi-analytics-avg-row">
        <div className="usi-analytics-avg-label">{label}</div>
        <div className="usi-analytics-avg-bar-bg">
          <div className="usi-analytics-avg-bar-fill" 
            style={{ '--usi-avg-width': `${(avg / 5) * 100}%`, '--usi-avg-bg': color }} />
          <span className={`usi-mono usi-analytics-avg-value ${avg > 2.5 ? 'inverted' : ''}`}>
            {count > 0 ? avg.toFixed(2) : '—'}
          </span>
        </div>
        <div className="usi-small usi-analytics-avg-count">n={count}</div>
        {StarRating && <StarRating value={avg} readonly size={14} color={color} />}
      </div>
    );
  };
  usiRegister('CategoryAvgRow', CategoryAvgRow);

  const ProgressBarAnalytics = ({ rated, partial, total }) => {
    if (total === 0) return <div className="usi-small usi-text-secondary">Brak danych</div>;
    
    return (
      <>
        <div data-component="Progress-Bar" className="usi-analytics-progress-bar">
          <div className="usi-analytics-progress-segment complete" 
            style={{ '--usi-progress-width': `${rated/total*100}%` }}>
            {rated > 0 ? rated : ''}
          </div>
          <div className="usi-analytics-progress-segment partial" 
            style={{ '--usi-progress-width': `${partial/total*100}%` }}>
            {partial > 0 ? partial : ''}
          </div>
          <div className="usi-analytics-progress-segment unrated">
            {total - rated - partial > 0 ? total - rated - partial : ''}
          </div>
        </div>
        <div className="usi-analytics-legend-container">
          <div data-component="Legend" className="usi-analytics-legend-item">
            <span className="usi-analytics-legend-dot success" /> Pełne
          </div>
          <div data-component="Legend" className="usi-analytics-legend-item">
            <span className="usi-analytics-legend-dot warn" /> Częściowe
          </div>
          <div data-component="Legend" className="usi-analytics-legend-item">
            <span className="usi-analytics-legend-dot surface" /> Nieocenione
          </div>
        </div>
      </>
    );
  };
  usiRegister('ProgressBarAnalytics', ProgressBarAnalytics);

  const MetadataPanel = ({ inv, config }) => {
    const { safeRender } = window;
    if (!config) return <div className="usi-tiny">Ładowanie metadanych...</div>;

    const getValue = (obj, path) => {
      return path.split('.').reduce((acc, part) => acc && acc[part], obj);
    };

    const Row = ({ k, v, mono }) => (
      <div data-component="Metadata-Row">
        <div className="usi-small usi-m-b-1">{k}</div>
        <div className={`${mono ? 'usi-mono' : ''} usi-body usi-weight-500`}>{v}</div>
      </div>
    );

    return (
      <div data-component="MetadataPanel">
        <div className="usi-tiny usi-m-b-8">Metadane</div>
        <div data-component="Metadata-Grid" className="usi-metadata-grid">
          {config.map(field => {
            const val = getValue(inv, field.path);
            const rendered = field.type === 'count' 
              ? safeRender(Array.isArray(val) ? val.length : val, 'number')
              : safeRender(val, field.type === 'currency' ? 'currency' : 'string');

            return <Row key={field.key} k={field.label} v={rendered} mono={field.type === 'currency' || field.type === 'count'} />;
          })}
          {inv.folder_path && (
            <div data-component="Metadata-FolderPath" className="usi-metadata-folder-path">
              <div className="usi-small usi-m-b-1">Ścieżka folderu</div>
              <div className="usi-mono usi-metadata-folder-text">{inv.folder_path}</div>
            </div>
          )}
        </div>
      </div>
    );
  };
  usiRegister('MetadataPanel', MetadataPanel);

  const NavbarCounter = () => {
    const { bus } = useDataBus();
    const count = bus.visibleInvestments ? bus.visibleInvestments.length : 0;
    
    return (
      <div data-component="NavbarCounter" className="usi-mono usi-navbar-counter">
        <span className="usi-opacity-60">REKORDY:</span>
        <span className="usi-ink">{count}</span>
      </div>
    );
  };
  usiRegister('NavbarCounter', NavbarCounter);

})();

