import re
from urllib.parse import urlparse, parse_qs

def parse_url(url: str) -> dict:
    """
    Parses RynekPierwotny.pl or Otodom.pl URL to extract necessary identifiers.
    """
    parsed = urlparse(url)
    domain = parsed.netloc
    path = parsed.path
    
    # 1. RynekPierwotny.pl
    # Format: https://rynekpierwotny.pl/oferty/[developer_slug]/[investment_slug]-[id]/
    if "rynekpierwotny.pl" in domain:
        # regex to match /oferty/dev-slug/inv-slug-id/
        match = re.search(r'/oferty/([^/]+)/([^/]+)-(\d+)/', path)
        if match:
            query = parse_qs(parsed.query)
            return {
                "type": "rynekpierwotny",
                "developer_slug": match.group(1),
                "investment_slug": match.group(2),
                "offer_id": match.group(3),
                "stage_id": query.get("stage", [None])[0],
                "show_sold_stage": "show_sold_stage" in query,
                "url": url,
            }
        # Fallback for alternative URLs if needed
        
    # 2. Otodom.pl
    # Format: https://www.otodom.pl/pl/inwestycja/[slug]
    if "otodom.pl" in domain:
        match = re.search(r'/inwestycja/([^/]+)', path)
        if match:
            investment_slug = match.group(1)
            return {
                "type": "otodom",
                "developer_slug": "unknown",
                "investment_slug": investment_slug,
                "url": url
            }

    # 3. Tabelaofert.pl
    # Format: https://tabelaofert.pl/inwestycja/{slug},i{id}
    if "tabelaofert.pl" in domain:
        match = re.search(r'/inwestycja/([^,]+),i(\d+)', path)
        if match:
            return {
                "type": "tabelaofert",
                "developer_slug": "unknown",  # placeholder, updated after scraping
                "investment_slug": match.group(1),
                "to_id": match.group(2),
                "url": url,
            }

    return {"type": "unknown", "url": url}
