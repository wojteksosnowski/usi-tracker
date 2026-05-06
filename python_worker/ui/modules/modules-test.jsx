// modules-test.jsx — Lekki framework testowy dla logiki frontendowej

(function() {
  const { React, usiRegister, useDataBus } = window;

  const results = [];
  const suites = [];

  const TestSuite = {
    describe: (name, fn) => {
      suites.push({ name, fn });
    },
    run: async () => {
      results.length = 0;
      for (const suite of suites) {
        console.group(`[TestSuite] ${suite.name}`);
        const suiteResults = [];
        
        const test = async (testName, testFn) => {
          try {
            await testFn();
            suiteResults.push({ name: testName, status: 'pass' });
            console.log(`✅ ${testName}`);
          } catch (err) {
            suiteResults.push({ name: testName, status: 'fail', error: err.message });
            console.error(`❌ ${testName}: ${err.message}`);
          }
        };

        const expect = (actual) => ({
          toBe: (expected) => {
            if (actual !== expected) throw new Error(`Oczekiwano ${expected}, otrzymano ${actual}`);
          },
          toEqual: (expected) => {
            if (JSON.stringify(actual) !== JSON.stringify(expected)) {
              throw new Error(`Oczekiwano ${JSON.stringify(expected)}, otrzymano ${JSON.stringify(actual)}`);
            }
          },
          toBeTruthy: () => {
            if (!actual) throw new Error(`Oczekiwano wartości prawidziwej, otrzymano ${actual}`);
          },
          toBeFalsy: () => {
            if (actual) throw new Error(`Oczekiwano wartości fałszywej, otrzymano ${actual}`);
          }
        });

        // Inject into global for the duration of suite execution
        window.test = test;
        window.expect = expect;
        
        await suite.fn();
        
        // Cleanup globals
        delete window.test;
        delete window.expect;

        results.push({ name: suite.name, tests: suiteResults });
        console.groupEnd();
      }
      
      const hasFailures = results.some(s => s.tests.some(t => t.status === 'fail'));
      if (window.useDataBus) {
        const { setVariable } = window.useDataBus();
        setVariable('appStatus', { 
          type: hasFailures ? 'error' : 'success', 
          msg: hasFailures ? 'Błąd testów JS!' : 'Testy JS: OK' 
        });
        setVariable('testResults', results);
      }
      return results;
    }
  };

  usiRegister('TestSuite', TestSuite);

  /**
   * useRenderTracker - Hook for quantifying component renders during development.
   * Logs only when localStorage.getItem('USI_DEBUG_RENDER') === 'true'.
   */
  function useRenderTracker(name) {
    const { React } = window;
    const renderCount = React.useRef(0);
    renderCount.current++;

    React.useEffect(() => {
      if (localStorage.getItem('USI_DEBUG_RENDER') === 'true') {
        console.log(`[RenderTracker] ${name} render #${renderCount.current}`);
      }
    });
  }
  window.useRenderTracker = useRenderTracker;
  usiRegister('useRenderTracker', useRenderTracker);

  // ─── Initial Tests ───
  TestSuite.describe('Logika ocen', () => {
    const { ocenaLog, avgRating, ratedCount } = window;
    
    test('ratedCount dla pustego obiektu', () => {
      expect(ratedCount({})).toBe(0);
    });

    test('avgRating dla kompletu ocen', () => {
      const inv = { ratings: { 'Balkony': 4, 'Fasady': 4, 'Wnętrza': 4, 'Teren': 4, 'Mieszkania': 4, 'Udogodnienia': 4 } };
      expect(avgRating(inv)).toBe(4);
    });

    test('ocenaLog (log-mean-exp) dla skrajnych wartości', () => {
      const inv = { ratings: { 'Balkony': 4, 'Fasady': 0 } };
      const score = ocenaLog(inv);
      expect(score > 0 && score < 4).toBeTruthy();
    });
  });

})();
