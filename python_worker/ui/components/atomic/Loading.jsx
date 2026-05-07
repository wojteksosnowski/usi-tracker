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
    <div data-component="LoadingScreen" className="usi-loading-screen">
      <Spinner />
      <div className="usi-loading-text">Ładowanie danych...</div>
    </div>
  );
}
window.usiRegister('LoadingScreen', LoadingScreen);
