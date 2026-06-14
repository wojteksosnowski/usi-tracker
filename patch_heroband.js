const fs = require('fs');
const file = 'python_worker/ui/components/HeroBand.jsx';
let content = fs.readFileSync(file, 'utf8');
content = content.replace(
    /let links = \[\];/,
    "let links = []; console.log('SourceLinks inv:', inv.usi_inv_id, 'sources:', inv.sources);"
);
fs.writeFileSync(file, content);
