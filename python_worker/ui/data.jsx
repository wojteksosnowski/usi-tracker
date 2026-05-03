// data.jsx — async hook for loading investments from server

const DataBusContext = React.createContext();

function DataBusProvider({ children }) {
  const [bus, setBus] = React.useState({
    visibleInvestments: [],
    currentInvestment: null,
    nearbyInvestments: [],
    reports: []
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
  const context = React.useContext(DataBusContext);
  if (!context) {
    // Fallback for components rendered outside provider (e.g. during initial loads)
    return { bus: {}, setVariable: () => {}, getVariable: () => {} };
  }
  return context;
}

function useInvestments() {
// ... existing useInvestments ...
  const [investments, setInvestments] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

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
  const [developers, setDevelopers] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

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
  const [config, setConfig] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => setConfig(data))
      .catch(e => {
        console.error("Failed to load config", e);
        setConfig({});
      });
  }, []);
  return config;
}

function useMetadataConfig() {
  const [meta, setMeta] = React.useState(null);
  React.useEffect(() => {
    fetch('/api/metadata-config')
      .then(r => r.json())
      .then(data => setMeta(data))
      .catch(e => {
        console.error("Failed to load metadata config", e);
        setMeta([]);
      });
  }, []);
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

Object.assign(window, { useInvestments, useDevelopers, useConfig, useMetadataConfig, ratedCount, avgRating, ratingStatus, ocenaLog, DataBusProvider, useDataBus });
