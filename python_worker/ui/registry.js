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

  // ─── Module Registry (Krok B03/B04) ─────────────────────────────────────
  win.ModuleRegistry = {
    _modules: {},
    _presets: {},
    register(name, definition, spec = null) {
      if (this._modules[name]) {
        console.warn(`[ModuleRegistry] Overwriting module: ${name}`);
      }
      if (spec) definition.__spec = spec;
      this._modules[name] = definition;
      return definition;
    },
    get(name) {
      if (!this._modules[name]) {
        console.warn(`[ModuleRegistry] Module not found: ${name}`);
        return null;
      }
      return this._modules[name];
    },
    list() {
      return Object.keys(this._modules);
    },
    registerPreset(name, config) {
      this._presets[name] = config;
      return config;
    },
    getPreset(name) {
      return this._presets[name] || null;
    }
  };

})(window);
