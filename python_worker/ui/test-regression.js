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
