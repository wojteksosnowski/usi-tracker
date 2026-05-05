// view-reports.jsx — Widok raportów USI

function ReportsList({ onSelectReport }) {
  const { React, Spinner, Icon, useApi } = window;
  const [reports, setReports] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const { request } = useApi();

  const fetchReports = React.useCallback(() => {
    setLoading(true);
    request('/api/reports')
      .then(data => {
        setReports(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [request]);

  React.useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  return (
    <div data-component="ReportsList" className="reports-list-content usi-scroll">
        {loading ? (
          <div className="usi-app-loading"><Spinner /></div>
        ) : reports.length === 0 ? (
          <div className="usi-app-empty">Brak definicji raportów w Public/USIdata/reports/</div>
        ) : (
          <div className="reports-grid-layout">
            {reports.map(report => (
              <div key={report.id} 
                data-component="ReportCard"
                className="usi-card report-card" 
                onClick={() => onSelectReport(report)}>
                <h2 className="usi-h2">{report.title}</h2>
                <p className="usi-small">{report.description}</p>
                <div className="report-card-footer">
                  <button className="usi-btn sm">Otwórz <Icon name="arrow" size={12} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
    </div>
  );
}

function DataGridModule({ data: investments, ...props }) {
  const { React, DataGrid, SourceBadge } = window;
  const [sort, setSort] = React.useState({ key: 'name', dir: 'asc' });

  const handleSort = (key) => {
    setSort(prev => ({
      key,
      dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc'
    }));
  };

  const sortedData = React.useMemo(() => {
    return [...investments].sort((a, b) => {
      const va = a[sort.key] || '';
      const vb = b[sort.key] || '';
      if (va < vb) return sort.dir === 'asc' ? -1 : 1;
      if (va > vb) return sort.dir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [investments, sort]);

  const columns = [
    { 
      key: 'name', 
      label: 'Inwestycja', 
      sortable: true,
      render: (val, row) => (
        <div className="datagrid-cell-name">
          <SourceBadge source={row.source} />
          <span className="usi-weight-600">{val}</span>
        </div>
      )
    },
    { key: 'developer', label: 'Deweloper', sortable: true },
    { key: 'district', label: 'Dzielnica', sortable: true },
    { 
      key: 'status', 
      label: 'Status', 
      sortable: true,
      render: (val) => <span className={`usi-pill ${val === 'Ukończona' ? 'success' : 'info'}`}>{val}</span>
    }
  ];

  return (
    <div className="usi-card datagrid-module-container">
        <DataGrid 
          data={sortedData} 
          columns={columns}
          sortKey={sort.key}
          sortDir={sort.dir}
          onSort={handleSort}
          onRowClick={(row) => console.log("Clicked row:", row)}
        />
    </div>
  );
}
window.ModuleRegistry.register('DataGridModule', DataGridModule);

// ─── Presets Registration (Krok B03) ───────────────────────────────────
window.ModuleRegistry.registerPreset('DeveloperOverview', [
  { type: 'PriceTrendModule', props: { title: 'Trend Inwestycji Dewelopera' } },
  { type: 'MapModule', props: { title: 'Lokalizacje Inwestycji', height: 300 } },
  { type: 'DataGridModule' }
]);

window.ModuleRegistry.registerPreset('LocationAnalysis', [
  { type: 'MapModule', props: { title: 'Mapa Analizy Okolicy', height: 500 } },
  { type: 'DataGridModule' }
]);


function ReportDetail({ reportId, onBack }) {
  const { React, Spinner, Icon, ModuleRegistry, ModuleErrorBoundary, useApi } = window;
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const { request } = useApi();

  React.useEffect(() => {
    setLoading(true);
    request(`/api/report/${reportId}/data`)
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [reportId, request]);

  if (loading) return <div className="usi-app-loading"><Spinner /></div>;
  if (!data) return <div className="usi-app-empty">Błąd ładowania raportu.</div>;

  const { definition, data: investments } = data;
  
  // Resolve modules (supporting presets)
  const modulesToRender = React.useMemo(() => {
    const raw = definition.modules || [{ type: 'DataGridModule' }];
    const resolved = [];
    raw.forEach(m => {
      if (m.type === 'preset') {
        const p = ModuleRegistry.getPreset(m.name);
        if (p) resolved.push(...p);
        else resolved.push({ type: 'error', message: `Nieznany preset: ${m.name}` });
      } else {
        resolved.push(m);
      }
    });
    return resolved;
  }, [definition.modules, ModuleRegistry]);

  return (
    <div data-component="ReportDetail" className="report-detail-content usi-scroll">
        <div className="report-detail-header">
          <div className="report-detail-header-row">
            <button className="usi-btn icon-only" onClick={onBack}><Icon name="arrow" className="icon-rotated-180" /></button>
            <h1 className="usi-h1">{definition.title}</h1>
          </div>
          <div className="usi-body secondary">{investments.length} inwestycji spełnia kryteria</div>
        </div>
        
        <div className="report-modules-stack">
          {modulesToRender.map((mod, idx) => {
             if (mod.type === 'error') return <div key={idx} className="usi-pill error">{mod.message}</div>;

             const { validateModuleSpec } = window;
             const ModComponent = ModuleRegistry.get(mod.type);
             if (!ModComponent) return <div key={idx} className="usi-pill error">Nieznany moduł: {mod.type}</div>;
             
             const val = validateModuleSpec(ModComponent, mod);
             if (!val.valid) {
               return <div key={idx} className="usi-pill error">Błąd konfiguracji {mod.type}: {val.errors.join(', ')}</div>;
             }

             return (
               <ModuleErrorBoundary key={idx}>
                 <ModComponent data={investments} definition={definition} {...(mod.props || {})} modules={mod.modules} />
               </ModuleErrorBoundary>
             );
          })}
        </div>
    </div>
  );
}

Object.assign(window, { ReportsList, ReportDetail });
