// view-list.jsx — widok listy inwestycji

(function() {
  const { React, usiRegister, useDataBus, DataGrid, ListCard, ocenaLog } = window;

  function ViewList({ onSelectInv, mode = 'grid' }) {
    const { useDataBusSelector, DataBoundary, useRenderTracker } = window;
    if (useRenderTracker) useRenderTracker('ViewList');
    
    const investments = useDataBusSelector(state => state.visibleInvestments || []);
    
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
        render: (val, inv) => {
          const { SourceBadge } = window;
          return (
            <div className="datagrid-cell-name">
              <SourceBadge source={inv.source} />
              <span className="usi-weight-600">{val}</span>
            </div>
          );
        }
      },
      { key: 'developer', label: 'Deweloper', sortable: true },
      { key: 'district', label: 'Dzielnica', sortable: true, render: val => <span className="usi-text-secondary">{val}</span> },
      { 
        key: 'score', 
        label: 'Ocena', 
        width: 100, 
        align: 'right', 
        sortable: true,
        render: (_, inv) => {
          const score = ocenaLog ? ocenaLog(inv) : null;
          return score !== null ? <span className="usi-pill success usi-mono">{score.toFixed(2)}</span> : '—';
        }
      }
    ];

    return (
      <div data-component="ViewList" className="usi-h-full usi-overflow-hidden">
        <DataGrid 
          data={investments}
          mode={mode}
          columns={columns}
          rowHeight={56}
          gridConfig={{ itemsPerRow: 4, cardHeight: 340 }}
          onRowClick={onSelectInv}
          renderCard={(inv) => (
            <DataBoundary data={inv}>
              {(validInv) => <ListCard inv={validInv} onSelect={() => onSelectInv(validInv)} />}
            </DataBoundary>
          )}
          emptyMessage="Brak wyników dla podanych filtrów"
        />
      </div>
    );
  }
  usiRegister('ViewList', ViewList);

})();
