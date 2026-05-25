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
