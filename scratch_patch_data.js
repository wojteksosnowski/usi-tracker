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
      if (f.sources && f.sources.size > 0) params.append('sources', Array.from(f.sources).join(','));
      if (f.cities && f.cities.size > 0) params.append('cities', Array.from(f.cities).join(','));
      url += `?${params.toString()}`;
    }
    return setVariable(type, fetch(url).then(r => r.json()).then(data => {
      if (data && typeof data === 'object' && data.data) {
        setVariable('unreviewedCount', data.unreviewedCount || 0);
        return Array.isArray(data.data) ? data.data : [];
      }
      return Array.isArray(data) ? data : [];
    })).finally(() => setVariable('loading', false));
  }, [setVariable]);

  // Global exports for debugging
