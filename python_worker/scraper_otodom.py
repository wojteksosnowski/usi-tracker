import json
import re
import logging
from .fetcher import fetch_html
from .image_saver import save_images

logger = logging.getLogger(__name__)

def fetch_otodom_html(url: str) -> str:
    """Fetches the Otodom URL using the centralized Fetcher."""
    return fetch_html(url) or ""

def extract_next_data(html: str) -> dict:
    """
    Extracts __NEXT_DATA__ JSON from the HTML source.
    """
    # Use regex to find the script tag content
    # <script id="__NEXT_DATA__" type="application/json" crossorigin="anonymous">...</script>
    pattern = r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>'
    match = re.search(pattern, html, re.DOTALL)
    
    if not match:
        logger.warning("Could not find __NEXT_DATA__ in Otodom HTML.")
        return {}
        
    try:
        data = json.loads(match.group(1))
        # Navigate to relevant props (props -> pageProps -> data)
        # Based on the original spec formulas
        return data.get("props", {}).get("pageProps", {})
    except Exception as e:
        logger.error(f"Error parsing __NEXT_DATA__ JSON: {e}")
        return {}

def discover_otodom_investments(agency_id: str) -> list[dict]:
    """
    Discovers investments for a given agency ID on Otodom.pl.
    Note: Otodom usually lists individual units as ads. 
    This function looks for project/investment links or unique ads.
    """
    # Otodom agency URL pattern: https://www.otodom.pl/pl/firmy/deweloperzy/any-slug-ID{agency_id}
    # We use a dummy slug since the ID is what matters
    url = f"https://www.otodom.pl/pl/firmy/deweloperzy/deweloper-ID{agency_id}"
    logger.info(f"Discovering Otodom investments for agency ID: {agency_id}")

    html = fetch_otodom_html(url)
    if not html:
        return []

    data = extract_next_data(html)
    if not data:
        return []

    offers = []
    try:
        # Search for ads in the agency profile
        # Path might vary, common one for agency is props.pageProps.data.searchAds.items
        search_ads = data.get("props", {}).get("pageProps", {}).get("data", {}).get("searchAds", {})
        items = search_ads.get("items", [])

        for item in items:
            slug = item.get("slug")
            if slug:
                offers.append({
                    "url": f"https://www.otodom.pl/pl/oferta/{slug}",
                    "name": item.get("title"),
                    "slug": slug
                })
    except Exception as e:
        logger.error(f"Error parsing Otodom discovery data: {e}")

    return offers

def scrape_otodom(url: str, developer_slug: str, investment_slug: str) -> dict:

    """
    Main function to scrape Otodom investment and save images.
    """
    # 1. Fetch HTML
    html = fetch_otodom_html(url)
    if not html:
        return {"error": "Could not fetch HTML"}
        
    # 2. Extract Data
    page_props = extract_next_data(html)
    if not page_props:
        return {"error": "Could not extract __NEXT_DATA__ JSON"}
        
    ad_data = page_props.get("ad", {})
    if not ad_data:
        # Fallback for search ads structure if it's a listing page instead of a detail page
        # but usually we're on a detail page
        ad_data = page_props.get("data", {}).get("searchAds", {})
        
    # 3. Extract Images and Developer Slug
    images = []
    images_raw = ad_data.get("images", [])
    for img in images_raw:
        # Prefer large resolution
        img_url = img.get("large")
        if img_url:
            images.append(img_url)
            
    # Try to extract actual developer slug from agency url (e.g. /deweloper/nick-ID)
    agency_url = ad_data.get("agency", {}).get("url", "")
    agency_name = ad_data.get("agency", {}).get("name", "")
    
    if agency_url:
        # regex from otodom.pl.md: (?<=\/)[^\/]+(?=-ID)
        dev_match = re.search(r'(?<=/)[^/]+(?=-ID)', agency_url)
        if dev_match:
            developer_slug = dev_match.group(0)
            logger.info(f"Extracted developer slug from Otodom: {developer_slug}")
        elif developer_slug in ("otodom", "unknown") and agency_name:
            from .csv_importer import slugify
            developer_slug = slugify(agency_name)
            logger.info(f"Resolved developer slug from Otodom agency name: {developer_slug}")
    elif developer_slug in ("otodom", "unknown") and agency_name:
        from .csv_importer import slugify
        developer_slug = slugify(agency_name)
        logger.info(f"Resolved developer slug from Otodom agency name: {developer_slug}")
            
    # 4. Save Images
    logger.info(f"Found {len(images)} images for Otodom investment {investment_slug}")
    saved_filenames = save_images(images, developer_slug, investment_slug)
    image_paths = [f"/Public/USI/{developer_slug}/{investment_slug}/{fname}" for fname in saved_filenames]
    
    # 5. Extract Geo
    # Coordinates are at location.coordinates (mapDetails only has radius/zoom)
    coords = ad_data.get("location", {}).get("coordinates", {})
    lat = coords.get("latitude")
    lng = coords.get("longitude")

    # 6. Extract delivery date
    # New format: topInformation[label=project_finish_date].values[0] = "YYYY-MM-DD"
    delivery_quarter = None
    delivery_year = None
    for item in ad_data.get("topInformation", []):
        if item.get("label") == "project_finish_date":
            values = item.get("values", [])
            if values:
                try:
                    parts = values[0].split("-")
                    delivery_year = int(parts[0])
                    delivery_quarter = (int(parts[1]) - 1) // 3 + 1
                except Exception:
                    pass
            break
    # Fallback to old format if present
    if delivery_quarter is None:
        old_delivery = ad_data.get("investmentEstimatedDelivery") or {}
        delivery_quarter = old_delivery.get("quarter")
        delivery_year = old_delivery.get("year")

    # 7. Build Result JSON
    ad_data["url"] = url
    ad_data["images_count"] = len(saved_filenames)
    ad_data["image_paths"] = image_paths
    
    result = {
        "source": "otodom.pl",
        "url": url,
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": f"/Public/USI/{developer_slug}/{investment_slug}/",
        "title": ad_data.get("title"),
        "agency_name": ad_data.get("agency", {}).get("name"),
        "agency_id": ad_data.get("agency", {}).get("id"),
        "latitude": lat,
        "longitude": lng,
        "delivery_quarter": delivery_quarter,
        "delivery_year": delivery_year,
        "images_count": len(saved_filenames),
        "image_paths": image_paths,
        "raw_details": ad_data
    }
    
    return result
