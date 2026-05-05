// modules-charts.jsx — Analytics and Chart modules

(function() {
  const { React, usiRegister, useModuleContext, BaseModule } = window;

  function PriceTrendModule({ data: localData, chartColor = '#3989C6', tension = 0.3, title = "Trend Inwestycji" }) {
    const canvasRef = React.useRef(null);
    const chartRef = React.useRef(null);
    const { aggregateByQuarter } = useModuleContext(localData);

    React.useEffect(() => {
      if (!canvasRef.current || !window.Chart) return;
      
      const ctx = canvasRef.current.getContext('2d');
      if (chartRef.current) chartRef.current.destroy();

      const labels = aggregateByQuarter.map(d => d.quarter);
      const dataset = aggregateByQuarter.map(d => d.flats);

      chartRef.current = new window.Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [{
            label: 'Liczba mieszkań',
            data: dataset,
            borderColor: chartColor,
            backgroundColor: chartColor + '33',
            tension: tension,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: chartColor
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: { mode: 'index', intersect: false }
          },
          scales: {
            y: { beginAtZero: true, grid: { color: 'rgba(0,0,0,0.05)', drawBorder: false }, ticks: { font: { size: 10 } } },
            x: { grid: { display: false }, ticks: { font: { size: 10 } } }
          }
        }
      });

      return () => { if (chartRef.current) chartRef.current.destroy(); };
    }, [aggregateByQuarter, chartColor, tension]);

    return (
      <BaseModule title={title} icon="trending-up">
        {aggregateByQuarter.length === 0 ? (
          <div className="usi-small" style={{ color: 'var(--usi-ink-4)', padding: '20px 0', textAlign: 'center' }}>
            Brak danych do wygenerowania wykresu trendów.
          </div>
        ) : (
          <div style={{ height: 200, width: '100%', padding: '10px 0' }}>
            <canvas ref={canvasRef} />
          </div>
        )}
      </BaseModule>
    );
  }
  PriceTrendModule.__spec = {
    props: {
      title: { type: 'String', label: 'Tytuł modułu', default: 'Trend Inwestycji' },
      chartColor: { type: 'Color', label: 'Kolor wykresu', default: '#3989C6' },
      tension: { type: 'Number', label: 'Zaokrąglenie linii', default: 0.3 }
    }
  };
  window.ModuleRegistry.register('PriceTrendModule', PriceTrendModule, PriceTrendModule.__spec);
  usiRegister('PriceTrendModule', PriceTrendModule);

})();
