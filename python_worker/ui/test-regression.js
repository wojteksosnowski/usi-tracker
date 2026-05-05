/**
 * USI Tracker - Visual Regression Test Tool
 * Compares current computed styles with the baseline from Krok B01.
 */

window.runVisualRegressionTest = async function runVisualRegressionTest(baselineFile = 'usi_baseline_light.json') {
    console.log(`🧪 Starting Visual Regression Test against ${baselineFile}...`);
    
    try {
        const response = await fetch(`/ui/${baselineFile}`);
        if (!response.ok) throw new Error("Baseline file not found. Place it in python_worker/ui/");
        const baseline = await response.json();
        
        const currentElements = document.querySelectorAll('[data-component]');
        const report = {
            matches: 0,
            mismatches: 0,
            missing: 0,
            details: []
        };

        const componentsByBaselineId = baseline;

        Object.keys(baseline).forEach(id => {
            const base = baseline[id];
            const name = base.component;
            
            // Find current element by data-component and approximate index
            const elements = document.querySelectorAll(`[data-component="${name}"]`);
            // This is a naive matching by index as recorded in capture-tool.js
            const index = parseInt(id.split('_')[1]);
            const el = elements[index];

            if (!el) {
                report.missing++;
                report.details.push({ component: name, id, status: 'MISSING' });
                return;
            }

            const currentStyle = window.getComputedStyle(el);
            const diffs = {};
            let hasDiff = false;

            Object.keys(base.styles).forEach(prop => {
                const baseVal = base.styles[prop];
                const currVal = currentStyle[prop];
                
                // Simplified comparison (strings might differ slightly due to browser normalization)
                if (baseVal !== currVal) {
                    // Check if it's just a hex vs rgb difference or similar
                    diffs[prop] = { baseline: baseVal, current: currVal };
                    hasDiff = true;
                }
            });

            if (hasDiff) {
                report.mismatches++;
                report.details.push({ component: name, id, status: 'MISMATCH', diffs });
            } else {
                report.matches++;
            }
        });

        console.table(report.details.filter(d => d.status === 'MISMATCH').map(d => ({
            Component: d.component,
            Prop: Object.keys(d.diffs).join(', '),
            Baseline: Object.values(d.diffs).map(v => v.baseline).join(' | '),
            Current: Object.values(d.diffs).map(v => v.current).join(' | ')
        })));

        console.log(`📊 Test Results: ${report.matches} matches, ${report.mismatches} mismatches, ${report.missing} missing.`);
        return report;
    } catch (err) {
        console.error("❌ Test failed:", err);
    }
};

/**
 * runDataIntegrityTest - Stress tests components with broken/empty data.
 */
window.runDataIntegrityTest = function runDataIntegrityTest() {
    const { React, ReactDOM, ListCard, HeroBand } = window;
    console.log("🧪 Starting Data Integrity Stress Test...");

    const testContainer = document.createElement('div');
    testContainer.style.display = 'none';
    document.body.appendChild(testContainer);

    const testCases = [
        { name: "ListCard with empty object", component: ListCard, props: { inv: {} } },
        { name: "ListCard with null inv", component: ListCard, props: { inv: null } },
        { name: "HeroBand with broken numbers", component: HeroBand, props: { inv: { price_avg: "BŁĄD", coords: [] } } },
        { 
          name: "DataBoundary Sanitization", 
          component: function TestDB() {
            const { DataBoundary } = window;
            return React.createElement(DataBoundary, { data: { name: 123, photos: null } }, (valid) => {
                if (typeof valid.name !== 'string' || valid.name !== '123') throw new Error("Name not converted to string");
                if (!Array.isArray(valid.photos)) throw new Error("Photos not converted to array");
                return React.createElement('div', null, "OK");
            });
          }, 
          props: {} 
        },
        {
          name: "Deep Nesting (Ratings)",
          component: function TestRatings() {
            const { DataBoundary } = window;
            return React.createElement(DataBoundary, { data: { ratings: null } }, (valid) => {
                if (typeof valid.ratings !== 'object' || valid.ratings === null) throw new Error("Ratings not converted to object");
                return React.createElement('div', null, "OK");
            });
          },
          props: {}
        }
    ];

    const results = [];

    testCases.forEach(tc => {
        try {
            // Using a new root or rendering into a detached node to catch React errors
            ReactDOM.render(React.createElement(tc.component, tc.props), testContainer);
            results.push({ name: tc.name, status: 'PASS' });
            console.log(`✅ ${tc.name}: PASS`);
        } catch (err) {
            results.push({ name: tc.name, status: 'FAIL', error: err.message });
            console.error(`❌ ${tc.name}: FAIL`, err);
        }
    });

    // Cleanup
    ReactDOM.unmountComponentAtNode(testContainer);
    document.body.removeChild(testContainer);

    console.table(results);
    return results;
};

