// Loading.jsx — komponenty ładowania i spinnera

function Spinner({ size = 40, stroke = 3 }) {
  return (
    <div data-component="Spinner">
      <div className="usi-spinner" style={{ width: size, height: size, borderWidth: stroke }} />
    </div>
  );
}
window.usiRegister('Spinner', Spinner);

function LoadingScreen() {
  const { React } = window;
  return (
    <div data-component="LoadingScreen" style={{ 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100%',
      gap: 16
    }}>
      <Spinner />
      <div style={{ color: 'var(--usi-ink-3)', fontSize: 13, fontWeight: 500 }}>Ładowanie danych...</div>
    </div>
  );
}
window.usiRegister('LoadingScreen', LoadingScreen);
