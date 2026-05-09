// ratings.jsx — Star Rating and scoring components

(function() {
  const { React, usiRegister } = window;

  const StarRating = ({ value = 0, max = 4, size = 22, color, onChange, readonly = false, label }) => {
    const [hover, setHover] = React.useState(0);
    const display = hover || value;
    const c = color || 'var(--usi-accent, #1F1C16)';
    return (
      <div data-component="StarRating" role="radiogroup" aria-label={label}
        className="usi-starrating-container"
        style={{ color: c, cursor: readonly ? 'default' : 'pointer' }}
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
              className="usi-starrating-btn"
              style={{
                cursor: readonly ? 'default' : 'pointer',
                width: size, height: size,
                transform: hover === idx ? 'scale(1.1)' : 'scale(1)',
                position: 'relative'
              }}>
              <img src="/assets/usi-star-white.svg" width={size} height={size}
                style={{
                  opacity: filled || halfFill ? 1 : 0.2,
                  filter: (filled || halfFill) ? 'none' : 'grayscale(1) brightness(0.5)',
                  transition: 'opacity .12s, filter .12s'
                }}
                alt="star"
              />
              {halfFill && (
                <div style={{
                  position: 'absolute', top: 0, left: 0, width: '50%', height: '100%',
                  overflow: 'hidden', pointerEvents: 'none'
                }}>
                  <img src="/assets/usi-star-white.svg" width={size} height={size}
                    style={{ position: 'absolute', top: 0, left: 0 }}
                    alt="star-half"
                  />
                </div>
              )}
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
        <div data-component="CategoryRating" className="usi-categoryrating-circles">
          {[0,1,2,3,4].map(n => {
            const filled = value !== null && n <= value;
            return (
              <button key={n} type="button"
                onClick={() => onChange(value === n ? null : n)}
                title={String(n)}
                className="usi-categoryrating-circle-btn"
                style={{ background: filled ? category.color : 'var(--usi-surface-3)' }}>
                {filled && (
                  <img
                    src={n === 0 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'}
                    width="14" height="16"
                    alt={String(n)}
                    className="usi-categoryrating-circle-img"
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
        <div data-component="CategoryRating" className="usi-categoryrating-chips">
          {[0,1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              className="usi-categoryrating-chip-btn"
              style={{
                background: value === n ? category.color : 'var(--usi-surface)',
                color: value === n ? '#fff' : 'var(--usi-ink-2)',
                borderColor: value === n ? category.color : 'var(--usi-border-strong)',
              }}>{n}</button>
          ))}
        </div>
      );
    }
    if (variant === 'segmented') {
      return (
        <div data-component="CategoryRating" className="usi-categoryrating-segmented">
          {[0,1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              className="usi-categoryrating-segmented-btn"
              style={{
                background: value === n ? category.color : 'transparent',
                color: value === n ? '#fff' : 'var(--usi-ink-3)',
              }}>{n}</button>
          ))}
        </div>
      );
    }
    if (variant === 'dots') {
      return (
        <div data-component="CategoryRating" className="usi-categoryrating-dots">
          {[1,2,3,4].map(n => (
            <button key={n} type="button" onClick={() => onChange(value === n ? null : n)}
              className="usi-categoryrating-dot-btn"
              style={{
                background: n <= value ? category.color : 'var(--usi-star-empty)',
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
      <div data-component="CategoryStripe" className="usi-categorystripe-container" style={{ height }}>
        {categories.map(cat => {
          const v = ratings[cat.key] || 0;
          return (
            <div key={cat.key} className="usi-categorystripe-segment">
              {v > 0 && (
                <div className="usi-categorystripe-fill"
                  style={{
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
      <div data-component="CategoryDots" className="usi-categorydots-container">
        {categories.map(cat => {
          const v = ratings[cat.key] || 0;
          return (
            <div key={cat.key} title={`${cat.key}: ${v || '—'}`}
              className="usi-categorydots-dot"
              style={{
                width: size, height: size,
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
      <img
        src="/assets/icons/star.svg"
        width={15}
        height={15}
        className="usi-usistarscore-star"
        alt="star"
        style={{ opacity, display: 'inline-block', verticalAlign: 'middle' }}
      />
    );
    return (
      <div data-component="UsiStarScore" className="usi-usistarscore-container">
        {Array.from({ length: nFull }).map((_, i) => <Star key={i} />)}
        {fracChar && (
          <>
            <Star opacity={0.3} />
            <span className="usi-usistarscore-frac">{fracChar}</span>
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
      <div data-component="WeightedUsiScore" className="usi-weightedscore-container">
        <div className="usi-weightedscore-badge" style={{ width: size, height: size }}>
          <img 
            src={score < 0.5 ? '/assets/usi-zero-white.svg' : '/assets/usi-star-white.svg'} 
            width={size * 0.55} height={size * 0.55} 
            alt="USI"
          />
        </div>
        <div className="usi-weightedscore-info">
          <div className="usi-weightedscore-value" style={{ fontSize: size * 0.55 }}>
            {nFull}{fracChar && <span style={{ fontSize: '0.65em', verticalAlign: 'top', marginLeft: 1 }}>{fracChar}</span>}
            <span className="usi-weightedscore-max">/ 4</span>
          </div>
          <div className="usi-weightedscore-label">Ważona USI</div>
        </div>
      </div>
    );
  };
  usiRegister('WeightedUsiScore', WeightedUsiScore);

})();

