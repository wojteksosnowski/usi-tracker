const fs = require('fs');
const file = 'python_worker/ui/modules/modules-ui.jsx';
let content = fs.readFileSync(file, 'utf8');

// Replace the header to add the refresh button
content = content.replace(
    /<div className="usi-h3">W okolicy<\/div>\s*<Icon name="map-pin" size=\{16\} className="usi-ink-4" \/>\s*<\/div>/,
    `<div className="usi-flex-row align-center usi-gap-8">
            <div className="usi-h3">W okolicy</div>
            <button 
              className="usi-btn ghost icon-only sm" 
              title="Odśwież skanowanie okolicy"
              onClick={(e) => {
                e.stopPropagation();
                if (window.fetch && inv.usi_inv_id) {
                    window.fetch(\`/api/investment/\${inv.usi_inv_id}/recalc-nearby\`, { method: 'POST' })
                      .then(res => res.json())
                      .then(data => {
                          if (data.nearby_investments) {
                              setNearby(data.nearby_investments);
                          }
                      })
                      .catch(err => console.error(err));
                }
              }}
            >
              <Icon name="refresh" size={14} />
            </button>
          </div>
          <Icon name="map-pin" size={16} className="usi-ink-4" />
        </div>`
);

fs.writeFileSync(file, content);
console.log("Patch applied!");
