/**
 * registry.js — USI Tracker Component Registry
 * Provides a formal way to register and retrieve components/hooks
 * to avoid race conditions in Babel Standalone environment.
 */

(function(win) {
  const registry = {};

  win.usiRegister = function(name, definition) {
    if (registry[name]) {
      console.warn(`[usiRegister] Overwriting existing registration: ${name}`);
    }
    
    // Attach to registry and window for backward compatibility
    registry[name] = definition;
    win[name] = definition;
    
    return definition;
  };

  win.usiGet = function(name) {
    if (!registry[name]) {
      console.error(`[usiGet] Component/Hook not found: ${name}`);
      return null;
    }
    return registry[name];
  };

  // Diagnostic helper
  win.usiInspectRegistry = function() {
    return Object.keys(registry);
  };

})(window);
