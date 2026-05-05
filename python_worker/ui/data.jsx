// data.jsx — async hook for loading investments from server

// Defined at top level but safely using window.React
const DataBusContext = window.React.createContext();
const LocalModuleContext = window.React.createContext(null);

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Białystok'];

function DataBusProvider({ children }) {
  const { React } = window;
  const isDebug = localStorage.getItem('USI_DEBUG_BUS') === 'true';

  const [bus, setBus] = React.useState({
    investments: [],
    developers: [],
    visibleInvestments: [],
    loading: true,
    isDispatching: false,
    currentInvestment: null,
    nearbyInvestments: [],
    reports: [],
    activeJobs: [],
    appStatus: null,
    
    // Scoped Namespaces
    filters: {
      search: '',
      dev: '',
      status: '',
      sources: new Set(['RP', 'OTO', 'TO']),
      cities: new Set()
    },
    download: {
      activePortals: new Set(['rp']),
      mode: 'grid',
      search: '',
      onlyNew: false,
      selectedDev: ''
    }
  });

  const busRef = React.useRef(bus);
  busRef.current = bus;

  const setVariable = React.useCallback((path, value) => {
    // 1. Handle direct Promise
    if (value && typeof value.then === 'function') {
      if (isDebug) console.log(`[DataBus] ASYNC START: ${path}`);
      setBus(prev => ({ ...prev, isDispatching: true }));
      return value
        .then(res => setVariable(path, res))
        .catch(err => console.error(`Async setVariable failed for ${path}:`, err))
        .finally(() => setBus(prev => ({ ...prev, isDispatching: false })));
    }

    // 2. Handle function (check if async)
    if (typeof value === 'function') {
      const currentVal = path.includes('.') 
        ? path.split('.').reduce((o, i) => (o || {})[i], busRef.current) 
        : busRef.current[path];
      
      const result = value(currentVal);
      if (result && typeof result.then === 'function') {
        if (isDebug) console.log(`[DataBus] ASYNC REDUCER START: ${path}`);
        setBus(prev => ({ ...prev, isDispatching: true }));
        return result
          .then(res => setVariable(path, res))
          .catch(err => console.error(`Async reducer failed for ${path}:`, err))
          .finally(() => setBus(prev => ({ ...prev, isDispatching: false })));
      }
      // If it was sync, we already have the result, but we'll re-evaluate in setBus 
      // to ensure atomicity against React's concurrent state updates.
    }

    // 3. Synchronous Update (standard logic)
    setBus(prev => {
      const keys = path.split('.');
      let nextState = prev;

      if (!path.includes('.')) {
        const nextValue = typeof value === 'function' ? value(prev[path]) : value;
        if (prev[path] === nextValue) return prev;
        nextState = { ...prev, [path]: nextValue };
      } else {
        const updateLevel = (obj, depth) => {
          const key = keys[depth];
          if (depth === keys.length - 1) {
            const currentVal = obj[key];
            const nextVal = typeof value === 'function' ? value(currentVal) : value;
            if (currentVal === nextVal) return obj;
            return { ...obj, [key]: nextVal };
          }
          const child = obj[key] || {};
          const newChild = updateLevel(child, depth + 1);
          if (newChild === child) return obj;
          return { ...obj, [key]: newChild };
        };
        nextState = updateLevel(prev, 0);
      }

      if (isDebug && nextState !== prev) {
        const oldVal = path.split('.').reduce((o, i) => (o || {})[i], prev);
        const newVal = path.split('.').reduce((o, i) => (o || {})[i], nextState);
        console.groupCollapsed(`[DataBus] UPDATE: ${path}`);
        console.log('Prev:', oldVal);
        console.log('Next:', newVal);
        console.groupEnd();
      }

      return nextState;
    });
  }, [isDebug]);

  const refetch = React.useCallback((type = 'investments') => {
    setVariable('loading', true);
    return setVariable(type, fetch(`/api/${type}`).then(r => r.json()).then(data => Array.isArray(data) ? data : []))
      .finally(() => setVariable('loading', false));
  }, [setVariable]);

  // Global exports for debugging
  React.useEffect(() => {
    window.usiExportDataBus = () => {
      const state = busRef.current;
      const json = JSON.stringify(state, (key, value) => {
        if (value instanceof Set) return Array.from(value);
        return value;
      }, 2);
      console.log("[DataBus] FULL EXPORT:\n", json);
      try {
        navigator.clipboard.writeText(json);
        console.log("[DataBus] Skopiowano do schowka.");
      } catch (e) {}
      return state;
    };
    if (isDebug) window.__USI_BUS__ = busRef.current;
    return () => {
      delete window.usiExportDataBus;
      delete window.__USI_BUS__;
    };
  }, [isDebug]);

  React.useEffect(() => {
    if (isDebug) window.__USI_BUS__ = bus;
  }, [bus, isDebug]);

  // Automatic filtering
  const visibleInvestments = React.useMemo(() => {
    const { investments, filters } = bus;
    const { search, dev, status, sources, cities } = filters;
    return investments.filter(inv => {
      if (search) {
        const s = search.toLowerCase();
        const match = (inv.name?.toLowerCase().includes(s) ||
                     inv.developer?.toLowerCase().includes(s) ||
                     inv.district?.toLowerCase().includes(s) ||
                     inv.address?.toLowerCase().includes(s));
        if (!match) return false;
      }
      if (dev && inv.developer_slug !== dev && inv.developer !== dev) return false;
      if (status && inv.status !== status) return false;
      if (sources.size > 0 && inv.source && !sources.has(inv.source.toUpperCase())) return false;
      if (cities.size > 0) {
        const addr = (inv.address || '').toLowerCase();
        const foundCity = MAIN_CITIES.find(c => addr.includes(c.toLowerCase()));
        if (!foundCity || !cities.has(foundCity)) return false;
      }
      return true;
    });
  }, [bus.investments, bus.filters]);

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

  // Polling for active jobs
  React.useEffect(() => {
    let poll;
    const activeCount = (bus.activeJobs || []).length;
    if (activeCount > 0) {
      poll = setInterval(() => refetch('jobs'), 1500);
    }
    return () => { if (poll) clearInterval(poll); };
  }, [bus.activeJobs, refetch]);

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


function useModuleContext(localData) {
  const { React, useDataBus, ratedCount, avgRating, LocalModuleContext } = window;
  const { bus } = useDataBus();
  const ctxData = React.useContext(LocalModuleContext);
  
  const hasBus = bus && Object.keys(bus).length > 0;
  if (!hasBus) {
     // No warning here to avoid console spam during initial renders, but we handle it.
  }

  return React.useMemo(() => {
    try {
      const data = localData || ctxData || bus.visibleInvestments || bus.currentInvestment || [];
      const isArray = Array.isArray(data);
      const records = isArray ? data : [data];
      
      const sumApartments = records.reduce((sum, inv) => sum + (parseInt(inv?.flats_count) || parseInt(inv?.units_count) || 0), 0);
      
      const rated = records.filter(inv => ratedCount(inv) > 0);
      const avgListRating = rated.length > 0 ? rated.reduce((sum, inv) => sum + avgRating(inv), 0) / rated.length : 0;
      
      const quarters = {};
      records.forEach(inv => {
        const q = (inv?.delivery_quarter || inv?.delivery_date) || 'Nieznany';
        if (!quarters[q]) quarters[q] = { flats: 0, ratingSum: 0, ratedCount: 0 };
        quarters[q].flats += (parseInt(inv?.flats_count) || parseInt(inv?.units_count) || 0);
        const r = avgRating(inv);
        if (r > 0) { quarters[q].ratingSum += r; quarters[q].ratedCount += 1; }
      });
      const aggregateByQuarter = Object.entries(quarters)
        .map(([q, d]) => ({ quarter: q, flats: d.flats, avgRating: d.ratedCount > 0 ? d.ratingSum / d.ratedCount : 0 }))
        .sort((a, b) => a.quarter.localeCompare(b.quarter));
        
      const invForGeo = isArray ? (records[0] || {}) : data;
      const coords = invForGeo?.coords || [];
      const geoPoint = coords[0] && coords[0] !== 0 ? { lat: coords[0], lng: coords[1] } : null;

      return { sumApartments, avgListRating, aggregateByQuarter, geoPoint, bus };
    } catch(err) {
      console.error("useModuleContext error:", err);
      return { sumApartments: 0, avgListRating: 0, aggregateByQuarter: [], geoPoint: null, bus: bus || {} };
    }
  }, [localData, bus, ratedCount, avgRating]);
}
window.usiRegister('useModuleContext', useModuleContext);

Object.assign(window, { useInvestments, useDevelopers, useConfig, useMetadataConfig, ratedCount, avgRating, ratingStatus, ocenaLog, DataBusProvider, useDataBus, useModuleContext, LocalModuleContext });

