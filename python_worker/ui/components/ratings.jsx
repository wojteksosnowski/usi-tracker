// ratings.jsx — Star Rating and scoring components

(function() {
  const { React, usiRegister } = window;

  const StarRating = ({ value = 0, max = 4, size = 22, color, onChange, readonly = false, label }) => {
    const [hover, setHover] = React.useState(0);
    const display = hover || value;
    const c = color || 'var(--usi-accent, #1F1C16)';
    return (
      <div data-component="StarRating" role="radiogroup" aria-label={label}
        style={{ display: 'inline-flex', gap: 2, color: c, cursor: readonly ? 'default' : 'pointer' }}
        onMouseLeave={() => setHover(0)}>
        {Array.from({ length: max }).map((_, i) => {
          const idx = i + 1;
          const filled = idx <= Math.floor(display);
          const halfFill = !filled && idx - 0.5 <= display;
          return (
            <button key={i} type="button" disabled={readonly}
              aria-checked={value === idx} role="radio"
              onMouseEnter={() => !readonly && setHover(idx)}
              onClick={() => !readonly && onChange && onChange(value === idx ? 0 : idx)}
              style={{
                border: 'none', background: 'transparent', padding: 0,
                cursor: readonly ? 'default' : 'pointer',
                width: size, height: size, lineHeight: 0,
                transform: hover === idx ? 'scale(1.1)' : 'scale(1)',
                transition: 'transform .12s',
              }}>
              <svg width={size} height={size} viewBox="0 0 48 48" style={{ display: 'block' }}>
                <defs>
                  <linearGradient id={`half-${i}-${size}`} x1="0" x2="1" y1="0" y2="0">
                    <stop offset="50%" stopColor={c} />
                    <stop offset="50%" stopColor="var(--usi-star-empty)" />
                  </linearGradient>
                </defs>
                <path d="M22.85 15.05c0-.32 .21-.6 .51-.69 .75-.21 2.53-.5 6.57-.5 4.05 0 5.83 .3 6.58 .51 .3 .09 .51 .37 .51 .68v15.78L51.06 26c.3-.1 .63 .02 .81 .28 .43 .65 1.27 2.25 2.51 6.1 1.25 3.85 1.51 5.64 1.55 6.42 .01 .31-.19 .6-.49 .69-3.04 .99-20.55 6.68-30 9.75l18.55 25.56c.17 .25 .16 .59 .03 .83-.49 .61-1.75 1.9-5.02 4.27-3.27 2.38-4.89 3.18-5.62 3.45-.26 .09-.54 .03-.74-.16L24 88c-19.36-26-19.55-26.21-19.71-26.34-.29-.21-.49-.49-.46-.81 .03-.78 .29-2.57 1.55-6.43 1.26-3.89 2.1-5.48 2.53-6.11 .17-.25 .49-.36 .77-.27z"
                  fill={filled ? c : (halfFill ? `url(#half-${i}-${size})` : 'var(--usi-star-empty)')}
                  style={{ transition: 'fill .12s' }} />
              </svg>
            </button>
          );
        })}
      </div>
    );
  };
  usiRegister('StarRating', StarRating);

  const CategoryRating = ({ category, value, onChange, variant = 'stars', size = 'md' }) => {
    const sz = size === 'sm' ? 18 : size === 'lg' ? 28 : 22;
    if (variant === 'circles') {
      return (
        <div data-component="CategoryRating" style={{ display: 'flex', gap: 5, alignItems: 'center' }}>
          {[0,1,2,3,4].map(n => {
            const filled = value !== null && n <= value;
            return (
              <button key={n} type="button"
                onClick={() => onChange(value === n ? null : n)}
                title={String(n)}
                style={{
                  width: 30, height: 30, borderRadius: '50%', padding: 0,
                  border: 'none',
                  background: filled ? category.color : 'var(--usi-surface-3)',
                  cursor: 'pointer',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  transition: 'background .12s',
                  flexShrink: 0,
                }}>
                {filled && (
                  <img
                    src={n === 0 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'}
                    width="14" height="16"
                    alt={String(n)}
                    style={{ display: 'block', pointerEvents: 'none' }}
                  />
                )}
              </button>
            );
          })}
        </div>
      );
    }
    if (variant === 'chips') {
      return (
        <div data-component="CategoryRating" style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
          {[0,1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              style={{
                border: '.5px solid var(--usi-border-strong)',
                background: value === n ? category.color : 'var(--usi-surface)',
                color: value === n ? '#fff' : 'var(--usi-ink-2)',
                borderColor: value === n ? category.color : 'var(--usi-border-strong)',
                borderRadius: 6, height: 26, minWidth: 26, padding: '0 6px',
                fontSize: 12, fontWeight: 600, cursor: 'pointer',
                fontFamily: 'inherit',
                transition: 'all .12s',
              }}>{n}</button>
          ))}
        </div>
      );
    }
    if (variant === 'segmented') {
      return (
        <div data-component="CategoryRating" style={{ display: 'inline-flex', background: 'var(--usi-surface-3)', borderRadius: 8, padding: 2, position: 'relative' }}>
          {[0,1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              style={{
                border: 'none', background: value === n ? category.color : 'transparent',
                color: value === n ? '#fff' : 'var(--usi-ink-3)',
                borderRadius: 6, height: 24, width: 28, padding: 0,
                fontSize: 12, fontWeight: 600, cursor: 'pointer', fontFamily: 'inherit',
                transition: 'all .12s',
              }}>{n}</button>
          ))}
        </div>
      );
    }
    if (variant === 'dots') {
      return (
        <div data-component="CategoryRating" style={{ display: 'inline-flex', gap: 4 }}>
          {[1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              style={{
                border: 'none', cursor: 'pointer', padding: 0,
                width: 14, height: 14, borderRadius: '50%',
                background: n <= value ? category.color : 'var(--usi-star-empty)',
                transition: 'background .12s, transform .1s',
              }} />
          ))}
        </div>
      );
    }
    return <StarRating value={value} onChange={onChange} color={category.color} size={sz} label={category.key} />;
  };
  usiRegister('CategoryRating', CategoryRating);

  const CategoryStripe = ({ ratings, height = 4 }) => {
    const categories = window.USI_CATEGORIES || [];
    return (
      <div data-component="CategoryStripe" style={{ display: 'flex', gap: 1.5, height, borderRadius: 2, overflow: 'hidden' }}>
        {categories.map(cat => {
          const v = ratings[cat.key] || 0;
          return (
            <div key={cat.key} style={{ flex: 1, background: 'var(--usi-star-empty)', position: 'relative' }}>
              {v > 0 && (
                <div style={{
                  position: 'absolute', inset: 0,
                  background: cat.color,
                  opacity: 0.3 + (v / 4) * 0.7,
                }} />
              )}
            </div>
          );
        })}
      </div>
    );
  };
  usiRegister('CategoryStripe', CategoryStripe);

  const CategoryDots = ({ ratings, size = 8 }) => {
    const categories = window.USI_CATEGORIES || [];
    return (
      <div data-component="CategoryDots" style={{ display: 'flex', gap: 4 }}>
        {categories.map(cat => {
          const v = ratings[cat.key] || 0;
          return (
            <div key={cat.key} title={`${cat.key}: ${v || '—'}`}
              style={{
                width: size, height: size, borderRadius: '50%',
                background: v > 0 ? cat.color : 'transparent',
                border: v > 0 ? 'none' : `1px solid var(--usi-border-strong)`,
                opacity: v > 0 ? 0.4 + (v / 4) * 0.6 : 1,
              }} />
          );
        })}
      </div>
    );
  };
  usiRegister('CategoryDots', CategoryDots);

  const UsiStarScore = ({ score }) => {
    if (score === null || score === undefined) return null;
    let nFull = Math.floor(score);
    const frac = score - nFull;
    let fracChar = null;
    if (frac >= 0.875) {
      nFull += 1;
    } else if (frac >= 0.625) {
      fracChar = '¾';
    } else if (frac >= 0.375) {
      fracChar = '½';
    } else if (frac >= 0.125) {
      fracChar = '¼';
    }
    const Star = ({ opacity = 1 }) => (
      <svg width={15} height={15} viewBox="0 0 16 16" fill="currentColor" style={{ display: 'block', opacity }}>
        <path d="M8 2l1.8 4 4.2.4-3.2 2.8 1 4.4L8 11.4 4.2 13.6l1-4.4L2 6.4l4.2-.4z" />
      </svg>
    );
    return (
      <div data-component="UsiStarScore" style={{ display: 'inline-flex', alignItems: 'center', gap: 1, color: 'var(--usi-accent)' }}>
        {Array.from({ length: nFull }).map((_, i) => <Star key={i} />)}
        {fracChar && (
          <>
            <Star opacity={0.3} />
            <span style={{ fontSize: 12, fontWeight: 600, lineHeight: 1, marginLeft: 1 }}>{fracChar}</span>
          </>
        )}
      </div>
    );
  };
  usiRegister('UsiStarScore', UsiStarScore);

  const WeightedUsiScore = ({ score, size = 40 }) => {
    if (score === null || score === undefined) return null;
    let nFull = Math.floor(score);
    const frac = score - nFull;
    let fracChar = null;
    if (frac >= 0.875) {
      nFull += 1;
    } else if (frac >= 0.625) {
      fracChar = '¾';
    } else if (frac >= 0.375) {
      fracChar = '½';
    } else if (frac >= 0.125) {
      fracChar = '¼';
    }
    return (
      <div data-component="WeightedUsiScore" style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <div style={{
          width: size, height: size, borderRadius: '50%',
          background: 'var(--usi-accent)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          boxShadow: '0 4px 12px rgba(229, 0, 109, 0.15)',
          flexShrink: 0,
        }}>
          <img 
            src={score < 0.5 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'} 
            width={size * 0.55} height={size * 0.55} 
            alt="USI"
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.1 }}>
          <div style={{ fontSize: size * 0.55, fontWeight: 800, color: 'var(--usi-ink)' }}>
            {nFull}{fracChar && <span style={{ fontSize: '0.65em', verticalAlign: 'top', marginLeft: 1 }}>{fracChar}</span>}
            <span style={{ fontSize: '0.5em', color: 'var(--usi-ink-4)', fontWeight: 600, marginLeft: 3 }}>/ 4</span>
          </div>
          <div className="usi-tiny" style={{ opacity: 0.5, fontWeight: 800, textTransform: 'uppercase', letterSpacing: 0.5, fontSize: 9 }}>Ważona USI</div>
        </div>
      </div>
    );
  };
  usiRegister('WeightedUsiScore', WeightedUsiScore);

})();

