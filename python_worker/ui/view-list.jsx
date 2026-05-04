// view-list.jsx — widok listy inwestycji

function ListGrid({ 
  investments = [], 
  filteredInvestments = [],
  onSelectInv = () => {},
  mode = 'grid'
}) {
  const {
    React, StandardCard, SourceBadge, CategoryStripe, Icon,
    ocenaLog, avgRating
  } = window;
  
  // Virtualization state
  const containerRef = React.useRef(null);
  const [scrollTop, setScrollTop] = React.useState(0);
  const [dimensions, setDimensions] = React.useState({ 
    width: window.innerWidth, 
    height: window.innerHeight 
  });

  const handleScroll = (e) => {
    setScrollTop(e.target.scrollTop);
  };

  React.useEffect(() => {
    const update = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.offsetWidth,
          height: containerRef.current.offsetHeight
        });
      }
    };
    update();
    window.addEventListener('resize', update);
    return () => window.removeEventListener('resize', update);
  }, []);

  // Virtualization logic
  const rowHeight = mode === 'grid' ? 340 : 56;
  const viewHeight = dimensions.height || 800;
  const availableWidth = Math.max(dimensions.width - 48, 320);
  const itemsPerRow = mode === 'grid' ? Math.max(1, Math.floor(availableWidth / 220)) : 1; 
  const overscanRows = 4;
  
  const totalRows = Math.ceil(filteredInvestments.length / itemsPerRow);
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscanRows);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewHeight) / rowHeight) + overscanRows);
  
  const visibleItems = filteredInvestments.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * rowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * rowHeight);

  return (
    <div data-component="ListGrid" 
         ref={containerRef}
         onScroll={handleScroll}
         className="usi-scroll"
         style={{ height: '100%', overflowY: 'auto' }}
    >
      <div style={{ height: paddingTop }} />
      <div className="list-grid-layout" style={{ 
          display: mode === 'grid' ? 'grid' : 'block', 
          gridTemplateColumns: mode === 'grid' ? `repeat(${itemsPerRow}, 1fr)` : 'none',
          padding: '16px'
      }}>
        {mode === 'grid' ? (
          visibleItems.map(inv => <ListCard key={inv.slug} inv={inv} onSelect={() => onSelectInv(inv)} />)
        ) : (
          <ListTableContent investments={visibleItems} onSelectInv={onSelectInv} />
        )}
      </div>
      <div style={{ height: paddingBottom }} />
      
      {filteredInvestments.length === 0 && (
        <div className="list-empty-state" style={{ padding: '80px 20px', textAlign: 'center' }}>
          <div style={{ fontSize: 48, marginBottom: 16 }}>🔍</div>
          <div className="usi-body">Brak wyników dla podanych filtrów</div>
        </div>
      )}
    </div>
  );
}

function ListCard({ inv, onSelect }) {
  const avg = avgRating(inv);
  const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
  const { StandardCard, SourceBadge, CategoryStripe, Icon } = window;

  return (
    <StandardCard
      data-component="ListCard"
      image={thumb}
      title={inv.name}
      subtitle={inv.developer}
      extra={inv.district}
      onClick={onSelect}
      badges={<SourceBadge source={inv.source} />}
      footerLeft={<CategoryStripe ratings={inv.ratings || {}} />}
      footerRight={
        <div className="list-card-avg-box">
          <Icon name="star" size={12} />
          <span className="usi-mono" style={{ fontWeight: 600 }}>{avg.toFixed(2)}</span>
        </div>
      }
    />
  );
}

function ListTableContent({ investments = [], onSelectInv }) {
  const { SourceBadge, ocenaLog } = window;
  return (
    <div data-component="ListTableContent" className="usi-card list-table-container">
      <table className="list-table">
        <thead className="list-table-head">
          <tr>
            <th className="list-table-th" style={{ width: 60 }}></th>
            <th className="list-table-th">Inwestycja</th>
            <th className="list-table-th">Deweloper</th>
            <th className="list-table-th">Dzielnica</th>
            <th className="list-table-th" style={{ textAlign: 'right' }}>Ocena</th>
          </tr>
        </thead>
        <tbody>
          {investments.map(inv => {
            const score = ocenaLog(inv);
            const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
            return (
              <tr key={inv.slug} className="list-table-tr" onClick={() => onSelectInv(inv)}>
                <td className="list-table-td">
                  {thumb ? <img src={thumb} alt="" className="list-table-thumb" /> : <div className="list-table-thumb-empty" />}
                </td>
                <td className="list-table-td">
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <SourceBadge source={inv.source} />
                    <span style={{ fontWeight: 600 }}>{inv.name}</span>
                  </div>
                </td>
                <td className="list-table-td">{inv.developer}</td>
                <td className="list-table-td" style={{ color: 'var(--usi-ink-3)' }}>{inv.district}</td>
                <td className="list-table-td" style={{ textAlign: 'right' }}>
                  {score !== null ? <span className="usi-pill success usi-mono">{score.toFixed(2)}</span> : '—'}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

Object.assign(window, { ListGrid, ListTableContent });
