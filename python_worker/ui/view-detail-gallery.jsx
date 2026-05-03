// view-detail-gallery.jsx — komponenty galerii: PhotoTile, SlideShow, Gallery, Lightbox

function tileBtn(active) {
  return {
    width: 28, height: 28, borderRadius: 6, border: 'none',
    background: active ? 'var(--usi-danger)' : 'rgba(0,0,0,0.55)',
    color: '#fff', cursor: 'pointer', backdropFilter: 'blur(6px)',
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 1, position: 'relative',
    boxShadow: active ? '0 2px 8px rgba(192,57,43,0.5)' : 'none',
  };
}

function DeletionBadge({ zIndex }) {
  const { Icon } = window;
  return (
    <div data-component="DeletionBadge" style={{
      position: 'absolute', top: 10, left: 10,
      background: 'var(--usi-danger)', color: '#fff',
      padding: '4px 8px', borderRadius: 4,
      fontSize: 10, fontWeight: 700, letterSpacing: '.06em',
      display: 'flex', alignItems: 'center', gap: 5,
      boxShadow: '0 4px 12px rgba(192,57,43,0.4)',
      textTransform: 'uppercase',
      ...(zIndex != null ? { zIndex } : {}),
    }}>
      <Icon name="trash" size={11} /> Do usunięcia
    </div>
  );
}

function PhotoOverlay({ onOpen, onToggleMark, marked, visible, zIndex }) {
  const { Icon } = window;
  return (
    <div data-component="PhotoOverlay" style={{
      position: 'absolute', top: 8, right: 8,
      display: 'flex', gap: 6,
      opacity: visible ? 1 : 0.55, transition: 'opacity .15s',
      ...(zIndex != null ? { zIndex } : {}),
    }}>
      <button onClick={e => { e.stopPropagation(); onOpen(); }} title="Podgląd" style={tileBtn(false)}>
        <Icon name="eye" size={13} />
      </button>
      <button onClick={e => { e.stopPropagation(); onToggleMark(); }}
        title={marked ? 'Cofnij oznaczenie' : 'Oznacz do usunięcia'}
        style={tileBtn(marked)}>
        <Icon name={marked ? 'undo' : 'trash'} size={13} />
      </button>
    </div>
  );
}

function PhotoTile({ src, marked, onMark, onOpen, ratio = '4/3', hero = false }) {
  const { React } = window;
  const [hover, setHover] = React.useState(false);
  return (
    <div data-component="PhotoTile"
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      style={{
        position: 'relative', aspectRatio: ratio, borderRadius: hero ? 12 : 8, overflow: 'hidden',
        background: 'var(--usi-surface-3)',
        border: marked ? '2px solid var(--usi-danger)' : '.5px solid var(--usi-border)',
        outline: marked ? '3px solid rgba(192,57,43,0.18)' : 'none',
        outlineOffset: marked ? -3 : 0,
        transition: 'border-color .15s, outline-color .15s',
      }}>
      <img src={src} alt="" loading="lazy"
        style={{
          width: '100%', height: '100%', objectFit: 'cover', display: 'block',
          filter: marked ? 'grayscale(.6) brightness(.65)' : 'none',
        }} />
      {marked && <DeletionBadge />}
      <PhotoOverlay onOpen={onOpen} onToggleMark={onMark} marked={marked} visible={hover || marked} />
      {!hero && (
        <button onClick={onMark} aria-label={marked ? 'Cofnij oznaczenie' : 'Oznacz do usunięcia'}
          style={{ position: 'absolute', inset: 0, background: 'transparent', border: 'none', cursor: 'pointer', zIndex: 0 }} />
      )}
    </div>
  );
}

function SlideShow({ photos = [], marked, onToggleMark, onLightbox, style: extraStyle = {} }) {
  const { React } = window;
  const [idx, setIdx] = React.useState(0);
  const total = photos.length;

  React.useEffect(() => { setIdx(0); }, [photos]);

  React.useEffect(() => {
    const handler = (e) => {
      if (e.key === 'ArrowLeft')  { e.stopPropagation(); setIdx(i => Math.max(0, i - 1)); }
      if (e.key === 'ArrowRight') { e.stopPropagation(); setIdx(i => Math.min(total - 1, i + 1)); }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [total]);

  if (total === 0) {
    return (
      <div data-component="SlideShow" style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 8, color: 'var(--usi-ink-4)' }}>
        <span style={{ fontSize: 40 }}>📷</span>
        <span className="usi-small">Brak zdjęć</span>
      </div>
    );
  }

  const src = photos[idx];
  const isMrk = marked && marked.has(idx);

  const navBtn = (dir) => ({
    position: 'absolute', top: '50%', transform: 'translateY(-50%)',
    [dir === 'left' ? 'left' : 'right']: 12,
    width: 40, height: 40, borderRadius: '50%', border: 'none',
    background: 'rgba(0,0,0,0.45)', color: '#fff', cursor: 'pointer',
    backdropFilter: 'blur(6px)', display: 'flex', alignItems: 'center', justifyContent: 'center',
    zIndex: 2, fontSize: 18, fontWeight: 600,
    opacity: (dir === 'left' && idx === 0) || (dir === 'right' && idx === total - 1) ? 0.25 : 1,
    pointerEvents: (dir === 'left' && idx === 0) || (dir === 'right' && idx === total - 1) ? 'none' : 'auto',
  });

  return (
    <div data-component="SlideShow" style={{ flex: 1, position: 'relative', overflow: 'hidden', background: 'var(--usi-bg)', ...extraStyle }}>
      <img src={src} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />

      <button style={navBtn('left')} onClick={() => setIdx(i => Math.max(0, i - 1))} title="Poprzednie">‹</button>
      <button style={navBtn('right')} onClick={() => setIdx(i => Math.min(total - 1, i + 1))} title="Następne">›</button>

      <PhotoOverlay onOpen={() => onLightbox && onLightbox(idx)}
        onToggleMark={() => onToggleMark && onToggleMark(idx)}
        marked={isMrk} visible={true} zIndex={2} />

      <div style={{
        position: 'absolute', bottom: 12, left: '50%', transform: 'translateX(-50%)',
        background: 'rgba(0,0,0,0.5)', color: '#fff',
        padding: '3px 12px', borderRadius: 999, fontSize: 12, backdropFilter: 'blur(6px)',
        zIndex: 2,
      }}>
        {idx + 1} / {total}
      </div>

      {isMrk && <DeletionBadge zIndex={2} />}
    </div>
  );
}

function Gallery({ inv, columns = 4, marked, onToggleMark, onLightbox }) {
  if (!inv.photos || inv.photos.length === 0) {
    return (
      <div data-component="Gallery" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200, color: 'var(--usi-ink-4)', flexDirection: 'column', gap: 8 }}>
        <span style={{ fontSize: 32 }}>📷</span>
        <span className="usi-small">Brak zdjęć</span>
      </div>
    );
  }
  const [hero, ...rest] = inv.photos;
  return (
    <div data-component="Gallery" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <PhotoTile src={hero} marked={marked.has(0)}
        onMark={() => onToggleMark(0)} onOpen={() => onLightbox(0)}
        ratio="16/9" hero />
      {rest.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: `repeat(${columns}, 1fr)`, gap: 8 }}>
          {rest.map((src, i) => (
            <PhotoTile key={i+1} src={src} marked={marked.has(i+1)}
              onMark={() => onToggleMark(i+1)} onOpen={() => onLightbox(i+1)}
              ratio="4/3" />
          ))}
        </div>
      )}
    </div>
  );
}

function Lightbox({ inv, index, onClose }) {
  const { React, ReactDOM, Icon } = window;
  const [i, setI] = React.useState(index);
  React.useEffect(() => {
    const k = (e) => {
      if (e.key === 'Escape') { e.stopPropagation(); onClose(); }
      if (e.key === 'ArrowLeft') { e.stopPropagation(); setI(p => Math.max(0, p - 1)); }
      if (e.key === 'ArrowRight') { e.stopPropagation(); setI(p => Math.min(inv.photos.length - 1, p + 1)); }
    };
    document.addEventListener('keydown', k, true);
    return () => document.removeEventListener('keydown', k, true);
  }, [inv.photos.length, onClose]);
  return ReactDOM.createPortal(
    <div data-component="Lightbox" onClick={onClose} style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.85)',
      zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center',
      backdropFilter: 'blur(8px)',
    }}>
      <img src={inv.photos[i]} alt="" onClick={e => e.stopPropagation()}
        style={{ maxWidth: '90vw', maxHeight: '90vh', borderRadius: 8, boxShadow: '0 20px 60px rgba(0,0,0,0.6)' }} />
      <div style={{ position: 'absolute', bottom: 24, left: '50%', transform: 'translateX(-50%)', color: '#fff', fontSize: 13 }}>
        {i + 1} / {inv.photos.length}
      </div>
      <button onClick={onClose} style={{
        position: 'absolute', top: 20, right: 20,
        background: 'rgba(255,255,255,0.1)', color: '#fff', border: 'none',
        width: 36, height: 36, borderRadius: 18, cursor: 'pointer',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        <Icon name="close" />
      </button>
    </div>,
    document.body
  );
}

Object.assign(window, { PhotoTile, SlideShow, Gallery, Lightbox });
