// DataGrid.jsx — Wirtualizowany grid danych

function DataGrid({
  data = [],
  columns = [],
  rowHeight = 52,
  mode = 'table',
  onRowClick = () => {},
  emptyMessage = "Brak danych",
  sortKey = null,
  sortDir = 'asc',
  onSort = () => {},
  gridConfig = { itemsPerRow: 3, cardHeight: 340 },
  renderCard = null
}) {
  const { React, Icon } = window;
  const containerRef = React.useRef(null);
  const rafRef = React.useRef(null);
  const [scrollTop, setScrollTop] = React.useState(0);
  const [dimensions, setDimensions] = React.useState({ width: 0, height: 0 });

  React.useEffect(() => {
    if (!containerRef.current) return;
    const obs = new ResizeObserver(entries => {
      for (let e of entries) {
        setDimensions({ width: e.contentRect.width, height: e.contentRect.height });
      }
    });
    obs.observe(containerRef.current);
    return () => obs.disconnect();
  }, []);

  const handleScroll = (e) => {
    const top = e.target.scrollTop;
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(() => setScrollTop(top));
  };

  const isGrid = mode === 'grid';

  // Table mode: no virtualization — renders all rows directly (no flicker, ~200 rows is cheap)
  if (!isGrid) {
    return (
      <div data-component="DataGrid" ref={containerRef}
           className="usi-scroll usi-datagrid-container">
        {data.length === 0
          ? <div className="usi-empty-state usi-datagrid-empty"><div className="usi-datagrid-empty-icon">🔍</div><div className="usi-small">{emptyMessage}</div></div>
          : (
            <div className="usi-card usi-datagrid-table-card">
              <table className="usi-datagrid-table list-table">
                <thead className="usi-datagrid-table-head list-table-head">
                  <tr>
                    {columns.map(col => {
                      const alignClass = col.align === 'right' ? 'usi-text-right' : (col.align === 'center' ? 'usi-text-center' : 'usi-text-left');
                      const justifyClass = col.align === 'right' ? 'usi-justify-end' : (col.align === 'center' ? 'usi-justify-center' : 'usi-justify-start');
                      return (
                        <th key={col.key}
                            className={`usi-datagrid-th list-table-th ${alignClass} ${col.sortable ? 'sortable' : ''}`}
                            style={{ width: col.width }}
                            onClick={() => col.sortable && onSort(col.key)}>
                          <div className={`usi-datagrid-th-content ${justifyClass}`}>
                            <span className="usi-datagrid-th-label">{col.label}</span>
                            {col.sortable && sortKey === col.key && (
                              <Icon name={sortDir === 'asc' ? 'chevronDown' : 'chevronUp'} size={12} />
                            )}
                          </div>
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {data.map((item, idx) => {
                    const itemKey = `${item.portal || item.source || 'inv'}-${item.id || item.slug || idx}`;
                    return (
                      <tr key={itemKey} className="list-table-tr" onClick={() => onRowClick(item)}>
                        {columns.map(col => {
                          const alignClass = col.align === 'right' ? 'usi-text-right' : (col.align === 'center' ? 'usi-text-center' : 'usi-text-left');
                          return (
                            <td key={col.key}
                                className={`usi-datagrid-td list-table-td ${alignClass}`}
                                style={{ height: rowHeight }}>
                              {col.render ? col.render(item[col.key], item) : item[col.key]}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        }
      </div>
    );
  }

  // Grid mode: virtualized
  // effectiveRowHeight must include the row gap so calculated total height
  // matches actual CSS grid height — otherwise the browser auto-corrects scroll.
  const gap = gridConfig.gap !== undefined ? gridConfig.gap : 16;
  const effectiveRowHeight = gridConfig.cardHeight + gap;
  let itemsPerRow = 1;
  if (gridConfig.minCardWidth && dimensions.width > 0) {
    const availableWidth = dimensions.width - 32 - 1;
    itemsPerRow = Math.max(1, Math.floor((availableWidth + gap) / (gridConfig.minCardWidth + gap)));
  } else {
    itemsPerRow = gridConfig.itemsPerRow || 1;
  }

  const totalRows = Math.ceil(data.length / itemsPerRow);
  const overscan = 3;
  const startRow = Math.max(0, Math.floor(scrollTop / effectiveRowHeight) - overscan);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + (dimensions.height || 600)) / effectiveRowHeight) + overscan);

  const visibleItems = data.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * effectiveRowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * effectiveRowHeight);

  if (data.length === 0) {
    return (
      <div className="usi-empty-state usi-datagrid-empty">
        <div className="usi-datagrid-empty-icon">🔍</div>
        <div className="usi-small">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div data-component="DataGrid"
         ref={containerRef}
         onScroll={handleScroll}
         className="usi-scroll usi-datagrid-container">
      <div style={{ height: paddingTop }} />
      <div className="usi-datagrid-grid"
           style={{
             '--usi-dg-cols': itemsPerRow,
             '--usi-dg-gap': `${gap}px`,
             gridAutoRows: `${gridConfig.cardHeight}px`
           }}>
        {visibleItems.map((item, idx) => {
          const itemKey = `${item.portal || item.source || 'inv'}-${item.id || item.slug || idx}`;
          return (
            <div key={itemKey} onClick={() => onRowClick(item)}>
              {renderCard ? renderCard(item) : <pre className="usi-datagrid-pre-debug">{JSON.stringify(item, null, 2)}</pre>}
            </div>
          );
        })}
      </div>
      <div style={{ height: paddingBottom }} />
    </div>
  );
}
const MemoizedDataGrid = window.React.memo(DataGrid, (prev, next) => window.shallowCompare(prev, next));
window.usiRegister('DataGrid', MemoizedDataGrid);
