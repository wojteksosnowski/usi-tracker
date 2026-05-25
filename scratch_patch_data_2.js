  // Trigger backend refetch on filter change with debounce
  const filtersStr = JSON.stringify(bus.filters, (k, v) => v instanceof Set ? Array.from(v).sort() : v);
  React.useEffect(() => {
    const timer = setTimeout(() => refetch('investments'), 300);
    return () => clearTimeout(timer);
  }, [filtersStr, refetch]);

  const { visibleInvestments, unreviewedCount } = React.useMemo(() => {
    return { visibleInvestments: bus.investments, unreviewedCount: bus.unreviewedCount || 0 };
  }, [bus.investments, bus.unreviewedCount]);

  // Add visibleInvestments to the bus object for selectors
