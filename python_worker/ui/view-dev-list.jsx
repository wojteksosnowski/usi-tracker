// view-dev-list.jsx — widok listy deweloperów

function DeveloperListGrid({ 
  developers = [], 
  onSelectDev = () => {}
}) {
  const { React, DataGrid, DeveloperCard } = window;
  
  return (
    <div data-component="DeveloperListGrid" style={{ height: '100%', overflow: 'hidden' }}>
      <DataGrid 
        data={developers}
        mode="grid"
        gridConfig={{ minCardWidth: 220, cardHeight: 340, gap: 16 }}
        onRowClick={onSelectDev}
        renderCard={(dev) => <DeveloperCard dev={dev} onSelect={() => onSelectDev(dev)} />}
        emptyMessage="Brak deweloperów pasujących do filtrów"
      />
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

Object.assign(window, { DeveloperListGrid, DeveloperCard });
