// data.jsx — async hook for loading investments from server

const shallowCompare = (a, b) => {
  if (a === b) return true;
  if (typeof a !== 'object' || a === null || typeof b !== 'object' || b === null) return false;
  const keysA = Object.keys(a);
  const keysB = Object.keys(b);
  if (keysA.length !== keysB.length) return false;
  for (let key of keysA) {
    if (!Object.prototype.hasOwnProperty.call(b, key) || a[key] !== b[key]) return false;
  }
  return true;
};
window.usiRegister('shallowCompare', shallowCompare);

// Defined at top level but safely using window.React
const DataBusStateContext = window.React.createContext();
const DataBusDispatchContext = window.React.createContext();
const LocalModuleContext = window.React.createContext(null);

// Global exports for Babel-compiled files to share same context instances
window.DataBusStateContext = DataBusStateContext;
window.DataBusDispatchContext = DataBusDispatchContext;
window.LocalModuleContext = LocalModuleContext;

const MAIN_CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Łódź', 'Poznań', 'Gdańsk', 'Szczecin', 'Bydgoszcz', 'Lublin', 'Białystok'];

function DataBusProvider({ children }) {
  const { React } = window;
  const isDebug = localStorage.getItem('USI_DEBUG_BUS') === 'true';

  const [bus, setBus] = React.useState({
    investments: [],
    developers: [],
    loading: true,
    isDispatching: false,
    currentInvestment: null,
    nearbyInvestments: [],
    reports: [],
    activeJobs: [],
    appStatus: null,
    appNotifications: [],
    
    // Scoped Namespaces (for component instances)
    scopes: {},
    
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

  // External store for useSyncExternalStore
  const listeners = React.useRef(new Set());
  const subscribe = React.useCallback((listener) => {
    listeners.current.add(listener);
    return () => listeners.current.delete(listener);
  }, []);
  const getSnapshot = React.useCallback(() => busRef.current, []);

  const notify = React.useCallback(() => {
    listeners.current.forEach(l => l());
  }, []);

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
    }

    // 3. Synchronous Update (standard logic)
    const prev = busRef.current;
    const keys = path.split('.');
    let nextState = prev;

    if (!path.includes('.')) {
      const nextValue = typeof value === 'function' ? value(prev[path]) : value;
      if (prev[path] === nextValue) return;
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

    if (nextState !== prev) {
      if (isDebug) {
        const oldVal = path.split('.').reduce((o, i) => (o || {})[i], prev);
        const newVal = path.split('.').reduce((o, i) => (o || {})[i], nextState);
        console.groupCollapsed(`[DataBus] UPDATE: ${path}`);
        console.log('Prev:', oldVal);
        console.log('Next:', newVal);
        console.groupEnd();
      }
      busRef.current = nextState;
      setBus(nextState);
      notify();
    }
  }, [isDebug, notify]);

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

  // Add visibleInvestments to the bus object for selectors
  busRef.current = { ...bus, visibleInvestments };

  const dispatchValue = React.useMemo(() => ({ 
    setVariable, 
    refetch 
  }), [setVariable, refetch]);

  const stateValue = React.useMemo(() => ({
    bus: busRef.current,
    subscribe,
    getSnapshot
  }), [bus, visibleInvestments, subscribe, getSnapshot]);

  React.useEffect(() => {
    refetch('investments');
    refetch('developers');
  }, []);

  // Polling for active jobs
  React.useEffect(() => {
    // Poll every 3 seconds always to catch background tasks
    const poll = setInterval(() => refetch('jobs'), 3000);
    return () => clearInterval(poll);
  }, [refetch]);

  return (
    <DataBusDispatchContext.Provider value={dispatchValue}>
      <DataBusStateContext.Provider value={stateValue}>
        {children}
      </DataBusStateContext.Provider>
    </DataBusDispatchContext.Provider>
  );
}
window.usiRegister('DataBusProvider', DataBusProvider);

function useDataBus(scopeId) {
  const { React, DataBusStateContext: GlobalState, DataBusDispatchContext: GlobalDispatch } = window;
  const state = React.useContext(GlobalState || DataBusStateContext);
  const dispatch = React.useContext(GlobalDispatch || DataBusDispatchContext);
  if (!state || !dispatch) {
    return { bus: {}, setVariable: () => {}, getVariable: () => {}, refetch: () => {} };
  }
  
  const context = { ...state, ...dispatch };
  const { bus, setVariable, ...rest } = context;

  if (scopeId) {
    const scopedBus = bus.scopes?.[scopeId] || {};
    const scopedSetVariable = (path, value) => setVariable(`scopes.${scopeId}.${path}`, value);
    
    return {
      bus,
      setVariable,
      scopedBus,
      scopedSetVariable,
      ...rest
    };
  }

  return context;
}
window.usiRegister('useDataBus', useDataBus);

function useDataBusSelector(selector, compare = (a, b) => a === b) {
  const { React, DataBusStateContext: GlobalState } = window;
  const context = React.useContext(GlobalState || DataBusStateContext) || {};
  const isDebug = localStorage.getItem('USI_DEBUG_BUS') === 'true';
  
  // Safe defaults to ensure unconditional hook execution
  const subscribe = context.subscribe || (() => () => {});
  const getSnapshot = context.getSnapshot || (() => ({}));

  const slice = React.useSyncExternalStore(
    subscribe,
    () => {
      const val = selector(getSnapshot());
      if (isDebug && localStorage.getItem('USI_DEBUG_RENDER') === 'true') {
        console.log(`[useDataBusSelector] snapshot update triggered`);
      }
      return val;
    },
    () => selector({})
  );

  return slice;
}
window.usiRegister('useDataBusSelector', useDataBusSelector);

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
  const { React, useApi } = window;
  const [config, setConfig] = React.useState(null);
  const { request } = useApi();

  React.useEffect(() => {
    request('/api/config')
      .then(data => setConfig(data))
      .catch(() => setConfig({}));
  }, [request]);

  return config;
}
window.usiRegister('useConfig', useConfig);

function useMetadataConfig() {
  const { React, useApi } = window;
  const [meta, setMeta] = React.useState(null);
  const { request } = useApi();

  React.useEffect(() => {
    request('/api/metadata-config')
      .then(data => setMeta(data))
      .catch(() => setMeta([]));
  }, [request]);

  return meta;
}
window.usiRegister('useMetadataConfig', useMetadataConfig);

const _CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];

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

Object.assign(window, { useInvestments, useDevelopers, useConfig, useMetadataConfig, DataBusProvider, useDataBus, useModuleContext, LocalModuleContext });
