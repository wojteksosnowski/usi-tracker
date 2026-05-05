// HeroBand.jsx — Top header for investment detail view

(function() {
  const { React, usiRegister, Icon, SourceBadge, MiniMap, WeightedUsiScore, ocenaLog } = window;

  const SourceLinks = ({ inv }) => {
    const links = inv.source_links || [{ source: inv.source, url: inv.source_url }];
    return (
      <div data-component="SourceLinks" className="source-links" style={{ display: 'flex', gap: 8 }}>
        {links.map((link, i) => (
          <a key={i} className="usi-btn sm ghost" href={link.url} target="_blank" rel="noopener" style={{ padding: '4px 8px' }}>
            <SourceBadge source={link.source} /> <Icon name="arrow" size={11} />
          </a>
        ))}
      </div>
    );
  };
  usiRegister('SourceLinks', SourceLinks);

  const HeroBand = ({ inv, showMap, moduleContext, detailMode, onModeChange }) => {
    const score = ocenaLog(inv);
    const hasMap = showMap && inv.coords[0] !== 0;

    return (
      <div data-component="HeroBand" className="hero-band" style={{
        display: 'grid',
        gridTemplateColumns: hasMap ? '1fr auto 280px' : '1fr auto',
        gap: 24,
        paddingBottom: 24,
        borderBottom: '.5px solid var(--usi-border)',
        marginBottom: 24
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 4 }}>
            <h1 className="usi-h1" style={{ margin: 0 }}>{inv.name}</h1>
            <span className="usi-body" style={{ opacity: 0.6 }}>{inv.developer}</span>
          </div>
          <div style={{ display: 'flex', gap: 16, color: 'var(--usi-ink-3)', fontSize: 13, marginBottom: 12 }}>
            {inv.address && <span>📍 {inv.address}</span>}
            {inv.price_avg > 0 && <span className="usi-mono">{inv.price_avg.toLocaleString('pl-PL')} zł/m²</span>}
            <span className="usi-mono">{inv.delivery}</span>
          </div>
          <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <SourceLinks inv={inv} />
              <div style={{ width: 1, height: 16, background: 'var(--usi-border)' }} />
              <div style={{ display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2 }}>
                  <button className="usi-btn sm ghost" style={{ background: detailMode === 'A' ? 'var(--usi-surface)' : 'transparent', fontSize: 11 }} onClick={() => onModeChange('A')}>Standard</button>
                  <button className="usi-btn sm ghost" style={{ background: detailMode === 'C' ? 'var(--usi-surface)' : 'transparent', fontSize: 11 }} onClick={() => onModeChange('C')}>Media</button>
              </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center' }}>
          <WeightedUsiScore score={score} size={56} />
        </div>

        {hasMap && moduleContext && (
          <div style={{ height: 100, borderRadius: 12, overflow: 'hidden', border: '.5px solid var(--usi-border)' }}>
              <MiniMap coords={inv.coords} height="100%" />
          </div>
        )}
      </div>
    );
  };
  usiRegister('HeroBand', HeroBand);

})();
