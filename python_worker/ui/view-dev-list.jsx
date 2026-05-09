// view-dev-list.jsx — widok listy deweloperów

function DeveloperListGrid({
  onSelectDev = () => {}
}) {
  const { React, DataGrid, DeveloperCard, useDataBus } = window;
  const { bus } = useDataBus();
  const { developers = [], filters = {} } = bus;
  const { search = '', sources = new Set() } = filters;
  const [onlyActive, setOnlyActive] = React.useState(false);

  const TWELVE_MONTHS_AGO = Date.now() / 1000 - 365 * 24 * 3600;

  const filteredDevelopers = React.useMemo(() => {
    return developers.filter(dev => {
      if (search) {
        const s = search.toLowerCase();
        const matches = (dev.name || '').toLowerCase().includes(s) ||
                        (dev.developer_slug || '').toLowerCase().includes(s) ||
                        (dev.usi_dev_id || '').toLowerCase().includes(s);
        if (!matches) return false;
      }
      if (sources.size > 0) {
        const devSources = Object.keys(dev.portal_mapping || {}).map(s => s.toLowerCase());
        const hasMatch = Array.from(sources).some(s => devSources.includes(s.toLowerCase()));
        if (!hasMatch) return false;
      }
      if (onlyActive) {
        if (!dev.last_updated || dev.last_updated < TWELVE_MONTHS_AGO) return false;
      }
      return true;
    });
  }, [developers, search, sources, onlyActive]);

  return (
    <div data-component="DeveloperListGrid" className="usi-h-full usi-flex-col usi-overflow-hidden">
      <div className="usi-dev-list-toolbar">
        <button
          className={`usi-btn sm ${onlyActive ? '' : 'ghost'}`}
          onClick={() => setOnlyActive(v => !v)}>
          Aktywni
        </button>
        <span className="usi-tiny usi-text-secondary">{filteredDevelopers.length} deweloperów</span>
      </div>
      <div className="usi-flex-1 usi-overflow-hidden">
        <DataGrid
          data={filteredDevelopers}
          mode="grid"
          gridConfig={{ minCardWidth: 220, cardHeight: 340, gap: 16 }}
          onRowClick={onSelectDev}
          renderCard={(dev) => <DeveloperCard dev={dev} onSelect={() => onSelectDev(dev)} />}
          emptyMessage="Brak deweloperów pasujących do filtrów"
        />
      </div>
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
      footerRight={
        <>
          {dev.new_since_review > 0 && (
            <div className="usi-pill solid success usi-tiny" title="Nowe inwestycje odkryte przez crawler">
              +{dev.new_since_review} nowe
            </div>
          )}
          {dev.suggestions && dev.suggestions.length > 0 && (
            <div className="usi-pill outline info usi-mono usi-tiny">
              Sugestie: {dev.suggestions.length}
            </div>
          )}
        </>
      }
    />
  );
}

Object.assign(window, { DeveloperListGrid, DeveloperCard });
