// view-reports.jsx — Widok raportów USI

function ReportsList({ onSelectReport, onNav, dark, onToggleTheme }) {
  const [reports, setReports] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  const [navOpen, setNavOpen] = React.useState(false);

  const fetchReports = () => {
    setLoading(true);
    fetch('/api/reports')
      .then(r => r.json())
      .then(data => {
        setReports(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  };

  React.useEffect(() => {
    fetchReports();
  }, []);

  return (
    <div data-component="ReportsList" className="usi-app reports-list-container">
      <div data-component="ReportsList-Toolbar" className="reports-list-toolbar">
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <h1 className="usi-h2" style={{ margin: 0 }}>Raporty USI</h1>
        <div style={{ flex: 1 }} />
        <button data-component="Reports-Refresh" className="usi-btn ghost sm" onClick={fetchReports}>
          <Icon name="sparkle" size={14} /> Odśwież
        </button>
      </div>

      <div data-component="ReportsList-Grid" className="reports-list-content usi-scroll">
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
                <h2 className="usi-h2" style={{ margin: 0 }}>{report.title}</h2>
                <p className="usi-small" style={{ color: 'var(--usi-ink-2)', flex: 1 }}>{report.description}</p>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <button className="usi-btn sm">Otwórz <Icon name="arrow" size={12} /></button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {navOpen && <NavDrawer current="reports" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav && onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
    </div>
  );
}

function ReportDetail({ reportId, onBack, onNav, dark, onToggleTheme }) {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [navOpen, setNavOpen] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);
    fetch(`/api/report/${reportId}/data`)
      .then(r => r.json())
      .then(d => {
        setData(d);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [reportId]);

  if (loading) return (
    <div className="usi-app-loading">
      <Spinner />
    </div>
  );

  if (!data) return <div className="usi-app-empty">Błąd ładowania raportu.</div>;

  const { definition, data: investments } = data;

  return (
    <div data-component="ReportDetail" className="usi-app report-detail-container">
      <div className="report-detail-toolbar">
        <NavMenuButton onClick={() => setNavOpen(true)} />
        <button className="usi-btn ghost sm" onClick={onBack}><Icon name="chevronLeft" /> Powrót</button>
        <div>
          <h1 className="usi-h1" style={{ margin: 0, fontSize: 18 }}>{definition.title}</h1>
          <div className="usi-tiny" style={{ color: 'var(--usi-ink-3)' }}>{investments.length} inwestycji spełnia kryteria</div>
        </div>
        <div style={{ flex: 1 }} />
      </div>

      <div className="report-detail-content usi-scroll">
        <div className="report-modules-stack">
          {definition.modules && definition.modules.map((mod, idx) => (
            <ReportModuleContainer key={idx} module={mod} investments={investments} />
          ))}
        </div>
      </div>

      {navOpen && <NavDrawer current="reports" onClose={() => setNavOpen(false)} onNav={v => { setNavOpen(false); onNav && onNav(v); }} dark={dark} onToggleTheme={onToggleTheme} />}
    </div>
  );
}

function ReportModuleContainer({ module, investments }) {
  const ModuleComponent = ModuleRegistry[module.type] || (() => <div>Nieznany typ modułu: {module.type}</div>);
  
  return (
    <div data-component="ReportModuleContainer" className="usi-card report-module-container">
      <div className="report-module-header">
        <h3 className="usi-h3" style={{ margin: 0, fontSize: 14 }}>{module.title}</h3>
        <div className="usi-tiny" style={{ opacity: 0.5 }}>{module.type.toUpperCase()}</div>
      </div>
      <div className="report-module-content">
        <ModuleComponent config={module.config} investments={investments} />
      </div>
    </div>
  );
}

// ─── Moduły Raportowe ──────────────────────────────────────────

function TableModule({ config, investments }) {
  const columns = config.columns || ['name', 'address', 'price_avg'];
  
  return (
    <div data-component="TableModule" className="table-module-container">
      <table className="table-module-table">
        <thead>
          <tr style={{ borderBottom: '1px solid var(--usi-border)', textAlign: 'left' }}>
            {columns.map(col => <th key={col} className="table-module-th">{col}</th>)}
          </tr>
        </thead>
        <tbody>
          {investments.slice(0, 20).map((inv, idx) => (
            <tr key={idx} style={{ borderBottom: '.5px solid var(--usi-border)' }}>
              {columns.map(col => (
                <td key={col} className="table-module-td">
                  {col === 'price_avg' ? (inv[col] ? `${inv[col].toLocaleString()} zł` : '—') : inv[col]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {investments.length > 20 && <div className="usi-tiny" style={{ marginTop: 8, textAlign: 'center', opacity: 0.5 }}>+ {investments.length - 20} więcej...</div>}
    </div>
  );
}

function MapModule({ config, investments }) {
  const cfg = useConfig();
  const apiKey = cfg?.hereApiKey;
  const withCoords = investments.filter(i => i.coords && i.coords[0] !== 0);
  
  if (!apiKey || withCoords.length === 0) {
    return (
      <div className="map-module-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div className="usi-small" style={{ color: 'var(--usi-ink-4)' }}>
          {!apiKey ? 'Brak klucza API HERE' : 'Brak danych geolokalizacyjnych'}
        </div>
      </div>
    );
  }

  const pts = withCoords.slice(0, 200).map(inv => `${inv.coords[0]},${inv.coords[1]}`).join('|');
  const style = config.dark ? 'lite.night' : 'lite.day';
  const src = `https://image.maps.hereapi.com/mia/v3/base/mc/overlay:padding=32/800x400/png?apiKey=${apiKey}&overlay=point:${pts}|size=small;icon=circle;color=white&style=${style}&features=pois:disabled&lang=pl`;

  return (
    <div className="map-module-container">
      <img src={src} alt="Mapa" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
    </div>
  );
}

function PriceTrendModule({ config, investments }) {
  const canvasRef = React.useRef(null);
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!canvasRef.current || investments.length === 0) return;

    // Grupowanie cen (uproszczone - zestawienie cen z listy)
    const sorted = [...investments]
      .filter(i => i.price_avg > 0)
      .sort((a, b) => a.price_avg - b.price_avg);
    
    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext('2d');
    chartRef.current = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: sorted.map(i => i.name),
        datasets: [{
          label: 'Cena za m²',
          data: sorted.map(i => i.price_avg),
          backgroundColor: 'rgba(229, 0, 109, 0.6)',
          borderColor: 'rgba(229, 0, 109, 1)',
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: {
            beginAtZero: false,
            title: { display: true, text: 'zł / m²' }
          },
          x: {
            ticks: { display: false } // Za dużo nazw, ukrywamy
          }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [investments]);

  return (
    <div className="chart-module-container">
      <canvas ref={canvasRef}></canvas>
    </div>
  );
}

function RatingComparisonModule({ config, investments }) {
  const canvasRef = React.useRef(null);
  const chartRef = React.useRef(null);

  React.useEffect(() => {
    if (!canvasRef.current || investments.length === 0) return;

    const data = investments
      .filter(i => avgRating(i) > 0)
      .map(i => ({
        x: avgRating(i),
        y: i.price_avg,
        name: i.name
      }))
      .filter(i => i.y > 0);
    
    if (chartRef.current) chartRef.current.destroy();

    const ctx = canvasRef.current.getContext('2d');
    chartRef.current = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Inwestycje',
          data: data,
          backgroundColor: 'rgba(31, 28, 22, 0.6)',
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (ctx) => `${ctx.raw.name}: ${ctx.raw.x.toFixed(2)} ★, ${ctx.raw.y.toLocaleString()} zł/m²`
            }
          }
        },
        scales: {
          x: { title: { display: true, text: 'Średnia Ocena' }, min: 0, max: 4 },
          y: { title: { display: true, text: 'Cena za m²' } }
        }
      }
    });

    return () => {
      if (chartRef.current) chartRef.current.destroy();
    };
  }, [investments]);

  return (
    <div className="chart-module-container">
      <canvas ref={canvasRef}></canvas>
    </div>
  );
}

const ModuleRegistry = {
  'map': MapModule,
  'table': TableModule,
  'price-trend': PriceTrendModule,
  'rating-comparison': RatingComparisonModule
};

Object.assign(window, { ReportsList, ReportDetail });
