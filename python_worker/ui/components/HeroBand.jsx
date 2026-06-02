// HeroBand.jsx — Top header for investment detail view

(function() {
  const { React, usiRegister, Icon, SourceBadge, MiniMap, WeightedUsiScore, ocenaLog } = window;

  const SourceLinks = ({ inv }) => {
    let links = [];
    if (inv.sources) {
        links = Object.entries(inv.sources).map(([source, data]) => ({ source, url: data.url }));
    } else if (inv.source_links) {
        links = inv.source_links;
    } else if (inv.source && inv.source_url) {
        links = [{ source: inv.source, url: inv.source_url }];
    }
    return (
      <div data-component="SourceLinks" className="source-links">
        {links.map((link, i) => (
          <a key={i} className="usi-btn sm ghost" href={link.url} target="_blank" rel="noopener">
            <SourceBadge source={link.source} /> <Icon name="arrow" size={11} />
          </a>
        ))}
        {inv.website && (
          <a className="usi-btn sm ghost" href={inv.website} target="_blank" rel="noopener" title="Oficjalna strona inwestycji">
            <Icon name="link" size={11} className="usi-m-r-4" /> Strona WWW
          </a>
        )}
      </div>
    );
  };
  usiRegister('SourceLinks', SourceLinks);

  const HeroBand = ({ inv, showMap }) => {
    const { useModuleContext } = window;
    const { geoPoint } = useModuleContext(inv);
    const score = ocenaLog(inv);
    const hasMap = showMap && geoPoint;

    return (
      <div data-component="HeroBand" className={`hero-band ${hasMap ? 'has-map' : 'no-map'}`}>
        <div>
          <div className="hero-band-title-row">
            <h1 className="usi-h1 hero-band-title">{inv.name}</h1>
            <span className="usi-body hero-band-developer">{inv.developer}</span>
            <SourceLinks inv={inv} />
          </div>
          <div className="hero-band-stats">
            {inv.usi_inv_id && <span className="usi-mono" style={{opacity: 0.6}}>ID: {inv.usi_inv_id}</span>}
            {((inv.location && inv.location.address) || inv.address) ? <span>📍 {(inv.location && inv.location.address) || inv.address}</span> : <span>📍 —</span>}
            {((inv.financials && inv.financials.price_avg) || inv.price_avg) > 0 ? <span className="usi-mono">{((inv.financials && inv.financials.price_avg) || inv.price_avg).toLocaleString('pl-PL')} zł/m²</span> : <span className="usi-mono">—</span>}
            <span className="usi-mono">{((inv.specifications && (inv.specifications.delivery_date || inv.specifications.delivery_quarter || inv.specifications.delivery_year)) || inv.delivery || '—')}</span>
          </div>
        </div>

        <div className="hero-band-score-col">
          <WeightedUsiScore score={score} size={56} />
        </div>

        {hasMap && (
          <div className="hero-band-map-col">
              <MiniMap geo={geoPoint} ratio={3} />
          </div>
        )}
      </div>
    );
  };
  usiRegister('HeroBand', HeroBand);

})();
