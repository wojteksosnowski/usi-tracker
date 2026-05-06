// view-storyboard.jsx — Isolated testing environment for USI components

(function() {
  const { React, usiRegister } = window;

  const STORIES = {
    'Atomic/Icon': {
      component: 'Icon',
      props: { name: 'sparkle', size: 64, color: 'var(--usi-accent)' }
    },
    'Atomic/Loading': {
      component: 'Loading',
      props: { text: 'Wczytywanie makiety...' }
    },
    'Views/ListCard': {
      component: 'ListCard',
      props: {
        inv: { 
          name: 'Osiedle Testowe', 
          developer: 'Test Dev', 
          district: 'Warszawa', 
          price_avg: 12500, 
          photos: [],
          image: null,
          ratings: { USI: 4.5 }
        }
      }
    },
    'Atomic/ProgressRing': {
      component: 'ProgressRing',
      props: { value: 75, max: 100, size: 64, stroke: 6 }
    }
  };

  const STORY_KEYS = Object.keys(STORIES);

  const UIStoryboard = () => {
    const { 
      Icon, ModuleErrorBoundary, DataBoundary, 
      ...registeredComps 
    } = window;

    const [activeStoryKey, setActiveStoryKey] = React.useState(STORY_KEYS[0]);
    const [currentProps, setCurrentProps] = React.useState(STORIES[STORY_KEYS[0]].props);

    React.useEffect(() => {
      setCurrentProps(STORIES[activeStoryKey].props);
    }, [activeStoryKey]);

    const story = STORIES[activeStoryKey];
    const TargetComp = registeredComps[story.component];

    const updateProp = (path, val) => {
      setCurrentProps(prev => {
        const next = { ...prev };
        const keys = path.split('.');
        let cur = next;
        for (let i = 0; i < keys.length - 1; i++) {
          cur[keys[i]] = { ...cur[keys[i]] };
          cur = cur[keys[i]];
        }
        cur[keys[keys.length - 1]] = val;
        return next;
      });
    };

    return (
      <div data-component="ViewStoryboard" className="usi-flex-row" style={{ height: 'calc(100vh - 120px)' }}>
        {/* Navigation panel */}
        <aside style={{ width: 240, borderRight: '1.5px solid var(--usi-border)', background: 'var(--usi-surface-2)', padding: '16px 0', overflowY: 'auto' }}>
          <div className="usi-tiny" style={{ padding: '0 16px', marginBottom: 12, fontWeight: 700, opacity: 0.6 }}>STORIES</div>
          {STORY_KEYS.map(key => (
            <button
              key={key}
              onClick={() => setActiveStoryKey(key)}
              style={{
                width: '100%', padding: '10px 16px', border: 'none', background: key === activeStoryKey ? 'var(--usi-accent-10)' : 'transparent',
                color: key === activeStoryKey ? 'var(--usi-accent)' : 'var(--usi-ink)', textAlign: 'left', cursor: 'pointer',
                fontSize: 13, fontWeight: key === activeStoryKey ? 700 : 500, display: 'flex', alignItems: 'center', gap: 10
              }}
            >
              <div style={{ width: 4, height: 4, borderRadius: '50%', background: key === activeStoryKey ? 'var(--usi-accent)' : 'var(--usi-border-strong)' }} />
              {key}
            </button>
          ))}
        </aside>

        {/* Content panel */}
        <main style={{ flex: 1, padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--usi-surface-3)', overflowY: 'auto', position: 'relative' }}>
          <div style={{ position: 'absolute', top: 20, right: 20, textAlign: 'right' }}>
            <h2 className="usi-h2" style={{ margin: 0 }}>{activeStoryKey}</h2>
            <div className="usi-tiny" style={{ opacity: 0.6 }}>Isolated Mode (Mock Data)</div>
          </div>

          <div 
            style={{ 
              padding: 40, background: 'var(--usi-surface)', borderRadius: 12, border: '1px dashed var(--usi-border-strong)',
              boxShadow: 'var(--usi-shadow-sm)', maxWidth: '100%', minWidth: 200, display: 'flex', justifyContent: 'center' 
            }}
          >
            <ModuleErrorBoundary>
              {TargetComp ? <TargetComp {...currentProps} /> : <div>Component <b>{story.component}</b> not found in registry.</div>}
            </ModuleErrorBoundary>
          </div>
          
          <div style={{ marginTop: 40, width: '100%', maxWidth: 600, display: 'flex', gap: 20 }}>
             <div style={{ flex: 1 }}>
               <h4 className="usi-tiny" style={{ fontWeight: 700, opacity: 0.6, marginBottom: 8 }}>KNOBS</h4>
               <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                 {Object.keys(currentProps).map(key => {
                   const val = currentProps[key];
                   if (typeof val === 'string' || typeof val === 'number') {
                     return (
                       <div key={key} className="usi-flex-row usi-gap-8" style={{ alignItems: 'center' }}>
                         <span className="usi-small usi-w-100" style={{ fontWeight: 600 }}>{key}</span>
                         <input 
                           className="usi-input sm" 
                           value={val} 
                           onChange={e => updateProp(key, typeof val === 'number' ? Number(e.target.value) : e.target.value)} 
                         />
                       </div>
                     );
                   }
                   return null;
                 })}
               </div>
             </div>
             <div style={{ flex: 1 }}>
                <h4 className="usi-tiny" style={{ fontWeight: 700, opacity: 0.6, marginBottom: 8 }}>RAW PROPS</h4>
                <pre style={{ 
                  padding: 16, background: 'var(--usi-surface-2)', borderRadius: 8, fontSize: 10, border: '.5px solid var(--usi-border)',
                  color: 'var(--usi-ink-3)', overflow: 'auto', maxHeight: 200
                }}>
                  {JSON.stringify(currentProps, null, 2)}
                </pre>
             </div>
          </div>
        </main>
      </div>
    );
  };

  usiRegister('ViewStoryboard', UIStoryboard);
})();
