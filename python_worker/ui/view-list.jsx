// view-list.jsx — widok listy inwestycji

(function() {
  const { React, usiRegister, useDataBus, DataGrid, ListCard, ocenaLog } = window;

  function ViewList({ onSelectInv, mode = 'grid' }) {
    const { useDataBusSelector, DataBoundary, useRenderTracker } = window;
    if (useRenderTracker) useRenderTracker('ViewList');
    
    const investments = useDataBusSelector(state => state.visibleInvestments || []);
    
    const columns = React.useMemo(() => [
      { 
        key: 'photo', 
        label: '', 
        width: 60,
        render: (_, inv) => {
          const { resolvePhotoUrl } = window;
          const thumb = inv.photos && inv.photos.length > 0 ? inv.photos[0] : null;
          // Defensive check: resolvePhotoUrl might be missing due to race conditions
          const src = typeof resolvePhotoUrl === 'function' ? resolvePhotoUrl(thumb) : (typeof thumb === 'string' ? thumb : null);
          return src ? <img src={src} alt="" className="list-table-thumb" /> : <div className="list-table-thumb-empty" />;
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
      { key: 'delivery', label: 'Termin', sortable: true, width: 120, render: val => <span className="usi-mono">{val}</span> },
      { 
        key: 'price_avg', 
        label: 'Cena śr.', 
        sortable: true, 
        width: 140, 
        align: 'right', 
        render: (val) => {
          const { safeRender } = window;
          return <span className="usi-mono">{safeRender(val, 'currency')}</span>;
        }
      },
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
    ], [ocenaLog]);

    const renderCard = React.useCallback((inv) => (
      <DataBoundary data={inv}>
        {(validInv) => <ListCard inv={validInv} onSelect={() => onSelectInv(validInv)} />}
      </DataBoundary>
    ), [onSelectInv, ListCard]);

    return (
      <div data-component="ViewList" className="usi-h-full usi-overflow-hidden">
        <DataGrid 
          data={investments}
          mode={mode}
          columns={columns}
          rowHeight={56}
          gridConfig={{ minCardWidth: 280, cardHeight: 340, gap: 16 }}
          onRowClick={onSelectInv}
          renderCard={renderCard}
          emptyMessage="Brak wyników dla podanych filtrów"
        />
      </div>
    );
  }
  usiRegister('ViewList', ViewList);

})();
