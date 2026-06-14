const USI_INVESTMENT_SCHEMA = {
  name: { type: 'string', fallback: 'Bez nazwy' },
  source: { type: 'string', fallback: '?' },
  source_url: { type: 'string', fallback: '' },
  source_links: { type: 'array', fallback: [] }
};
function validateData(raw, schema) {
  const result = {};
  Object.entries(schema).forEach(([key, spec]) => {
      let val = raw[key];
      if (val === undefined || val === null) val = spec.fallback;
      result[key] = val;
  });
  return { ...raw, ...result };
}

const raw = {
  id: "INV-32833",
  sources: {
    rp: {
      id: "14103",
      url: "https://rynekpierwotny.pl/oferty/mill-yon-sp-z-oo/aura-vita-ii-pruszkow-14103/"
    }
  },
  source_links: [
    {
      source: "RP",
      url: "https://rynekpierwotny.pl/oferty/mill-yon-sp-z-oo/aura-vita-ii-pruszkow-14103/"
    }
  ]
};

const validInv = validateData(raw, USI_INVESTMENT_SCHEMA);

let links = [];
if (validInv.sources) {
    links = Object.entries(validInv.sources).map(([source, data]) => ({ source, url: data.url }));
} else if (validInv.source_links) {
    links = validInv.source_links;
}
console.log("links:", links);
