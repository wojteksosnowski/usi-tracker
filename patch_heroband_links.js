const fs = require('fs');
const file = 'python_worker/ui/components/HeroBand.jsx';
let content = fs.readFileSync(file, 'utf8');
content = content.replace(
    /let links = \[\];[ \s\S]*?(?=return \()/m,
    `let links = [];
    if (inv.sources && Object.keys(inv.sources).length > 0) {
        links = Object.entries(inv.sources)
            .filter(([source, data]) => data && data.url)
            .map(([source, data]) => ({ source, url: data.url }));
    } 
    
    if (links.length === 0 && inv.source_links && inv.source_links.length > 0) {
        links = inv.source_links;
    } 
    
    if (links.length === 0 && inv.source && inv.source_url) {
        links = [{ source: inv.source, url: inv.source_url }];
    }
    
    `
);
fs.writeFileSync(file, content);
