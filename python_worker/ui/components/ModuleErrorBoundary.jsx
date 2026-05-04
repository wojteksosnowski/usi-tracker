// ModuleErrorBoundary.jsx — Error Boundary for modular UI components

class ModuleErrorBoundary extends window.React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  static getDerivedStateFromError(error) { return { hasError: true, error }; }
  componentDidCatch(error, errorInfo) {
    console.error("Module Error:", error, errorInfo);
    fetch('/api/ui-error', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: 'Module Error: ' + (error?.message || 'Unknown'),
        stack: error?.stack || 'no stack',
        componentStack: errorInfo?.componentStack,
        url: window.location.href
      })
    }).catch(err => console.log('Failed to report module error:', err));
  }
  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div style={{ padding: 16, border: '1px dashed var(--usi-danger)', borderRadius: 12, backgroundColor: 'var(--usi-surface-2)', color: 'var(--usi-danger)', fontSize: 13, display: 'flex', flexDirection: 'column', gap: 8 }}>
          <strong>Moduł niedostępny</strong>
          <span style={{ fontSize: 11, opacity: 0.8, fontFamily: 'monospace' }}>{this.state.error?.message || 'Błąd renderowania'}</span>
        </div>
      );
    }
    return this.props.children;
  }
}
window.usiRegister('ModuleErrorBoundary', ModuleErrorBoundary);
