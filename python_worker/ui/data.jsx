// data.jsx — async hook for loading investments from server

// Defined at top level but safely using window.React
const DataBusContext = window.React.createContext();

function DataBusProvider({ children }) {
  const { React } = window;
  const [bus, setBus] = React.useState({
    visibleInvestments: [],
    currentInvestment: null,
    nearbyInvestments: [],
    reports: [],
    activeJobs: [],
    appStatus: null // { msg: string, type: 'success'|'error'|'info' }
  });

  const setVariable = React.useCallback((name, value) => {
    setBus(prev => {
      // Avoid unnecessary state updates if value is strictly equal
      if (prev[name] === value) return prev;
      return { ...prev, [name]: value };
    });
  }, []);

  const getVariable = React.useCallback((name) => bus[name], [bus]);

  const value = React.useMemo(() => ({ bus, setVariable, getVariable }), [bus, setVariable, getVariable]);

  return (
    <DataBusContext.Provider value={value}>
      {children}
    </DataBusContext.Provider>
  );
}

function useDataBus() {
  const { React } = window;
  const context = React.useContext(DataBusContext);
  if (!context) {
    // Fallback for components rendered outside provider (e.g. during initial loads)
    return { bus: {}, setVariable: () => {}, getVariable: () => {} };
  }
  return context;
}

function useInvestments() {
  const { React } = window;
// ... existing useInvestments ...
  const [investments, setInvestments] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  // ...

  const load = React.useCallback(() => {
    setLoading(true);
    fetch('/api/investments')
      .then(r => r.json())
      .then(data => { setInvestments(Array.isArray(data) ? data : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  React.useEffect(() => { load(); }, [load]);

  return { investments, loading, refetch: load };
}

function useDevelopers() {
  const { React } = window;
  const [developers, setDevelopers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);
  // ...

  const load = React.useCallback(() => {
    setLoading(true);
    fetch('/api/developers')
      .then(r => r.json())
      .then(data => { setDevelopers(Array.isArray(data) ? data : []); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  React.useEffect(() => { load(); }, [load]);

  return { developers, loading, refetch: load };
}

function useConfig() {
  const { React } = window;
  const [config, setConfig] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => setConfig(data))
      .catch(e => {
        console.error("Failed to load config", e);
        setConfig({});
      });
  }, [React]);
  return config;
}

function useMetadataConfig() {
  const { React } = window;
  const [meta, setMeta] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/metadata-config')
      .then(r => r.json())
      .then(data => setMeta(data))
      .catch(e => {
        console.error("Failed to load metadata config", e);
        setMeta([]);
      });
  }, [React]);
  return meta;
}

const _CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];

const ratedCount = (inv) =>
  _CATS.filter(k => ((inv.ratings || {})[k] ?? null) !== null).length;

const avgRating = (inv) => {
  const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
};

const ratingStatus = (inv) => {
  const c = ratedCount(inv);
  if (c === 0) return 'none';
  if (c < 6) return 'partial';
  return 'done';
};

const ocenaLog = (inv) => {
  const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
  if (vals.length === 0) return null;
  const sum = vals.reduce((acc, v) => acc + Math.exp(v), 0);
  return Math.log(sum) - Math.log(vals.length);
};

// ─── Ekstraktory Danych dla Modułów (Krok B05) ─────────────────
const extractModuleContext = {
  sumApartments: (records) => {
    if (!Array.isArray(records)) return 0;
    return records.reduce((sum, inv) => sum + (parseInt(inv.flats_count) || parseInt(inv.units_count) || 0), 0);
  },
  avgListRating: (records) => {
    if (!Array.isArray(records) || records.length === 0) return 0;
    const rated = records.filter(inv => ratedCount(inv) > 0);
    if (rated.length === 0) return 0;
    return rated.reduce((sum, inv) => sum + avgRating(inv), 0) / rated.length;
  },
  aggregateByQuarter: (records) => {
    if (!Array.isArray(records)) return [];
    const quarters = {};
    records.forEach(inv => {
      // Usi schema stores delivery_quarter, sometimes delivery_date
      const q = inv.delivery_quarter || inv.delivery_date || 'Nieznany';
      if (!quarters[q]) quarters[q] = { flats: 0, ratingSum: 0, ratedCount: 0 };
      quarters[q].flats += (parseInt(inv.flats_count) || parseInt(inv.units_count) || 0);
      const r = avgRating(inv);
      if (r > 0) {
        quarters[q].ratingSum += r;
        quarters[q].ratedCount += 1;
      }
    });
    return Object.entries(quarters)
      .map(([q, data]) => ({
        quarter: q,
        flats: data.flats,
        avgRating: data.ratedCount > 0 ? data.ratingSum / data.ratedCount : 0
      }))
      .sort((a, b) => a.quarter.localeCompare(b.quarter));
  },
  extractGeoPoint: (inv) => {
    return inv?.coords && inv.coords[0] !== 0 ? { lat: inv.coords[0], lng: inv.coords[1] } : null;
  }
};

Object.assign(window, { useInvestments, useDevelopers, useConfig, useMetadataConfig, ratedCount, avgRating, ratingStatus, ocenaLog, DataBusProvider, useDataBus, extractModuleContext });
