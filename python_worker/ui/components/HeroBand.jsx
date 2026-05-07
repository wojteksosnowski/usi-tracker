// HeroBand.jsx — Top header for investment detail view

(function() {
  const { React, usiRegister, Icon, SourceBadge, MiniMap, WeightedUsiScore, ocenaLog } = window;

  const SourceLinks = ({ inv }) => {
    const links = inv.source_links || [{ source: inv.source, url: inv.source_url }];
    return (
      <div data-component="SourceLinks" className="source-links">
        {links.map((link, i) => (
          <a key={i} className="usi-btn sm ghost" href={link.url} target="_blank" rel="noopener">
            <SourceBadge source={link.source} /> <Icon name="arrow" size={11} />
          </a>
        ))}
      </div>
    );
  };
  usiRegister('SourceLinks', SourceLinks);

  const HeroBand = ({ inv, showMap, detailMode, onModeChange }) => {
    const { useModuleContext } = window;
    const { geoPoint } = useModuleContext(inv);
    const score = ocenaLog(inv);
    const hasMap = showMap && geoPoint;

    return (
      <div data-component="HeroBand" className={`hero-band ${hasMap ? 'has-map' : 'no-map'}`}>
        <div>
          <div className="hero-band-title-row">
            <h1 className="usi-h1">{inv.name}</h1>
            <span className="usi-body hero-band-developer">{inv.developer}</span>
          </div>
          <div className="hero-band-stats">
            {inv.address && <span>📍 {inv.address}</span>}
            {inv.price_avg > 0 && <span className="usi-mono">{inv.price_avg.toLocaleString('pl-PL')} zł/m²</span>}
            <span className="usi-mono">{inv.delivery}</span>
          </div>
          <div className="hero-band-actions-row">
              <SourceLinks inv={inv} />
              <div className="usi-divider-v" />
              <div className="mode-switch">
                  <button className={`usi-btn sm ghost mode-switch-btn ${detailMode === 'A' ? 'active' : ''}`} onClick={() => onModeChange('A')}>Standard</button>
                  <button className={`usi-btn sm ghost mode-switch-btn ${detailMode === 'C' ? 'active' : ''}`} onClick={() => onModeChange('C')}>Media</button>
              </div>
          </div>
        </div>

        <div className="hero-band-score-col">
          <WeightedUsiScore score={score} size={56} />
        </div>

        {hasMap && (
          <div className="hero-band-map-col">
              <MiniMap 
                geo={geoPoint} 
                height="100%" 
                hereUrl={inv.here_map_url} 
                hereUrlDark={inv.here_map_url_dark} 
              />
          </div>
        )}
      </div>
    );
  };
  usiRegister('HeroBand', HeroBand);

})();
