/**
 * USI Tracker - Visual Baseline Capture Tool
 * Exposes window.captureVisualBaseline() for snapshotting component styles.
 */

window.captureVisualBaseline = function captureVisualBaseline() {
    const components = document.querySelectorAll('[data-component]');
    const baseline = {};
    const theme = document.body.classList.contains('usi-theme-dark') ? 'dark' : 'light';

    console.log(`📸 Capturing baseline for ${components.length} components in ${theme} mode...`);

    components.forEach((el, index) => {
        const name = el.getAttribute('data-component');
        const id = `${name}_${index}`; // Handle multiple instances
        
        const style = window.getComputedStyle(el);
        const rect = el.getBoundingClientRect();

        baseline[id] = {
            component: name,
            theme: theme,
            styles: {
                display: style.display,
                position: style.position,
                flexDirection: style.flexDirection,
                gap: style.gap,
                padding: style.padding,
                margin: style.margin,
                background: style.background,
                color: style.color,
                fontSize: style.fontSize,
                fontWeight: style.fontWeight,
                borderRadius: style.borderRadius,
                border: style.border,
                boxShadow: style.boxShadow,
                width: rect.width + 'px',
                height: rect.height + 'px'
            }
        };
    });

    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(baseline, null, 2));
    const downloadAnchorNode = document.createElement('a');
    downloadAnchorNode.setAttribute("href", dataStr);
    downloadAnchorNode.setAttribute("download", `usi_baseline_${theme}.json`);
    document.body.appendChild(downloadAnchorNode);
    downloadAnchorNode.click();
    downloadAnchorNode.remove();

    console.log("✅ Baseline exported!");
    return baseline;
};
