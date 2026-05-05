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

  const handleScroll = (e) => setScrollTop(e.target.scrollTop);

  const isGrid = mode === 'grid';
  const effectiveRowHeight = isGrid ? gridConfig.cardHeight : rowHeight;
  
  // Dynamic calculation for responsive grid keeping virtualization sync
  let itemsPerRow = 1;
  if (isGrid) {
    if (gridConfig.minCardWidth && dimensions.width > 0) {
      const gap = gridConfig.gap !== undefined ? gridConfig.gap : 16;
      const horizontalPadding = 32; // padding grida to 16px (16 z lewej, 16 z prawej)
      const availableWidth = dimensions.width - horizontalPadding;
      itemsPerRow = Math.max(1, Math.floor((availableWidth + gap) / (gridConfig.minCardWidth + gap)));
    } else {
      itemsPerRow = gridConfig.itemsPerRow || 1;
    }
  }

  const totalRows = Math.ceil(data.length / itemsPerRow);
  
  const overscan = 5;
  const startRow = Math.max(0, Math.floor(scrollTop / effectiveRowHeight) - overscan);
  const endRow = Math.min(totalRows, Math.ceil((scrollTop + (dimensions.height || 600)) / effectiveRowHeight) + overscan);

  const visibleItems = data.slice(startRow * itemsPerRow, endRow * itemsPerRow);
  const paddingTop = startRow * effectiveRowHeight;
  const paddingBottom = Math.max(0, (totalRows - endRow) * effectiveRowHeight);

  if (data.length === 0) {
    return (
      <div className="usi-empty-state" style={{ padding: '40px 20px', textAlign: 'center', color: 'var(--usi-ink-4)' }}>
        <div style={{ fontSize: 32, marginBottom: 8 }}>🔍</div>
        <div className="usi-small">{emptyMessage}</div>
      </div>
    );
  }

  return (
    <div data-component="DataGrid" 
         ref={containerRef} 
         onScroll={handleScroll} 
         className="usi-scroll" 
         style={{ height: '100%', overflowY: 'auto', position: 'relative' }}>
      <div style={{ height: paddingTop }} />
      
      {isGrid ? (
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: `repeat(${itemsPerRow}, 1fr)`,
          gap: gridConfig.gap !== undefined ? gridConfig.gap : 16,
          padding: 16
        }}>
          {visibleItems.map((item, idx) => (
            <div key={item.slug || item.id || idx} onClick={() => onRowClick(item)}>
              {renderCard ? renderCard(item) : <pre style={{ fontSize: 10 }}>{JSON.stringify(item, null, 2)}</pre>}
            </div>
          ))}
        </div>
      ) : (
        <div className="usi-card" style={{ margin: 0, border: 'none', borderRadius: 0, background: 'transparent' }}>
          <table className="list-table" style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead className="list-table-head" style={{ position: 'sticky', top: 0, zIndex: 10 }}>
              <tr>
                {columns.map(col => (
                  <th 
                    key={col.key} 
                    className="list-table-th" 
                    style={{ 
                      width: col.width, 
                      textAlign: col.align || 'left',
                      cursor: col.sortable ? 'pointer' : 'default',
                      userSelect: 'none',
                      backgroundColor: 'var(--usi-surface-2)'
                    }}
                    onClick={() => col.sortable && onSort(col.key)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: 4, justifyContent: col.align === 'right' ? 'flex-end' : 'flex-start' }}>
                      <span style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{col.label}</span>
                      {col.sortable && sortKey === col.key && (
                        <Icon name={sortDir === 'asc' ? 'chevronDown' : 'chevronUp'} size={12} />
                      )}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {visibleItems.map((item, idx) => (
                <tr key={item.slug || item.id || idx} className="list-table-tr" onClick={() => onRowClick(item)}>
                  {columns.map(col => (
                    <td key={col.key} className="list-table-td" style={{ textAlign: col.align || 'left', height: rowHeight }}>
                      {col.render ? col.render(item[col.key], item) : item[col.key]}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      
      <div style={{ height: paddingBottom }} />
    </div>
  );
}
const MemoizedDataGrid = window.React.memo(DataGrid, (prev, next) => window.shallowCompare(prev, next));
window.usiRegister('DataGrid', MemoizedDataGrid);
