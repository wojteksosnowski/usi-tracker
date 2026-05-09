// view-dev-list.jsx — widok listy deweloperów

function DeveloperListGrid({ 
  onSelectDev = () => {}
}) {
  const { React, DataGrid, DeveloperCard, useDataBus } = window;
  const { bus } = useDataBus();
  const { developers = [], filters = {} } = bus;
  const { search = '', sources = new Set(), cities = new Set() } = filters;
  
  const filteredDevelopers = React.useMemo(() => {
    return developers.filter(dev => {
      // 1. Search filter
      if (search) {
        const s = search.toLowerCase();
        const matches = (dev.name || '').toLowerCase().includes(s) || 
                        (dev.developer_slug || '').toLowerCase().includes(s) ||
                        (dev.usi_dev_id || '').toLowerCase().includes(s);
        if (!matches) return false;
      }

      // 2. Sources filter
      if (sources.size > 0) {
        const devSources = Object.keys(dev.portal_mapping || {}).map(s => s.toLowerCase());
        const hasMatch = Array.from(sources).some(s => devSources.includes(s.toLowerCase()));
        if (!hasMatch) return false;
      }

      // 3. City filter (from B05 - though user wants it removed from UI, keeping logic for consistency if active)
      if (cities.size > 0) {
         // Developers might not have a city field directly, but we could filter by investments if data is enriched
         // For now, if no city data on dev, we might just pass or filter out if city is selected.
         // Assuming we want to filter devs who HAVE investments in these cities.
         // This requires more data than currently in 'dev' object.
      }

      return true;
    });
  }, [developers, search, sources, cities]);

  return (
    <div data-component="DeveloperListGrid" className="usi-h-full usi-overflow-hidden">
      <DataGrid 
        data={filteredDevelopers}
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
  const { React, StandardCard, SourceBadge } = window;
  const portals = dev.portal_mapping || {};
  const hasRp = !!portals.rp;
  const hasOto = !!portals.oto;
  const hasTo = !!portals.to;

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
          <div className="usi-body usi-weight-600">
            {dev.investments_count || 0} 
            <small className="usi-text-secondary usi-weight-400"> inwestycji</small>
          </div>
          {dev.website && <div className="usi-tiny usi-text-secondary" style={{ maxWidth: 140, overflow: 'hidden', textOverflow: 'ellipsis' }}>{dev.website}</div>}
        </div>
      }
      footerRight={dev.suggestions && dev.suggestions.length > 0 && (
        <div className="usi-pill outline info usi-mono usi-tiny">
          Sugestie: {dev.suggestions.length}
        </div>
      )}
    />
  );
}

Object.assign(window, { DeveloperListGrid, DeveloperCard });
