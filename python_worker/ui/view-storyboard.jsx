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

    const [activeStory, setActiveStory] = React.useState(STORY_KEYS[0]);
    const story = STORIES[activeStory];

    const TargetComp = registeredComps[story.component];

    return (
      <div data-component="ViewStoryboard" className="usi-flex-row" style={{ height: 'calc(100vh - 120px)' }}>
        {/* Navigation panel */}
        <aside style={{ width: 240, borderRight: '1.5px solid var(--usi-border)', background: 'var(--usi-surface-2)', padding: '16px 0', overflowY: 'auto' }}>
          <div className="usi-tiny" style={{ padding: '0 16px', marginBottom: 12, fontWeight: 700, opacity: 0.6 }}>STORIES</div>
          {STORY_KEYS.map(key => (
            <button
              key={key}
              onClick={() => setActiveStory(key)}
              style={{
                width: '100%', padding: '10px 16px', border: 'none', background: key === activeStory ? 'var(--usi-accent-10)' : 'transparent',
                color: key === activeStory ? 'var(--usi-accent)' : 'var(--usi-ink)', textAlign: 'left', cursor: 'pointer',
                fontSize: 13, fontWeight: key === activeStory ? 700 : 500, display: 'flex', alignItems: 'center', gap: 10
              }}
            >
              <div style={{ width: 4, height: 4, borderRadius: '50%', background: key === activeStory ? 'var(--usi-accent)' : 'var(--usi-border-strong)' }} />
              {key}
            </button>
          ))}
        </aside>

        {/* Content panel */}
        <main style={{ flex: 1, padding: 40, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: 'var(--usi-surface-3)', overflowY: 'auto', position: 'relative' }}>
          <div style={{ position: 'absolute', top: 20, right: 20, textAlign: 'right' }}>
            <h2 className="usi-h2" style={{ margin: 0 }}>{activeStory}</h2>
            <div className="usi-tiny" style={{ opacity: 0.6 }}>Isolated Mode (Mock Data)</div>
          </div>

          <div 
            style={{ 
              padding: 40, background: 'var(--usi-surface)', borderRadius: 12, border: '1px dashed var(--usi-border-strong)',
              boxShadow: 'var(--usi-shadow-sm)', maxWidth: '100%', minWidth: 200, display: 'flex', justifyContent: 'center' 
            }}
          >
            <ModuleErrorBoundary>
              {TargetComp ? <TargetComp {...story.props} /> : <div>Component <b>{story.component}</b> not found in registry.</div>}
            </ModuleErrorBoundary>
          </div>
          
          <div style={{ marginTop: 40, width: '100%', maxWidth: 600 }}>
             <h4 className="usi-tiny" style={{ fontWeight: 700, opacity: 0.6, marginBottom: 8 }}>MOCK PROPS (JSON)</h4>
             <pre style={{ 
               padding: 16, background: 'var(--usi-surface-2)', borderRadius: 8, fontSize: 11, border: '.5px solid var(--usi-border)',
               color: 'var(--usi-ink-2)', overflow: 'auto'
             }}>
               {JSON.stringify(story.props, null, 2)}
             </pre>
          </div>
        </main>
      </div>
    );
  };

  usiRegister('ViewStoryboard', UIStoryboard);
})();
