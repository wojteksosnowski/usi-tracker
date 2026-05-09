// Icon.jsx — atomowy komponent ikon wykorzystujący zasoby zewnętrzne

function Icon({ name, size = 16, className = "" }) {
  const { React } = window;
  // Mapowanie nazw na pliki (obsługa aliasów jeśli potrzebne)
  const iconName = name || 'info';
  const src = `/assets/icons/${iconName}.svg`;

  return (
    <img
      data-component="Icon"
      src={src}
      width={size}
      height={size}
      className={`usi-icon ${className}`}
      alt={iconName}
      style={{
        display: 'inline-block',
        verticalAlign: 'middle',
        flexShrink: 0
      }}
      onError={(e) => {
        // Fallback dla brakujących ikon
        e.target.src = '/assets/icons/info.svg';
      }}
    />
  );
}
window.usiRegister('Icon', Icon);
