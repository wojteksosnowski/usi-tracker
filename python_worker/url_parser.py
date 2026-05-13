import re
import sys
from urllib.parse import urlparse, parse_qs

# Try to delegate to the library's parser if available
try:
    # Ensure library is in path (matches logic in config.py)
    LIB_PATH = "/Volumes/Samsam/claude-py/usi-scrapers"
    if LIB_PATH not in sys.path:
        sys.path.append(LIB_PATH)
        
    from usi_scrapers.utils.url_parser import parse_url as lib_parse_url
except ImportError:
    lib_parse_url = None

def parse_url(url: str) -> dict:
    """
    Parses RynekPierwotny.pl, Otodom.pl or TabelaOfert.pl URL.
    Delegates to usi-scrapers library for canonical parsing if available.
    """
    if lib_parse_url:
        return lib_parse_url(url)
        
    # FALLBACK (Legacy local logic)
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # 1. RynekPierwotny
    if "rynekpierwotny.pl" in domain:
        match = re.search(r'/oferty/([^/]+)/([^/]+)-(\d+)/', path)
        if match:
            query = parse_qs(parsed.query)
            return {
                "type": "rynekpierwotny",
                "kind": "investment",
                "developer_slug": match.group(1),
                "investment_slug": match.group(2),
                "offer_id": match.group(3),
                "stage_id": query.get("stage", [None])[0],
                "url": url,
            }
        match = re.search(r'/deweloperzy/([^/]+)/', path)
        if match:
            return {"type": "rynekpierwotny", "kind": "developer", "developer_slug": match.group(1), "url": url}
        
    # 2. Otodom
    if "otodom.pl" in domain:
        match = re.search(r'/firmy/deweloperzy/.*-ID(\d+)', path)
        if match:
            return {"type": "otodom", "kind": "developer", "agency_id": match.group(1), "url": url}
        match = re.search(r'/(inwestycja|oferta)/([^/]+)', path)
        if match:
            return {"type": "otodom", "kind": "investment", "investment_slug": match.group(2), "url": url}

    # 3. TabelaOfert
    if "tabelaofert.pl" in domain:
        match = re.search(r'/katalog-firm/deweloperzy/([^/]+)', path)
        if match:
            return {"type": "tabelaofert", "kind": "developer", "developer_slug": match.group(1), "url": url}
        match = re.search(r'/inwestycja/([^,]+),i(\d+)', path)
        if match:
            return {
                "type": "tabelaofert",
                "kind": "investment",
                "investment_slug": match.group(1),
                "to_id": match.group(2),
                "url": url,
            }

    return {"type": "unknown", "kind": "unknown", "url": url}
