// ---------- Komponenty pomocnicze (poziom modułu: stabilna tożsamość, brak remountów przy każdym renderze) ----------
const isJobActive = (j) => !!j && (j.status === 'running' || j.status === 'queued');

function ItemBadge({ item, fallbackNew }) {
  if (item) {
    const cls = item.status === 'saved' ? 'success' : (item.status === 'failed' || item.status === 'save_failed') ? 'danger' : 'info';
    return <span className={`usi-pill ${cls}`} title={item.error || item.message || ''}>{item.label}</span>;
  }
  return <span className={`usi-pill ${fallbackNew ? 'success outline' : 'outline'}`}>{fallbackNew ? 'nowa' : 'w bazie'}</span>;
}

function JobPanel({ job, detail, activeJob }) {
  const React = window.React;
  const j = detail || job;
  const counts = j.counts || {};
  const active = isJobActive(job);
  const failed = job.status === 'failed';
  const percent = Math.max(0, Math.min(100, Math.round(((j.progress || 0) / (j.total || 100)) * 100)));
  const phaseLabel = { scan: 'skanowanie', fetch: 'pobieranie', save: 'zapis', done: 'zakończono' }[j.phase] || (active ? 'w toku' : '');
  const statusLabel = { queued: 'w kolejce', running: 'w toku', completed: 'zakończone', failed: 'błąd' }[job.status] || job.status;
  const log = (detail && detail.log) || [];
  const items = (detail && detail.items) || [];
  const failedItems = items.filter(it => it.status === 'failed' || it.status === 'save_failed');
  const logRef = React.useRef(null);
  React.useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [log.length]);

  return (
    <div className="usi-flex-col usi-gap-12">
      <div className="usi-flex-row usi-gap-12" style={{ alignItems: 'center' }}>
        <span className={`usi-dot ${active ? 'active' : (failed ? 'bad' : '')}`} />
        <h2 className="usi-h2 usi-flex-1" style={{ margin: 0 }}>{job.name}</h2>
        <span className={`usi-pill ${failed ? 'danger' : (active ? 'info' : 'success')}`}>{statusLabel}{phaseLabel && active ? ` · ${phaseLabel}` : ''}</span>
      </div>
      <div className={`usi-dl-bar ${failed ? 'failed' : ''}`}><div style={{ width: `${percent}%` }} /></div>
      <div className="usi-flex-row usi-gap-16 usi-tiny usi-text-secondary" style={{ flexWrap: 'wrap' }}>
        <span>{percent}%</span>
        {counts.downloaded > 0 && <span>pobrano: {counts.downloaded}</span>}
        {counts.saved > 0 && <span className="usi-text-success">zapisano: {counts.saved}</span>}
        {counts.retrying > 0 && <span>ponowienia: {counts.retrying}</span>}
        {counts.failed > 0 && <span style={{ color: 'var(--usi-danger)' }}>błędy: {counts.failed}</span>}
        {job.status === 'queued' && activeJob && activeJob.id !== job.id && <span>czeka za: {activeJob.name}</span>}
      </div>
      <div className="usi-body">{j.message}</div>
      {active && j.current && <div className="usi-tiny usi-mono usi-text-secondary usi-dl-ellipsis">▸ {j.current}</div>}
      {failed && job.error && <div className="usi-pill danger">{job.error}</div>}
      {failedItems.length > 0 && (
        <div className="usi-flex-col usi-gap-8">
          {failedItems.slice(0, 10).map((it, i) => (
            <div key={i} className="usi-tiny" style={{ color: 'var(--usi-danger)' }}>
              ✕ {it.ref}: {it.error || it.message}
            </div>
          ))}
        </div>
      )}
      {log.length > 0 && (
        <div className="usi-dl-log usi-mono" ref={logRef}>
          {log.slice(-80).map(l => (
            <div key={l.seq} className={l.level === 'error' ? 'err' : ''}>{l.ts} {l.text}</div>
          ))}
        </div>
      )}
    </div>
  );
}

function RecentJobs({ jobs, shownId, onPick }) {
  const recent = jobs.slice(0, 8);
  if (recent.length <= 1) return null;
  return (
    <div className="usi-dl-recent">
      {recent.map(j => (
        <button
          key={j.id}
          className={`usi-pill ${j.status === 'failed' ? 'danger' : (isJobActive(j) ? 'info' : 'success')} ${j.id === shownId ? '' : 'outline'}`}
          onClick={() => onPick(j.id)}
          title={j.message || ''}
        >
          {j.name}
        </button>
      ))}
    </div>
  );
}

window.usiRegister('ViewDownload', function ViewDownload() {
  const {
    React, Icon, Spinner, useDataBus, useApi
  } = window;

  const { bus, setVariable, refetch } = useDataBus();
  const { download = {} } = bus;
  const { request } = useApi();
  const activePortals = Array.from(download.activePortals || ['rp']);
  const identifier = download.search || '';
  const onlyNew = !!download.onlyNew;

  // Stan skanu/pobierania żyje w busie (nie w komponencie), więc przełączenie widoku nie gubi pollingu.
  const results = download.results || [];
  const scanJobs = download.scanJobs || [];       // [{ portal, jobId, state: 'pending'|'done'|'failed', count, error }]
  const bulkJobIds = download.bulkJobIds || [];
  const allJobs = bus.allJobs || [];

  const resultsRef = React.useRef(results);
  const scanJobsRef = React.useRef(scanJobs);
  resultsRef.current = results;
  scanJobsRef.current = scanJobs;
  const collecting = React.useRef(new Set());

  const setResults = (arr) => { resultsRef.current = arr; setVariable('download.results', arr); };
  const setScanJobs = (arr) => { scanJobsRef.current = arr; setVariable('download.scanJobs', arr); };

  const setBulkJobsSafe = (ids) => setVariable('download.bulkJobIds', ids);
  const jobById = (id) => allJobs.find(j => j.id === id);
  const isActive = isJobActive;

  // ---- Zbieranie wyników zakończonych skanów ----
  React.useEffect(() => {
    scanJobs.filter(s => s.state === 'pending').forEach(s => {
      const job = jobById(s.jobId);
      if (!job) return;
      if (job.status === 'failed') {
        setScanJobs(scanJobsRef.current.map(x => x.jobId === s.jobId ? { ...x, state: 'failed', error: job.error || job.message || 'Zadanie nie powiodło się' } : x));
      } else if (job.status === 'completed' && !collecting.current.has(s.jobId)) {
        collecting.current.add(s.jobId);
        request(`/api/jobs/${s.jobId}`, { noCache: true }).then(full => {
          const found = Array.isArray(full.result) ? full.result.map(r => ({ ...r, source: s.portal })) : [];
          setResults([...resultsRef.current, ...found]);
          setScanJobs(scanJobsRef.current.map(x => x.jobId === s.jobId ? { ...x, state: 'done', count: found.length } : x));
        }).catch(e => {
          setScanJobs(scanJobsRef.current.map(x => x.jobId === s.jobId ? { ...x, state: 'failed', error: String(e.message || e) } : x));
        });
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allJobs, scanJobs]);

  const scanning = scanJobs.some(s => s.state === 'pending');

  // ---- Wybór zadania do podglądu: aktywne, w przeciwnym razie ostatnio śledzone ----
  const trackedIds = [...scanJobs.map(s => s.jobId), ...bulkJobIds];
  const activeJob = allJobs.find(isActive);
  const lastTracked = trackedIds.length ? jobById(trackedIds[trackedIds.length - 1]) : null;
  const [pinnedId, setPinnedId] = React.useState(null);
  const shownJob = (pinnedId && jobById(pinnedId)) || activeJob || lastTracked || null;

  const detailIds = Array.from(new Set([...bulkJobIds, shownJob && shownJob.id].filter(Boolean)));
  const anyActive = detailIds.some(id => isActive(jobById(id)));
  const details = useJobDetails(detailIds, anyActive);
  const shownDetail = shownJob ? details[shownJob.id] : null;

  // Status poszczególnych pozycji z zadań pobierania (po url / id)
  const statusByRef = {};
  bulkJobIds.forEach(id => {
    const d = details[id];
    if (d && d.items) d.items.forEach(it => { if (it.ref) statusByRef[String(it.ref)] = it; });
  });
  const bulkCounts = bulkJobIds.reduce((acc, id) => {
    const c = (jobById(id) && jobById(id).counts) || (details[id] && details[id].counts) || {};
    acc.saved += c.saved || 0; acc.failed += c.failed || 0; acc.downloaded += c.downloaded || 0;
    return acc;
  }, { saved: 0, failed: 0, downloaded: 0 });

  const itemStatus = (r) => {
    const it = statusByRef[String(r.url)] || statusByRef[String(r.id)];
    if (it) return it;
    if (r.queued) return { status: 'queued', label: 'w kolejce' };
    return null;
  };

  // Stats
  const totalFound = results.length;
  const newCount = results.filter(r => r.is_new && !r.registered && !r.queued).length;

  const handleGlobalScan = React.useCallback(async (pages = null) => {
    setResults([]);
    collecting.current = new Set();
    setBulkJobsSafe([]);
    const pagesLabel = pages && pages !== 'all' ? ` (limit: ${pages} stron)` : ' (pełne)';
    setVariable('appStatus', { type: 'info', msg: `Rozpoczęto skanowanie portali${pagesLabel} w tle...` });

    const started = [];
    for (const p of activePortals) {
      try {
        let url = `/api/discovery/${p}/job?id=${encodeURIComponent(identifier)}`;
        if (pages && pages !== 'all') url += `&pages=${pages}`;
        const jobStart = await request(url, { method: 'POST' });
        if (!jobStart.job_id) throw new Error('Nie udało się uruchomić zadania discovery');
        started.push({ portal: p, jobId: jobStart.job_id, state: 'pending' });
      } catch (e) {
        started.push({ portal: p, jobId: null, state: 'failed', error: String(e.message || e) });
      }
    }
    setScanJobs(started);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activePortals.join(','), request, setVariable, identifier]);

  // Expose triggers
  React.useEffect(() => {
    window.usiTriggerScan = handleGlobalScan;
    return () => {
      delete window.usiTriggerScan;
    };
  }, [handleGlobalScan]);

  const handleRegisterAll = async () => {
    const newOnes = results.filter(r => r.is_new && !r.registered && !r.queued);
    if (newOnes.length === 0) return;

    // Group by source (portal) as our API handles one portal at a time per batch
    const bySource = newOnes.reduce((acc, r) => {
      acc[r.source] = acc[r.source] || [];
      acc[r.source].push(r);
      return acc;
    }, {});

    setVariable('appStatus', { type: 'info', msg: `Uruchamianie pobierania zbiorczego dla ${newOnes.length} inwestycji...` });

    const jobIds = [];
    const queuedSources = new Set();
    for (const source in bySource) {
      try {
        const data = await request('/api/register-bulk', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ portal: source, investments: bySource[source] })
        });
        if (data && data.ok && data.job_id) { jobIds.push(data.job_id); queuedSources.add(source); }
      } catch (e) {
        setVariable('appStatus', { type: 'error', msg: `Nie udało się zlecić pobierania (${source}): ${e.message || e}` });
      }
    }

    if (jobIds.length > 0) {
      setBulkJobsSafe([...bulkJobIds, ...jobIds]);
      setResults(resultsRef.current.map(r => (r.is_new && !r.registered && queuedSources.has(r.source)) ? { ...r, queued: true } : r));
      setPinnedId(null);
      setVariable('appStatus', { type: 'success', msg: `Zlecono pobranie ${newOnes.length} inwestycji w ${jobIds.length} zadaniach zbiorczych.` });
    }
  };

  const visibleRows = (onlyNew ? results.filter(r => r.is_new) : results).slice(0, 300);
  const failedScans = scanJobs.filter(s => s.state === 'failed');

  return (
    <div data-component="ViewDownload" className="usi-scroll usi-h-full usi-overflow-auto usi-p-24">
     <div className="usi-dl-grid">
     <div className="usi-dl-col">

      {/* 1. Skanowanie manualne (Quick Stats) */}
      <section className="usi-card usi-p-24">
        <div className="usi-flex-row usi-gap-16" style={{ alignItems: 'center' }}>
          <div className="usi-flex-1">
            <h2 className="usi-h2" style={{ marginBottom: 4 }}>Skanowanie manualne</h2>
            <p className="usi-body usi-text-secondary">Wyszukaj i zarejestruj nowe inwestycje z wybranych portali.</p>
          </div>
          <div className="usi-flex-row usi-gap-12">
            <div className="usi-stat-box">
              <div className="usi-tiny usi-text-secondary">Zeskanowano</div>
              <div className="usi-h2">{scanning ? <Spinner size={16} /> : totalFound}</div>
            </div>
            <div className="usi-stat-box">
              <div className="usi-tiny usi-text-secondary">Nowe</div>
              <div className="usi-h2 usi-text-success">{scanning ? <Spinner size={16} /> : newCount}</div>
            </div>
            {bulkJobIds.length > 0 && (
              <>
                <div className="usi-stat-box">
                  <div className="usi-tiny usi-text-secondary">Zapisano</div>
                  <div className="usi-h2 usi-text-success">{bulkCounts.saved}</div>
                </div>
                <div className="usi-stat-box">
                  <div className="usi-tiny usi-text-secondary">Błędy</div>
                  <div className="usi-h2" style={{ color: bulkCounts.failed ? 'var(--usi-danger)' : undefined }}>{bulkCounts.failed}</div>
                </div>
              </>
            )}
          </div>
        </div>

        {newCount > 0 && (
          <div className="usi-m-t-24 usi-p-16 usi-surface-2 usi-round-12 usi-flex-row usi-gap-16" style={{ alignItems: 'center' }}>
            <Icon name="sparkle" className="usi-text-accent" />
            <div className="usi-flex-1">
              <div className="usi-weight-600">Znaleziono {newCount} nowych inwestycji</div>
              <div className="usi-tiny usi-text-secondary">Możesz je teraz dodać do bazy jednym kliknięciem.</div>
            </div>
            <button className="usi-btn" onClick={handleRegisterAll}>
              Pobierz wszystko
            </button>
          </div>
        )}

        {failedScans.map((s, i) => (
          <div key={i} className="usi-pill danger usi-m-t-16">Skan {String(s.portal).toUpperCase()} nieudany: {s.error}</div>
        ))}
        {!scanning && scanJobs.length > 0 && failedScans.length === 0 && totalFound === 0 && (
          <div className="usi-pill info usi-m-t-16">Nie znaleziono inwestycji na wybranych portalach.</div>
        )}
      </section>

      {/* 2. Bieżące zadanie */}
      {shownJob && (
        <section className="usi-card usi-p-24" data-component="DownloadJobPanel">
          <JobPanel job={shownJob} detail={shownDetail} activeJob={activeJob} />
          <RecentJobs jobs={allJobs} shownId={shownJob.id} onPick={setPinnedId} />
        </section>
      )}

      </div>
      <div className="usi-dl-col">

      {/* 3. Serwery / Fetcher */}
      <FetcherPanel />

      {/* 4. Wyniki */}
      {results.length > 0 && (
        <section className="usi-card usi-p-24">
          <h2 className="usi-h2" style={{ marginBottom: 12 }}>Wyniki ({visibleRows.length}{results.length > visibleRows.length ? ` z ${results.length}` : ''})</h2>
          <div className="usi-dl-rows">
            {visibleRows.map((r, i) => {
              const st = itemStatus(r);
              return (
                <div key={`${r.source}-${r.id || r.url || i}`} className="usi-dl-row">
                  <span className="usi-pill outline">{String(r.source).toUpperCase()}</span>
                  <div className="usi-flex-1" style={{ minWidth: 0 }}>
                    <div className="usi-weight-600 usi-dl-ellipsis">{r.name || r.title || r.url || r.id}</div>
                    <div className="usi-tiny usi-text-secondary usi-dl-ellipsis">{r.developer_name || r.developer || ''}</div>
                  </div>
                  <ItemBadge item={st} fallbackNew={r.is_new} />
                </div>
              );
            })}
          </div>
        </section>
      )}

      </div>
      </div>

      <style>{`
        .usi-dl-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; align-items: start; }
        .usi-dl-col { display: flex; flex-direction: column; gap: 24px; min-width: 0; }
        @media (max-width: 1000px) { .usi-dl-grid { grid-template-columns: minmax(0, 1fr); } }
        .usi-stat-box {
          padding: 12px 20px;
          background: var(--usi-surface-2);
          border-radius: 12px;
          min-width: 120px;
          text-align: center;
        }
        .usi-m-t-16 { margin-top: 16px !important; }
        .usi-m-t-24 { margin-top: 24px !important; }
        .usi-dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--usi-ink-3);
          display: inline-block;
        }
        .usi-dot.active {
          background: var(--usi-success);
          box-shadow: 0 0 8px var(--usi-success);
          animation: usi-pulse 2s infinite;
        }
        .usi-dot.bad { background: var(--usi-danger); }
        @keyframes usi-pulse {
          0% { opacity: 1; }
          50% { opacity: 0.4; }
          100% { opacity: 1; }
        }
        .usi-dl-bar { height: 8px; background: var(--usi-surface-2); border-radius: 4px; overflow: hidden; }
        .usi-dl-bar > div { height: 100%; background: var(--usi-success); transition: width .4s; }
        .usi-dl-bar.failed > div { background: var(--usi-danger); }
        .usi-dl-log {
          max-height: 220px; overflow: auto; background: var(--usi-surface-2);
          border-radius: 8px; padding: 10px 12px; font-size: 12px; line-height: 1.5;
        }
        .usi-dl-log .err { color: var(--usi-danger); }
        .usi-dl-rows { display: flex; flex-direction: column; gap: 8px; max-height: 480px; overflow: auto; }
        .usi-dl-row { display: flex; gap: 12px; align-items: center; padding: 8px 12px; background: var(--usi-surface-2); border-radius: 10px; }
        .usi-dl-ellipsis { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .usi-dl-table { width: 100%; border-collapse: collapse; font-size: 13px; }
        .usi-dl-table th, .usi-dl-table td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--usi-surface-2); }
        .usi-dl-recent { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
        .usi-dl-recent button { cursor: pointer; }
      `}</style>
    </div>
  );
});

// Odpytuje szczegóły (log, elementy) wskazanych zadań; przestaje, gdy żadne nie jest aktywne.
function useJobDetails(ids, keepPolling) {
  const React = window.React;
  const [details, setDetails] = React.useState({});
  const key = ids.join(',');
  React.useEffect(() => {
    if (!ids.length) return undefined;
    let stop = false;
    const load = () => Promise.all(ids.map(id =>
      fetch(`/api/jobs/${id}`, { cache: 'no-store' }).then(r => (r.ok ? r.json() : null)).catch(() => null)
    )).then(list => {
      if (stop) return;
      setDetails(prev => {
        const next = { ...prev };
        list.forEach(d => { if (d) next[d.id] = d; });
        return next;
      });
    });
    load();
    const t = keepPolling ? setInterval(load, 1500) : null;
    return () => { stop = true; if (t) clearInterval(t); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, keepPolling]);
  return details;
}

// Stan Fetchera (cooldowny, wyłączniki 403/429, liczniki) — odczyt z pamięci serwera, bez żądań do portali.
function FetcherPanel() {
  const React = window.React;
  const [snap, setSnap] = React.useState(null);
  React.useEffect(() => {
    let stop = false;
    const load = () => fetch('/api/fetcher/status', { cache: 'no-store' })
      .then(r => r.json()).then(d => { if (!stop) setSnap(d); }).catch(() => {});
    load();
    const t = setInterval(load, 3000);
    return () => { stop = true; clearInterval(t); };
  }, []);

  const domains = snap && snap.domains ? Object.entries(snap.domains) : [];
  return (
    <section className="usi-card usi-p-24" data-component="FetcherPanel">
      <h2 className="usi-h2" style={{ marginBottom: 4 }}>Serwery</h2>
      <p className="usi-tiny usi-text-secondary" style={{ marginBottom: 12 }}>
        Stan połączeń z portalami od startu aplikacji. Po 3 kolejnych odmowach (403/429) pobieranie z domeny jest wstrzymywane.
        {snap && snap.scraperapi_credits_cached != null ? ` Kredyty ScraperAPI: ${snap.scraperapi_credits_cached}.` : ''}
      </p>
      {domains.length === 0 ? (
        <div className="usi-tiny usi-text-secondary">Brak żądań w tej sesji.</div>
      ) : (
        <table className="usi-dl-table">
          <thead>
            <tr><th>Domena</th><th>OK</th><th>Błędy</th><th>ScraperAPI</th><th>Kody HTTP</th><th>Stan</th></tr>
          </thead>
          <tbody>
            {domains.map(([domain, d]) => (
              <tr key={domain}>
                <td className="usi-mono">{domain}</td>
                <td>{d.direct_ok}</td>
                <td style={{ color: d.direct_fail ? 'var(--usi-danger)' : undefined }}>{d.direct_fail}</td>
                <td>{d.scraperapi}</td>
                <td className="usi-mono">{Object.entries(d.status || {}).map(([k, v]) => `${k}×${v}`).join(' ') || '–'}</td>
                <td>
                  {d.breaker_open
                    ? <span className="usi-pill danger">wstrzymane · {d.breaker_remaining_s}s</span>
                    : d.cooldown_remaining_s > 0
                      ? <span className="usi-pill info">przerwa · {d.cooldown_remaining_s}s</span>
                      : <span className="usi-pill success">ok</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
