// view-dev-list.jsx — widok listy deweloperów

function DeveloperListGrid({ 
  developers = [], 
  onSelectDev = () => {}
}) {
  const { React, StandardCard, SourceBadge } = window;
  
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

  const rowHeight = 340;
  const viewHeight = dimensions.height || 800;
  const availableWidth = Math.max(dimensions.width - 48, 320);
  const itemsPerRow = Math.max(1, Math.floor(availableWidth / 220)); 
  const overscanRows = 4;
  
  const totalRows = Math.ceil(developers.length / itemsPerRow);
  const startRow = Math.max(0, Math.floor(scrollTop / rowHeight) - overscanRows);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + viewHeight) / rowHeight) + overscanRows);
  
  const visibleItems = developers.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * rowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * rowHeight);

  return (
    <div data-component="DeveloperListGrid" 
         ref={containerRef}
         onScroll={handleScroll}
         className="usi-scroll"
         style={{ height: '100%', overflowY: 'auto' }}
    >
      <div style={{ paddingTop, paddingBottom, minHeight: '100%', padding: '16px' }}>
        <div className="developer-grid-layout" style={{ 
          display: 'grid',
          gridTemplateColumns: `repeat(${itemsPerRow}, 1fr)`, 
          gap: '16px'
        }}>
          {visibleItems.map(dev => <DeveloperCard key={dev.usi_dev_id} dev={dev} onSelect={() => onSelectDev(dev)} />)}
        </div>
      </div>
      
      {developers.length === 0 && (
        <div className="developer-empty-state" style={{ padding: '80px 20px', textAlign: 'center' }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>🔍</div>
          <div className="usi-body">Brak deweloperów pasujących do filtrów</div>
        </div>
      )}
    </div>
  );
}

function DeveloperCard({ dev, onSelect }) {
  const portals = dev.portal_mapping || {};
  const hasRp = !!portals.rp;
  const hasOto = !!portals.oto;
  const hasTo = !!portals.to;
  const { StandardCard, SourceBadge } = window;

  return (
    <StandardCard
      title={dev.name}
      subtitle={dev.usi_dev_id}
      extra={dev.developer_slug}
      onClick={onSelect}
      badges={
        <>
          {hasRp && <SourceBadge source="rp" />}
          {hasOto && <SourceBadge source="oto" />}
          {hasTo && <SourceBadge source="to" />}
        </>
      }
      footerLeft={
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--usi-ink)' }}>
            {dev.investments_count || 0} 
            <small style={{ fontWeight: 400, opacity: 0.6 }}> inwestycji</small>
          </div>
          {dev.website && <div className="usi-tiny" style={{ opacity: 0.6, maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{dev.website}</div>}
        </div>
      }
      footerRight={dev.suggestions && dev.suggestions.length > 0 && (
        <div className="usi-pill outline usi-mono" style={{ fontSize: 10, borderColor: 'var(--usi-accent)', color: 'var(--usi-accent)' }}>
          Sugestie: {dev.suggestions.length}
        </div>
      )}
    />
  );
}

Object.assign(window, { DeveloperListGrid });
