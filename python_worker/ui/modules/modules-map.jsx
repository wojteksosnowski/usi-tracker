// modules-map.jsx — Map modules (HERE Maps)

(function() {
  const { React, usiRegister, useDarkMode, useModuleContext, BaseModule, useDataBus } = window;

  function MiniMap({ geo, label, height = 140, points = [], hereUrl = '', hereUrlDark = '', coords, containerWidth }) {
    const ctx = useModuleContext();
    const mapCoords = geo ? [geo.lat, geo.lng] : (coords || (ctx.geoPoint ? [ctx.geoPoint.lat, ctx.geoPoint.lng] : null));
    
    React.useEffect(() => {
      if (containerWidth > 0) { console.log(`[MiniMap] containerWidth: ${Math.round(containerWidth)}px`); }
    }, [containerWidth]);

    if (!mapCoords || mapCoords[0] === 0) return null;
    const url = `https://www.google.com/maps/@${mapCoords[0]},${mapCoords[1]},780m/`;
    const isDark = useDarkMode();
    const imgSrc = (isDark && hereUrlDark) ? hereUrlDark : hereUrl;

    return (
      <a data-component="MiniMap" href={url} target="_blank" rel="noopener" title="Otwórz w Google Maps"
        className="usi-minimap-container"
        style={{ '--usi-map-height': `${height}px` }}>
        {imgSrc ? (
          <img src={imgSrc} alt="Mapa lokalizacji" className="usi-minimap-img" />
        ) : (
          <svg viewBox="0 0 300 200" preserveAspectRatio="none" className="usi-minimap-svg">
            <rect x="0" y="0" width="300" height="200" fill="var(--usi-surface-3)" />
            <path d="M0 40 L80 50 L120 30 L200 35 L300 60 L300 0 L0 0 Z" fill="color-mix(in oklab, #7DB951 18%, transparent)" />
            <path d="M0 160 L40 165 L80 158 L120 170 L160 168 L200 175 L240 170 L300 178 L300 200 L0 200 Z" fill="color-mix(in oklab, #3989C6 18%, transparent)" />
            <g stroke="var(--usi-border-strong)" strokeWidth="1.2" fill="none" opacity="0.6">
              <path d="M-10 95 L310 105" /><path d="M-10 70 L310 75" /><path d="M-10 130 L310 138" />
              <path d="M70 -10 L75 210" /><path d="M150 -10 L160 210" /><path d="M225 -10 L230 210" />
            </g>
            <g transform="translate(150,100)">
              <circle r="14" fill="var(--usi-accent, #E5006D)" opacity="0.18" />
              <circle r="7" fill="var(--usi-accent, #E5006D)" stroke="#fff" strokeWidth="2" />
            </g>
          </svg>
        )}
      </a>
    );
  }
  MiniMap.__spec = {
    props: {
      label: { type: 'String', label: 'Etykieta', default: 'Lokalizacja' },
      height: { type: 'Number', label: 'Wysokość (px)', default: 140 },
      hereUrl: { type: 'String', label: 'Statyczna Mapa (Light)', default: '' },
      hereUrlDark: { type: 'String', label: 'Statyczna Mapa (Dark)', default: '' }
    }
  };
  window.ModuleRegistry.register('MiniMap', MiniMap, MiniMap.__spec);
  usiRegister('MiniMap', MiniMap);

  function MapModule({ instanceId, data: localData, height = 400, title = "Mapa Inwestycji", hereApiKey }) {
    const mapRef = React.useRef(null);
    const containerRef = React.useRef(null);
    const { bus, setVariable, scopedBus, scopedSetVariable } = useDataBus(instanceId);
    const [mapLoaded, setMapLoaded] = React.useState(!!window.H);
    const ctx = useModuleContext(localData);

    React.useEffect(() => {
      if (window.H) {
        setMapLoaded(true);
        return;
      }
      const loadScript = (src) => new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = src;
        script.async = false;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });

      const initHereMaps = async () => {
        try {
          await loadScript('https://js.api.here.com/v3/3.1/mapsjs-core.js');
          await loadScript('https://js.api.here.com/v3/3.1/mapsjs-service.js');
          await loadScript('https://js.api.here.com/v3/3.1/mapsjs-ui.js');
          await loadScript('https://js.api.here.com/v3/3.1/mapsjs-mapevents.js');
          await loadScript('https://js.api.here.com/v3/3.1/mapsjs-clustering.js');
          const link = document.createElement('link');
          link.rel = 'stylesheet';
          link.type = 'text/css';
          link.href = 'https://js.api.here.com/v3/3.1/mapsjs-ui.css';
          document.head.appendChild(link);
          setMapLoaded(true);
        } catch (err) {
          console.error("Failed to load HERE Maps API", err);
        }
      };
      initHereMaps();
    }, []);

    React.useEffect(() => {
      if (!mapLoaded || !containerRef.current) return;
      const H = window.H;

      const platform = new H.service.Platform({
        apikey: hereApiKey || window.usiConfig?.hereApiKey || 'BDske2zxCqqwwBGMf4IBKA49FRvRZLe4TnfBtYTor9c'
      });
      const defaultLayers = platform.createDefaultLayers();
      
      if (mapRef.current) {
        mapRef.current.dispose();
        containerRef.current.innerHTML = '';
      }

      const map = new H.Map(
        containerRef.current,
        defaultLayers.vector.normal.map,
        {
          center: { lat: 52.23, lng: 21.01 },
          zoom: 10,
          pixelRatio: window.devicePixelRatio || 1
        }
      );

      window.addEventListener('resize', () => map.getViewPort().resize());
      const behavior = new H.mapevents.Behavior(new H.mapevents.MapEvents(map));
      const ui = H.ui.UI.createDefault(map, defaultLayers);

      const data = Array.isArray(localData) ? localData : (ctx.bus?.visibleInvestments || []);
      const dataPoints = data.map(inv => {
        const coords = inv.coords || [];
        if (coords[0] && coords[1]) {
          return new H.clustering.DataPoint(coords[0], coords[1], null, inv);
        }
        return null;
      }).filter(Boolean);

      if (dataPoints.length > 0) {
        const clusteredDataProvider = new H.clustering.Provider(dataPoints, {
          clusteringOptions: { eps: 32, minWeight: 2 }
        });
        const clusteringLayer = new H.map.layer.ObjectLayer(clusteredDataProvider);
        map.addLayer(clusteringLayer);

        clusteredDataProvider.addEventListener('tap', (e) => {
          const target = e.target;
          if (target instanceof H.map.Marker && target.getData) {
            const inv = target.getData();
            if (!inv.isCluster) {
               console.log(`[MapModule:${instanceId}] selected: ${inv.slug}`);
               setVariable('currentInvestment', inv);
               if (scopedSetVariable) scopedSetVariable('selectedId', inv.slug || inv.name);
            } else {
               // Dla klastrów używamy getBoundingBox z obiektu klastra (inv)
               if (inv && typeof inv.getBoundingBox === 'function') {
                 map.getViewModel().setLookAtData({bounds: inv.getBoundingBox()});
               }
            }
          }
        });

        try {
          const boundingBox = H.geo.Rect.coverPoints(dataPoints.map(p => new H.geo.Point(p.lat, p.lng)));
          if (boundingBox) {
             map.getViewModel().setLookAtData({bounds: boundingBox});
          }
        } catch(e) {}
      }

      mapRef.current = map;
      return () => { if (mapRef.current) mapRef.current.dispose(); };
    }, [mapLoaded, localData, ctx.bus?.visibleInvestments, setVariable]);

    return (
      <BaseModule title={title} icon="map">
        {!mapLoaded ? (
          <div className="usi-app-loading usi-flex-center" style={{ '--usi-map-height': `${height}px` }}>
            Ładowanie mapy...
          </div>
        ) : (
          <div className="usi-map-module-relative">
            {scopedBus?.selectedId && (
              <div className="usi-map-module-selection-badge">
                <div className="usi-tiny usi-weight-700 usi-text-accent usi-text-uppercase usi-m-b-2">Wybrano</div>
                <div className="usi-small usi-weight-600">{scopedBus.selectedId}</div>
              </div>
            )}
            <div ref={containerRef} className="usi-map-module-canvas" style={{ '--usi-map-height': `${height}px` }} />
          </div>
        )}
      </BaseModule>
    );
  }
  MapModule.__spec = {
    props: {
      title: { type: 'String', label: 'Tytuł modułu', default: 'Mapa Inwestycji' },
      height: { type: 'Number', label: 'Wysokość (px)', default: 400 },
      hereApiKey: { type: 'String', label: 'HERE API Key', default: '' }
    }
  };
  window.ModuleRegistry.register('MapModule', MapModule, MapModule.__spec);
  usiRegister('MapModule', MapModule);

})();
