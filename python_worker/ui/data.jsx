// data.jsx — async hook for loading investments from server

// Defined at top level but safely using window.React
const DataBusContext = window.React.createContext();

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Białystok'];

function DataBusProvider({ children }) {
  const { React } = window;
  const [bus, setBus] = React.useState({
    investments: [],
    developers: [],
    visibleInvestments: [],
    loading: true,
    currentInvestment: null,
    nearbyInvestments: [],
    reports: [],
    activeJobs: [],
    appStatus: null,
    
    // Filter state
    search: '',
    filterDev: '',
    filterStatus: '',
    activeSources: new Set(['RP', 'OTO', 'TO']),
    activeCities: new Set()
  });

  const setVariable = React.useCallback((name, value) => {
    setBus(prev => {
      const nextValue = typeof value === 'function' ? value(prev[name]) : value;
      if (prev[name] === nextValue) return prev;
      return { ...prev, [name]: nextValue };
    });
  }, []);

  const refetch = React.useCallback(async (type = 'investments') => {
    setVariable('loading', true);
    try {
      const r = await fetch(`/api/${type}`);
      const data = await r.json();
      setVariable(type, Array.isArray(data) ? data : []);
    } catch (e) {
      console.error(`Failed to refetch ${type}`, e);
    } finally {
      setVariable('loading', false);
    }
  }, [setVariable]);

  // Automatic filtering
  const visibleInvestments = React.useMemo(() => {
    const { investments, search, filterDev, filterStatus, activeSources, activeCities } = bus;
    return investments.filter(inv => {
      if (search) {
        const s = search.toLowerCase();
        const match = (inv.name?.toLowerCase().includes(s) ||
                     inv.developer?.toLowerCase().includes(s) ||
                     inv.district?.toLowerCase().includes(s) ||
                     inv.address?.toLowerCase().includes(s));
        if (!match) return false;
      }
      if (filterDev && inv.developer_slug !== filterDev && inv.developer !== filterDev) return false;
      if (filterStatus && inv.status !== filterStatus) return false;
      if (activeSources.size > 0 && inv.source && !activeSources.has(inv.source.toUpperCase())) return false;
      if (activeCities.size > 0) {
        const addr = (inv.address || '').toLowerCase();
        const foundCity = MAIN_CITIES.find(c => addr.includes(c.toLowerCase()));
        if (!foundCity || !activeCities.has(foundCity)) return false;
      }
      return true;
    });
  }, [bus.investments, bus.search, bus.filterDev, bus.filterStatus, bus.activeSources, bus.activeCities]);

  // Sync visibleInvestments back to bus (using a ref to avoid infinite loops if needed, 
  // but here we just pass it in value)
  const value = React.useMemo(() => ({ 
    bus: { ...bus, visibleInvestments }, 
    setVariable, 
    refetch 
  }), [bus, visibleInvestments, setVariable, refetch]);

  React.useEffect(() => {
    refetch('investments');
    refetch('developers');
  }, []);

  return (
    <DataBusContext.Provider value={value}>
      {children}
    </DataBusContext.Provider>
  );
}
window.usiRegister('DataBusProvider', DataBusProvider);

function useDataBus() {
  const { React } = window;
  const context = React.useContext(DataBusContext);
  if (!context) {
    // Fallback for components rendered outside provider (e.g. during initial loads)
    return { bus: {}, setVariable: () => {}, getVariable: () => {}, refetch: () => {} };
  }
  return context;
}
window.usiRegister('useDataBus', useDataBus);

function useInvestments() {
  const { bus, refetch } = useDataBus();
  return { 
    investments: bus.investments, 
    loading: bus.loading, 
    refetch: () => refetch('investments') 
  };
}
window.usiRegister('useInvestments', useInvestments);

function useDevelopers() {
  const { bus, refetch } = useDataBus();
  return { 
    developers: bus.developers, 
    loading: bus.loading, 
    refetch: () => refetch('developers') 
  };
}
window.usiRegister('useDevelopers', useDevelopers);

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
window.usiRegister('useConfig', useConfig);

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
window.usiRegister('useMetadataConfig', useMetadataConfig);

const _CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];

const ratedCount = (inv) =>
  _CATS.filter(k => ((inv.ratings || {})[k] ?? null) !== null).length;

const avgRating = (inv) => {
  const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
};
window.usiRegister('avgRating', avgRating);

const ratingStatus = (inv) => {
  const c = ratedCount(inv);
  if (c === 0) return 'none';
  if (c < 6) return 'partial';
  return 'done';
};
window.usiRegister('ratingStatus', ratingStatus);

const ocenaLog = (inv) => {
  const vals = _CATS.map(k => ((inv.ratings || {})[k] ?? null)).filter(v => v !== null);
  if (vals.length === 0) return null;
  const sum = vals.reduce((acc, v) => acc + Math.exp(v), 0);
  return Math.log(sum) - Math.log(vals.length);
};
window.usiRegister('ocenaLog', ocenaLog);


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
