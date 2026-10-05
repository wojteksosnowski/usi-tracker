// view-report-location.jsx — Raport lokalizacyjny: inwestycje w zasięgu od punktu

const LOC_STORE_KEY = 'usi.report.location.v2';
const LOC_LIMITS = [12, 16, 24];

function _locLoad() {
  try { return JSON.parse(localStorage.getItem(LOC_STORE_KEY)) || {}; } catch (e) { return {}; }
}
function _locSave(state) {
  try { localStorage.setItem(LOC_STORE_KEY, JSON.stringify(state)); } catch (e) { /* brak storage */ }
}

// Zakres lat -> token backendu; brak obu granic = brak filtra
function _yearToken(from, to) {
  if (from && to) return `${from}-${to}`;
  if (from) return `${from}+`;
  if (to) return `1900-${to}`;
  return null;
}

// Pobiera PDF raportu (te same parametry co widok) i zapisuje go jako plik
async function downloadLocationPdf(params) {
  const r = await fetch('/api/reports/location/pdf', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!r.ok) {
    let msg = 'Nie udało się wygenerować PDF';
    try { msg = (await r.json()).error || msg; } catch (e) { /* odpowiedź nie-JSON */ }
    throw new Error(msg);
  }
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement('a');
  a.href = url;
  a.download = 'raport-lokalizacji.pdf';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

function LocationReport({ onSelectInv }) {
  const { React, Icon, Spinner, DataGrid, SourceBadge, MapModule, ListCard } = window;
  const saved = React.useMemo(_locLoad, []);
  const [input, setInput] = React.useState(saved.input || '');
  const [limit, setLimit] = React.useState(saved.limit || 12);
  const [yearFrom, setYearFrom] = React.useState('');
  const [yearTo, setYearTo] = React.useState('');
  const [query, setQuery] = React.useState(saved.input || null); // zatwierdzona lokalizacja
  const [result, setResult] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [sort, setSort] = React.useState({ key: 'distance', dir: 'asc' });
  const { bus, setVariable } = window.useDataBus();
  const mode = bus.reportMode || (saved.mode === 'table' ? 'table' : 'grid');
  const years = (result && result.years) || [];
  const yearToken = _yearToken(yearFrom, yearTo);
  const tokens = React.useMemo(() => (yearToken ? [yearToken] : []), [yearToken]);

  React.useEffect(() => { _locSave({ input: query || input, limit, mode }); }, [query, limit, mode]);

  // Parametry bieżącego widoku dla przycisku „Generuj PDF” w ActionBar
  React.useEffect(() => {
    setVariable('reportPdf', result && !loading && query
      ? { location: query, limit, delivery: tokens, sort }
      : null);
  }, [result, loading, query, limit, tokens, sort]);
  React.useEffect(() => () => setVariable('reportPdf', null), []);

  React.useEffect(() => {
    if (!query) return;
    let cancelled = false;
    setLoading(true);
    setError('');
    fetch('/api/reports/location', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ location: query, limit, delivery: tokens }),
    })
      .then(r => r.json().then(j => ({ ok: r.ok, j })))
      .then(({ ok, j }) => {
        if (cancelled) return;
        if (!ok) { setError(j.error || 'Błąd zapytania'); setResult(null); }
        else setResult(j);
        setLoading(false);
      })
      .catch(() => { if (!cancelled) { setError('Brak połączenia z serwerem'); setLoading(false); } });
    return () => { cancelled = true; };
  }, [query, limit, tokens]);

  // Wybrany rok spoza lat występujących w nowym obszarze nie ma sensu — wyczyść
  React.useEffect(() => {
    if (!result) return;
    if (yearFrom && !result.years.includes(Number(yearFrom))) setYearFrom('');
    if (yearTo && !result.years.includes(Number(yearTo))) setYearTo('');
  }, [result]);

  const changeFrom = (v) => {
    setYearFrom(v);
    if (v && yearTo && Number(v) > Number(yearTo)) setYearTo(v);
  };
  const changeTo = (v) => {
    setYearTo(v);
    if (v && yearFrom && Number(v) < Number(yearFrom)) setYearFrom(v);
  };

  const submit = (e) => {
    e.preventDefault();
    if (input.trim()) setQuery(input.trim());
  };

  const rows = React.useMemo(() => {
    const data = result ? [...result.data] : [];
    const { key, dir } = sort;
    data.sort((a, b) => {
      const va = a[key] ?? '', vb = b[key] ?? '';
      if (va < vb) return dir === 'asc' ? -1 : 1;
      if (va > vb) return dir === 'asc' ? 1 : -1;
      return 0;
    });
    return data;
  }, [result, sort]);

  const handleSort = (key) =>
    setSort(prev => ({ key, dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc' }));

  const columns = [
    { key: 'name', label: 'Inwestycja', sortable: true,
      render: (val, row) => (
        <div className="datagrid-cell-name">
          <SourceBadge source={row.source} />
          <span className="usi-weight-600">{val}</span>
        </div>
      ) },
    { key: 'developer', label: 'Deweloper', sortable: true },
    { key: 'district', label: 'Dzielnica', sortable: true },
    { key: 'delivery', label: 'Oddanie', sortable: true, render: (val) => val || '—' },
    { key: 'distance', label: 'Odległość', sortable: true, render: (val) => `${val} km` },
    { key: 'price_m2_min', label: 'Cena m² od', sortable: true,
      render: (val) => val ? `${Math.round(val).toLocaleString('pl-PL')} zł` : '—' },
    { key: 'status', label: 'Status', sortable: true },
  ];

  return (
    <div data-component="LocationReport" className="report-detail-content usi-scroll">
      <div className="report-detail-header">
        {result && (
          <div className="usi-body secondary">
            Pokazano {result.count} z {result.total} inwestycji w zasięgu {result.area_km} km{result.count < result.total ? ' (filtr terminu oddania)' : ''}
            {result.center.label ? ` od: ${result.center.label}` : ` od ${result.center.lat.toFixed(5)}, ${result.center.lon.toFixed(5)}`}
          </div>
        )}
      </div>

      <div className="loc-report-layout">
       <div className="loc-report-side">
        <form className="usi-card loc-report-controls" onSubmit={submit}>
          <label className="usi-small usi-weight-600" htmlFor="loc-input">Lokalizacja</label>
          <div className="loc-report-input-row">
            <input id="loc-input" className="usi-input loc-report-input" value={input}
              placeholder="Wklej link z Map Google, adres lub współrzędne"
              onChange={e => setInput(e.target.value)} />
            <button type="submit" className="usi-btn primary" disabled={!input.trim() || loading}>Ustaw</button>
          </div>
          {error && <div className="usi-pill error">{error}</div>}

          <div className="loc-report-group">
            <span className="usi-small usi-weight-600">Limit inwestycji</span>
            <div className="loc-report-chips">
              {LOC_LIMITS.map(n => (
                <button key={n} type="button" aria-pressed={limit === n}
                  className={`usi-btn sm${limit === n ? ' primary' : ''}`}
                  onClick={() => setLimit(n)}>{n}</button>
              ))}
            </div>
          </div>

          <div className="loc-report-group">
            <span className="usi-small usi-weight-600">Termin oddania (lata)</span>
            <div className="loc-report-chips">
              <label className="usi-small" htmlFor="loc-year-from">Od</label>
              <select id="loc-year-from" className="usi-input loc-report-select" value={yearFrom}
                onChange={e => changeFrom(e.target.value)}>
                <option value="">dowolny</option>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
              <label className="usi-small" htmlFor="loc-year-to">Do</label>
              <select id="loc-year-to" className="usi-input loc-report-select" value={yearTo}
                onChange={e => changeTo(e.target.value)}>
                <option value="">dowolny</option>
                {years.map(y => <option key={y} value={y}>{y}</option>)}
              </select>
              {(yearFrom || yearTo) && (
                <button type="button" className="usi-btn sm ghost"
                  onClick={() => { setYearFrom(''); setYearTo(''); }}>Wyczyść</button>
              )}
            </div>
            <span className="usi-tiny secondary">
              {yearToken ? 'Pokazane tylko inwestycje z terminem w wybranym zakresie.' : 'Bez filtra: wszystkie terminy, także bez daty.'}
            </span>
          </div>
        </form>

        {loading && <div className="usi-app-loading"><Spinner /></div>}

        {result && !loading && (
          <MapModule instanceId="loc_report_map" title="Mapa zasięgu" height={320}
            data={result.data} center={result.center} radiusKm={result.area_km}
            onMarkerSelect={(inv) => onSelectInv(inv, rows)} />
        )}
       </div>

       <div className="loc-report-main">
        {!query && <div className="usi-app-empty">Wklej lokalizację, aby zobaczyć inwestycje w zasięgu.</div>}
        {result && !loading && (
          <div className="usi-card datagrid-module-container">
            <DataGrid data={rows} columns={columns} mode={mode}
              gridConfig={{ minCardWidth: 280, cardHeight: 340, gap: 16 }}
              renderCard={(inv) => <ListCard inv={inv} onSelect={() => onSelectInv(inv, rows)} />}
              sortKey={sort.key} sortDir={sort.dir} onSort={handleSort}
              onRowClick={(inv) => onSelectInv(inv, rows)}
              emptyMessage="Brak inwestycji w zasięgu dla wybranych filtrów" />
          </div>
        )}
       </div>
      </div>
    </div>
  );
}

Object.assign(window, { LocationReport, downloadLocationPdf });
