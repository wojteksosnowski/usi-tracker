// data.jsx — async hook for loading investments from server

function useInvestments() {
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

function useConfig() {
  const [config, setConfig] = React.useState({});
  React.useEffect(() => {
    fetch('/api/config')
      .then(r => r.json())
      .then(data => setConfig(data))
      .catch(e => console.error("Failed to load config", e));
  }, []);
  return config;
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

Object.assign(window, { useInvestments, useConfig, ratedCount, avgRating, ratingStatus, ocenaLog });
