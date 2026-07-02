// view-dev-list.jsx — widok listy deweloperów

const DEV_PAGE_SIZE = 60;

function DeveloperListGrid({
  onSelectDev = () => {}
}) {
  const { React, DataGrid, DeveloperCard, useDataBus, SourceBadge } = window;
  const { bus, setVariable } = useDataBus();
  const { developers = [], filters = {}, devFilters = {}, devListMode = 'grid' } = bus;
  const { search = '', sources = new Set() } = filters;
  const { onlyActive = false, onlyMerged = false, onlyPending = false } = devFilters;

  const [displayedCount, setDisplayedCount] = React.useState(DEV_PAGE_SIZE);
  const [loading, setLoading] = React.useState(false);
  const loadMoreRef = React.useRef(null);

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
      if (onlyMerged) {
        const hasChildren = (dev.merged_from || []).length > 0;
        const pm = dev.portal_mapping || {};
        const hasMapping = !!(pm.rp || pm.oto || pm.to);
        if (!(hasChildren || hasMapping)) return false;
      }

      if (onlyPending) {
        if (!dev.unregistered_count || dev.unregistered_count <= 0) return false;
      }
      return true;
    });
  }, [developers, search, sources, onlyActive, onlyMerged, onlyPending]);

  // Reset pagination whenever the filtered set changes
  React.useEffect(() => {
    setDisplayedCount(DEV_PAGE_SIZE);
  }, [filteredDevelopers.length, search, sources, onlyActive, onlyMerged, onlyPending]);

  const displayedDevelopers = React.useMemo(
    () => filteredDevelopers.slice(0, displayedCount),
    [filteredDevelopers, displayedCount]
  );

  const hasMore = displayedCount < filteredDevelopers.length;

  // Load the next page when sentinel comes into view
  const loadNextPage = React.useCallback(() => {
    setLoading(true);
    // Defer to keep the browser responsive during large list slicing
    setTimeout(() => {
      setDisplayedCount(prev => Math.min(prev + DEV_PAGE_SIZE, filteredDevelopers.length));
      setLoading(false);
    }, 100);
  }, [filteredDevelopers.length]);

  // KROK 2: Bezpiecznik — observer jest tworzony tylko gdy hasMore && !loading
  React.useEffect(() => {
    if (loading || !hasMore) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          loadNextPage();
        }
      },
      { threshold: 0.1 }
    );

    if (loadMoreRef.current) {
      observer.observe(loadMoreRef.current);
    }

    return () => observer.disconnect();
  }, [loading, hasMore, loadNextPage]);

  const devIds = displayedDevelopers.map(d => d.usi_dev_id).join(',');
  React.useEffect(() => {
    setVariable('visibleDevelopers', filteredDevelopers);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [devIds, setVariable]);

  const devColumns = React.useMemo(() => [
    {
      key: 'name',
      label: 'Deweloper',
      render: (val, dev) => (
        <div>
          <div className="usi-body usi-weight-600">{dev.name}</div>
          <div className="usi-mono usi-tiny usi-text-secondary">{dev.developer_slug} · {dev.usi_dev_id}</div>
        </div>
      )
    },
    {
      key: 'portal_mapping',
      label: 'Portale',
      width: 120,
      render: (val, dev) => (
        <div className="usi-flex-row usi-gap-4">
          {dev.portal_mapping?.rp && <SourceBadge source="rp" />}
          {dev.portal_mapping?.oto && <SourceBadge source="oto" />}
          {dev.portal_mapping?.to && <SourceBadge source="to" />}
        </div>
      )
    },
    {
      key: 'investments_count',
      label: 'Inwest.',
      width: 80,
      align: 'right',
      sortable: true,
      render: (val) => <span className="usi-body usi-weight-600">{val || 0}</span>
    },
    {
      key: 'new_since_review',
      label: 'Nowe',
      width: 70,
      align: 'center',
      render: (val) => val > 0
        ? <span className="usi-pill solid success usi-tiny">+{val}</span>
        : <span className="usi-text-secondary">—</span>
    },
    {
      key: 'unregistered_count',
      label: 'Odkrycia',
      width: 70,
      align: 'center',
      render: (val) => val > 0
        ? <span className="usi-pill solid warning usi-tiny">+{val}</span>
        : <span className="usi-text-secondary">—</span>
    },
  ], [SourceBadge]);

  return (
    <div data-component="DeveloperListGrid"
         className="usi-h-full"
         style={{ overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      <DataGrid
        data={displayedDevelopers}
        mode={devListMode}
        columns={devColumns}
        gridConfig={{ minCardWidth: 220, cardHeight: 340, gap: 16 }}
        onRowClick={onSelectDev}
        renderCard={(dev) => <DeveloperCard dev={dev} onSelect={() => onSelectDev(dev)} />}
        emptyMessage="Brak deweloperów pasujących do filtrów"
        defaultSortKey="investments_count"
        defaultSortDir="desc"
      />
      {/* KROK 1: Sentinel renderowany warunkowo — tylko gdy jest co ładować i nie trwa ładowanie */}
      {hasMore && !loading && (
        <div
          ref={loadMoreRef}
          className="h-10 my-4 flex items-center justify-center text-muted-foreground text-sm"
        >
          Ładowanie kolejnych deweloperów...
        </div>
      )}
    </div>
  );
}

function DeveloperCard({ dev, onSelect }) {
  const { React, StandardCard, SourceBadge } = window;
  const portals = dev.portal_mapping || {};
  const hasRp = !!portals.rp;
  const hasOto = !!portals.oto;
  const hasTo = !!portals.to;

  const logoUrl = `/api/developer/${dev.usi_dev_id}/logo`;

  return (
    <StandardCard
      image={logoUrl}
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
          {dev.unregistered_count > 0 && (
            <div className="usi-pill solid warning usi-tiny" title="Nowe inwestycje znalezione w discovery (niezarejestrowane)" style={{ marginBottom: 4 }}>
              {dev.unregistered_count} nowości
            </div>
          )}
          {dev.new_since_review > 0 && (
            <div className="usi-pill solid success usi-tiny" title="Nowe inwestycje odkryte przez crawler" style={{ marginBottom: 4 }}>
              +{dev.new_since_review} nowe
            </div>
          )}

        </>
      }
    />
  );
}

Object.assign(window, { DeveloperListGrid, DeveloperCard });
