// view-list.jsx — widok listy inwestycji

(function() {
  const { React, usiRegister, useDataBus, DataGrid, StandardCard, SourceBadge, CategoryStripe, Icon, ocenaLog, avgRating } = window;

  const ListCard = ({ inv, onSelect }) => {
    const avg = avgRating(inv);
    const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;

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
  };
  usiRegister('ListCard', ListCard);

  function ViewList({ onSelectInv, mode = 'grid' }) {
    const { bus } = useDataBus();
    const investments = bus.visibleInvestments || [];
    
    const columns = [
      { 
        key: 'photo', 
        label: '', 
        width: 60,
        render: (_, inv) => {
          const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
          return thumb ? <img src={thumb} alt="" className="list-table-thumb" /> : <div className="list-table-thumb-empty" />;
        }
      },
      { 
        key: 'name', 
        label: 'Inwestycja', 
        sortable: true,
        render: (val, inv) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <SourceBadge source={inv.source} />
            <span style={{ fontWeight: 600 }}>{val}</span>
          </div>
        )
      },
      { key: 'developer', label: 'Deweloper', sortable: true },
      { key: 'district', label: 'Dzielnica', sortable: true, render: val => <span style={{ color: 'var(--usi-ink-3)' }}>{val}</span> },
      { 
        key: 'score', 
        label: 'Ocena', 
        width: 100, 
        align: 'right', 
        sortable: true,
        render: (_, inv) => {
          const score = ocenaLog(inv);
          return score !== null ? <span className="usi-pill success usi-mono">{score.toFixed(2)}</span> : '—';
        }
      }
    ];

    return (
      <div data-component="ViewList" style={{ height: '100%', overflow: 'hidden' }}>
        <DataGrid 
          data={investments}
          mode={mode}
          columns={columns}
          rowHeight={56}
          gridConfig={{ itemsPerRow: 4, cardHeight: 340 }}
          onRowClick={onSelectInv}
          renderCard={(inv) => <ListCard inv={inv} onSelect={() => onSelectInv(inv)} />}
          emptyMessage="Brak wyników dla podanych filtrów"
        />
      </div>
    );
  }
  usiRegister('ViewList', ViewList);

})();

