// Gallery.jsx — Photo components (Gallery, SlideShow, Lightbox, PhotoTile)

(function() {
  const { React, ReactDOM, usiRegister, Icon } = window;

  const DeletionBadge = ({ zIndex }) => (
    <div data-component="DeletionBadge" 
      className="usi-gallery-deletion-badge"
      style={zIndex != null ? { zIndex } : {}}>
      <Icon name="trash" size={11} /> Do usunięcia
    </div>
  );
  usiRegister('DeletionBadge', DeletionBadge);

  const PhotoOverlay = ({ onOpen, onToggleMark, marked, visible, zIndex }) => (
    <div data-component="PhotoOverlay" 
      className="usi-gallery-photo-overlay"
      style={{
        opacity: visible ? 1 : 0.55,
        ...(zIndex != null ? { zIndex } : {}),
      }}>
      <button onClick={e => { e.stopPropagation(); onOpen(); }} title="Podgląd" 
        className="usi-gallery-tile-btn">
        <Icon name="eye" size={13} />
      </button>
      <button onClick={e => { e.stopPropagation(); onToggleMark(); }}
        title={marked ? 'Cofnij oznaczenie' : 'Oznacz do usunięcia'}
        className={`usi-gallery-tile-btn ${marked ? 'active' : ''}`}>
        <Icon name={marked ? 'undo' : 'trash'} size={13} />
      </button>
    </div>
  );
  usiRegister('PhotoOverlay', PhotoOverlay);

  const PhotoTile = ({ src, marked, onMark, onOpen, ratio = '4/3', hero = false }) => {
    const [hover, setHover] = React.useState(false);
    return (
      <div data-component="PhotoTile"
        onMouseEnter={() => setHover(true)}
        onMouseLeave={() => setHover(false)}
        className={`usi-gallery-photo-tile ${marked ? 'marked' : ''}`}
        style={{
          aspectRatio: ratio, 
          borderRadius: hero ? 12 : 8,
        }}>
        <img src={src} alt="" loading="lazy"
          className={`usi-gallery-photo-img ${marked ? 'marked' : ''}`} />
        {marked && <DeletionBadge />}
        <PhotoOverlay onOpen={onOpen} onToggleMark={onMark} marked={marked} visible={hover || marked} />
        {!hero && (
          <button onClick={onMark} aria-label={marked ? 'Cofnij oznaczenie' : 'Oznacz do usunięcia'}
            className="usi-gallery-photo-clickable" />
        )}
      </div>
    );
  };
  usiRegister('PhotoTile', PhotoTile);

  const SlideShow = ({ photos = [], marked, onToggleMark, onLightbox, style: extraStyle = {} }) => {
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
        <div data-component="SlideShow" className="usi-slideshow-empty">
          <span className="usi-slideshow-empty-icon">📷</span>
          <span className="usi-small">Brak zdjęć</span>
        </div>
      );
    }

    const src = photos[idx];
    const isMrk = marked && marked.has(idx);

    return (
      <div data-component="SlideShow" className="usi-slideshow-container" style={extraStyle}>
        <img src={src} alt="" className="usi-slideshow-img" />

        <button className="usi-slideshow-nav-btn" 
          style={{ left: 12 }}
          disabled={idx === 0}
          onClick={() => setIdx(i => Math.max(0, i - 1))} title="Poprzednie">‹</button>
        <button className="usi-slideshow-nav-btn" 
          style={{ right: 12 }}
          disabled={idx === total - 1}
          onClick={() => setIdx(i => Math.min(total - 1, i + 1))} title="Następne">›</button>

        <PhotoOverlay onOpen={() => onLightbox && onLightbox(idx)}
          onToggleMark={() => onToggleMark && onToggleMark(idx)}
          marked={isMrk} visible={true} zIndex={2} />

        <div className="usi-slideshow-counter">
          {idx + 1} / {total}
        </div>

        {isMrk && <DeletionBadge zIndex={2} />}
      </div>
    );
  };
  usiRegister('SlideShow', SlideShow);

  const Gallery = ({ inv, columns = 4, marked, onToggleMark, onLightbox }) => {
    if (!inv.photos || inv.photos.length === 0) {
      return (
        <div data-component="Gallery" className="usi-gallery-empty">
          <span className="usi-gallery-empty-icon">📷</span>
          <span className="usi-small">Brak zdjęć</span>
        </div>
      );
    }
    const [hero, ...rest] = inv.photos;
    return (
      <div data-component="Gallery" className="usi-gallery-container">
        <PhotoTile src={hero} marked={marked.has(0)}
          onMark={() => onToggleMark(0)} onOpen={() => onLightbox(0)}
          ratio="16/9" hero />
        {rest.length > 0 && (
          <div className="usi-gallery-rest" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {rest.map((src, i) => (
              <PhotoTile key={i+1} src={src} marked={marked.has(i+1)}
                onMark={() => onToggleMark(i+1)} onOpen={() => onLightbox(i+1)}
                ratio="4/3" />
            ))}
          </div>
        )}
      </div>
    );
  };
  usiRegister('Gallery', Gallery);

  const Lightbox = ({ inv, index, onClose }) => {
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
      <div data-component="Lightbox" onClick={onClose} className="usi-lightbox-backdrop">
        <img src={inv.photos[i]} alt="" onClick={e => e.stopPropagation()}
          className="usi-lightbox-img" />
        <div className="usi-lightbox-counter">
          {i + 1} / {inv.photos.length}
        </div>
        <button onClick={onClose} className="usi-lightbox-close">
          <Icon name="close" />
        </button>
      </div>,
      document.body
    );
  };
  usiRegister('Lightbox', Lightbox);

})();
