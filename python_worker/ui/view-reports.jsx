// view-reports.jsx — Widok raportów USI

function ReportsList({ onSelectReport }) {
  const { React, Spinner, Icon } = window;
  const [reports, setReports] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

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
    <div data-component="ReportsList" className="reports-list-content usi-scroll" style={{ height: '100%', overflowY: 'auto', padding: '24px' }}>
        {loading ? (
          <div className="usi-app-loading" style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner /></div>
        ) : reports.length === 0 ? (
          <div className="usi-app-empty" style={{ textAlign: 'center', padding: 40 }}>Brak definicji raportów w Public/USIdata/reports/</div>
        ) : (
          <div className="reports-grid-layout" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '20px' }}>
            {reports.map(report => (
              <div key={report.id} 
                data-component="ReportCard"
                className="usi-card report-card" 
                style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: 12, cursor: 'pointer' }}
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
  );
}

function ReportDetail({ reportId, onBack }) {
  const { React, Spinner, Icon } = window;
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(true);

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

  if (loading) return <div className="usi-app-loading" style={{ display: 'flex', justifyContent: 'center', padding: 40 }}><Spinner /></div>;
  if (!data) return <div className="usi-app-empty" style={{ padding: 40 }}>Błąd ładowania raportu.</div>;

  const { definition, data: investments } = data;

  return (
    <div data-component="ReportDetail" className="report-detail-content usi-scroll" style={{ height: '100%', overflowY: 'auto', padding: '24px' }}>
        <div style={{ marginBottom: 24 }}>
          <h1 className="usi-h1" style={{ margin: 0, fontSize: 24 }}>{definition.title}</h1>
          <div className="usi-body" style={{ color: 'var(--usi-ink-3)', marginTop: 4 }}>{investments.length} inwestycji spełnia kryteria</div>
        </div>
        
        {/* Tu można wstawić moduły raportowe */}
        <div className="usi-card" style={{ padding: '20px' }}>
            <div className="usi-small">Tabela wyników raportu zostanie wyświetlona tutaj.</div>
        </div>
    </div>
  );
}

Object.assign(window, { ReportsList, ReportDetail });
