const inv = {
  "sources": {
    "rp": {
      "id": "14103",
      "url": "https://rynekpierwotny.pl/oferty/mill-yon-sp-z-oo/aura-vita-ii-pruszkow-14103/",
      "vendor_id": "801"
    }
  },
  "source_links": [
    {
      "source": "RP",
      "url": "https://rynekpierwotny.pl/oferty/mill-yon-sp-z-oo/aura-vita-ii-pruszkow-14103/"
    }
  ],
  "source": "RP",
  "source_url": "https://rynekpierwotny.pl/oferty/mill-yon-sp-z-oo/aura-vita-ii-pruszkow-14103/"
};

let links = [];
if (inv.sources) {
    console.log("Using sources");
    links = Object.entries(inv.sources).map(([source, data]) => ({ source, url: data.url }));
} else if (inv.source_links) {
    console.log("Using source_links");
    links = inv.source_links;
} else if (inv.source && inv.source_url) {
    console.log("Using source_url");
    links = [{ source: inv.source, url: inv.source_url }];
}

console.log(links);
