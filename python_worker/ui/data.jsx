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
    pendingTotal: 0,
    appStatus: null,
    appNotifications: [],
    
    // Scoped Namespaces (for component instances)
    scopes: {},
    
    filters: {
      search: '',
      dev: '',
      status: '',
      onlyUnreviewed: false,
      onlyNoPhotos: false,
      sources: new Set(['RP', 'OTO', 'TO']),
      segments: new Set(),
      cities: new Set()
    },
    devFilters: {
      onlyActive: false,
      onlyMerged: false,
      onlySuggestions: false,
      onlyPending: false
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
    let url = `/api/${type}`;
    if (type === 'investments') {
      const f = busRef.current.filters;
      const params = new URLSearchParams();
      if (f.search) params.append('search', f.search);
      if (f.dev) params.append('dev', f.dev);
      if (f.status) params.append('status', f.status);
      if (f.onlyUnreviewed) params.append('onlyUnreviewed', 'true');
      if (f.onlyNoPhotos) params.append('onlyNoPhotos', 'true');
      if (f.sources && f.sources.size > 0) f.sources.forEach(s => params.append('sources', s));
      if (f.segments && f.segments.size > 0) f.segments.forEach(s => params.append('segments', s));
      if (f.cities && f.cities.size > 0) f.cities.forEach(s => params.append('cities', s));
      url += `?${params.toString()}`;
    }
    return setVariable(type, fetch(url).then(r => r.json()).then(data => {
      if (data && typeof data === 'object' && data.data) {
        setVariable('unreviewedCount', data.unreviewedCount || 0);
        if (data.ratingsMap) setVariable('ratingsMap', data.ratingsMap);
        return Array.isArray(data.data) ? data.data : [];
      }
      return Array.isArray(data) ? data : [];
    })).finally(() => setVariable('loading', false));
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

  // Trigger backend refetch on filter change with debounce.
  // FIXME: Build a stable, deterministic string from filters WITHOUT creating new Set/Array
  // references on every render — which was previously causing spurious re-fetches.
  const f = bus.filters;
  const filtersStr = [
    f.search || '',
    f.dev || '',
    f.status || '',
    f.onlyUnreviewed ? '1' : '0',
    f.onlyNoPhotos ? '1' : '0',
    f.sources instanceof Set ? Array.from(f.sources).sort().join(',') : '',
    f.segments instanceof Set ? Array.from(f.segments).sort().join(',') : '',
    f.cities instanceof Set ? Array.from(f.cities).sort().join(',') : ''
  ].join('|');

  const refetchRef = React.useRef(refetch);
  React.useLayoutEffect(() => { refetchRef.current = refetch; });

  React.useEffect(() => {
    const timer = setTimeout(() => refetchRef.current('investments'), 300);
    return () => clearTimeout(timer);
  }, [filtersStr]); // Only filtersStr — no `refetch` in deps to avoid restart on every render

  const { visibleInvestments, unreviewedCount } = React.useMemo(() => {
    return { visibleInvestments: bus.investments, unreviewedCount: bus.unreviewedCount || 0 };
  }, [bus.investments, bus.unreviewedCount]);

  // Add visibleInvestments to the bus object for selectors
  busRef.current = { ...bus, visibleInvestments, unreviewedCount };

  const dispatchValue = React.useMemo(() => ({ 
    setVariable, 
    refetch 
  }), [setVariable, refetch]);

  const stateValue = React.useMemo(() => ({
    bus: busRef.current,
    subscribe,
    getSnapshot
  }), [bus, visibleInvestments, subscribe, getSnapshot]);

  // Initial data load — run once on mount.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  React.useEffect(() => {
    refetchRef.current('investments');
    refetchRef.current('developers');
  }, []);

  // Polling for active jobs with "Sticky" logic for finished tasks.
  // CRITICAL: `refetch` is intentionally accessed via `refetchRef` (not listed in deps)
  // to prevent the interval from being torn down and re-created on every render.
  // `setVariable` is stable (created with useCallback once), so it is safe in deps.
  React.useEffect(() => {
    const STICKY_DURATION = 5000;
    const stickyJobs = new Map(); // jobId -> { job, expires }

    const poll = setInterval(() => {
      fetch('/api/jobs')
        .then(r => r.json())
        .then(newJobs => {
          const now = Date.now();
          const currentActive = busRef.current.activeJobs || [];
          
          // 1. Identify jobs that just finished (present in local, but not in server response)
          currentActive.forEach(job => {
            const stillActive = newJobs.find(nj => nj.id === job.id);
            if (!stillActive && !stickyJobs.has(job.id)) {
              // Mark as sticky if it was running/queued
              if (job.status === 'running' || job.status === 'queued') {
                const finishedJob = { ...job, status: 'completed', message: 'Finished.' };
                stickyJobs.set(job.id, { job: finishedJob, expires: now + STICKY_DURATION });
                // Trigger data refresh on job completion — via ref to avoid dep instability
                refetchRef.current('investments');
                refetchRef.current('developers');
              }
            }
          });

          // 2. Filter out expired sticky jobs
          for (const [id, data] of stickyJobs.entries()) {
            if (now > data.expires) stickyJobs.delete(id);
          }

          // 3. Merge server active jobs with local sticky jobs
          const merged = [...newJobs];
          stickyJobs.forEach(data => {
            if (!merged.find(mj => mj.id === data.job.id)) {
              merged.push(data.job);
            }
          });

          setVariable('activeJobs', merged);
        })
        .catch(() => {});

      // Also poll pending summary
      fetch('/api/reports/pending-summary')
        .then(r => r.json())
        .then(data => {
          if (data.total_pending != null) setVariable('pendingTotal', data.total_pending);
        })
        .catch(() => {});
    }, 3000);
    return () => clearInterval(poll);
  }, [setVariable]); // `refetch` intentionally omitted — accessed via `refetchRef`

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
    request('/api/metadata-config', { noCache: true })
      .then(data => setMeta(data))
      .catch(() => setMeta([]));
  }, [request]);

  return meta;
}
window.usiRegister('useMetadataConfig', useMetadataConfig);

const _CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia'];

function useModuleContext(localData) {
  const { React, useDataBus, LocalModuleContext } = window;
  const { bus } = useDataBus();
  const ctxData = React.useContext(LocalModuleContext);

  return React.useMemo(() => {
    try {
      const data = localData || ctxData || bus.visibleInvestments || bus.currentInvestment || [];
      const isArray = Array.isArray(data);
      
      const invForGeo = isArray ? (data[0] || {}) : data;
      const coords = invForGeo?.coords || [];
      const geoPoint = coords[0] && coords[0] !== 0 ? { lat: coords[0], lng: coords[1] } : null;

      return { geoPoint, bus };
    } catch(err) {
      console.error("useModuleContext error:", err);
      return { geoPoint: null, bus: bus || {} };
    }
  }, [localData, bus]);
}
window.usiRegister('useModuleContext', useModuleContext);

Object.assign(window, { useInvestments, useDevelopers, useConfig, useMetadataConfig, DataBusProvider, useDataBus, useModuleContext, LocalModuleContext });
