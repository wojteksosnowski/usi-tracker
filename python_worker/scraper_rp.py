import logging
from .fetcher import fetch_json
from .image_saver import save_images
from .stage_detector import extract_groups_id, extract_stages

logger = logging.getLogger(__name__)

def fetch_rp_details(offer_id: str) -> dict:
    """
    Fetches investment details from RynekPierwotny.pl API v2.
    """
    url = f"https://rynekpierwotny.pl/api/v2/offers/offer/{offer_id}/?s=offer-detail"
    logger.info(f"Fetching RynekPierwotny details for ID: {offer_id} from {url}")
    return fetch_json(url) or {}

def fetch_rp_gallery(offer_id: str) -> list[str]:
    """
    Fetches image URLs from RynekPierwotny.pl gallery API.
    """
    url = f"https://rynekpierwotny.pl/api/v2/offers/offer/{offer_id}/?s=offer-detail-gallery"
    logger.info(f"Fetching RynekPierwotny gallery for ID: {offer_id} from {url}")
    
    data = fetch_json(url) or {}
    # Extract images from gallery
    images = []
    gallery = data.get("gallery", [])
    for item in gallery:
        # Prefer 1500 resolution
        img_url = item.get("image", {}).get("g_img_1500")
        if img_url:
            images.append(img_url)
                
    return images

def resolve_rp_vendor_id(slug: str) -> str | None:
    """
    Scrapes the developer profile page on RynekPierwotny.pl to find their vendor ID.
    """
    url = f"https://rynekpierwotny.pl/deweloperzy/{slug}/"
    logger.info(f"Resolving RP vendor ID for slug: {slug} from {url}")
    html = fetch_html(url)
    if not html:
        return None
    
    # Look for "vendor": ID in the page source or API calls mentioned in scripts
    # Usually it is in a script tag with some JSON
    match = re.search(r'"vendor_id":\s*(\d+)', html)
    if match:
        return match.group(1)
    
    # Alternative: check for vendor={ID} in links
    match = re.search(r'vendor=(\d+)', html)
    if match:
        return match.group(1)
        
    return None

def discover_rp_investments(vendor_id_or_slug: str) -> list[dict]:
    """
    Discovers all investments (offers) for a given vendor ID or slug on RynekPierwotny.pl.
    """
    vendor_id = vendor_id_or_slug
    if not vendor_id_or_slug.isdigit():
        vendor_id = resolve_rp_vendor_id(vendor_id_or_slug)
        if not vendor_id:
            logger.error(f"Could not resolve vendor ID for slug: {vendor_id_or_slug}")
            return []

    url = f"https://rynekpierwotny.pl/api/v2/offers/offer/?s=vendor-detail-offer-list&country=1&country=2&display_type=1&display_type=2&page=1&page_size=100&type=1&type=2&type=3&vendor={vendor_id}"
    logger.info(f"Discovering RynekPierwotny investments for vendor ID: {vendor_id}")
    
    data = fetch_json(url) or {}
    offers = []
    results = data.get("results", [])
    for item in results:
        offers.append({
            "id": str(item.get("id")),
            "name": item.get("name"),
            "slug": item.get("slug"),
            "address": item.get("address")
        })
    return offers

def scrape_rynek_pierwotny(offer_id: str, developer_slug: str, investment_slug: str, url: str = None) -> dict:
    """
    Main function to scrape RynekPierwotny investment and save images.
    """
    # Fetch core details
    details = fetch_rp_details(offer_id)
    if not details:
        return {"error": "Could not fetch details"}
        
    # Fetch gallery
    gallery_urls = fetch_rp_gallery(offer_id)
    
    # Add main image to gallery if present
    main_image = details.get("main_image", {}).get("m_img_500")
    if main_image:
        gallery_urls.insert(0, main_image)
        
    # Helper to get value from the common {type: ..., value: ...} structure
    def get_val(data, key, default=None):
        if not data or key not in data:
            return default
        val = data[key]
        if isinstance(val, dict) and "value" in val:
            return val["value"]
        return val

    # Try to extract actual developer slug from vendor data
    vendor_data = get_val(details, "vendor")
    vendor_slug = get_val(vendor_data, "slug") if vendor_data else None
    offer_slug = details.get("slug", "")

    if vendor_slug:
        developer_slug = vendor_slug.strip()
        logger.info(f"Extracted developer slug from RynekPierwotny: {developer_slug}")

    if not url and vendor_slug and offer_slug:
        url = f"https://rynekpierwotny.pl/oferty/{vendor_slug}/{offer_slug}-{offer_id}/"
        logger.info(f"Constructed RP URL from API: {url}")
        
    # Download images
    logger.info(f"Found {len(gallery_urls)} images for {investment_slug}")
    saved_filenames = save_images(gallery_urls, developer_slug, investment_slug)
    image_paths = [f"/Public/USI/{developer_slug}/{investment_slug}/{fname}" for fname in saved_filenames]
    
    # Add url to details for adapter
    details["url"] = url

    # Extract geo and dates using the same helper logic
    geo_point = get_val(details, "geo_point")
    coords = get_val(geo_point, "coordinates") if geo_point else None
    
    construction_date = get_val(details, "construction_date_range")
    const_upper = get_val(construction_date, "upper") if construction_date else None

    stages = extract_stages(details)
    groups_id = extract_groups_id(details)
    groups = details.get("groups") or {}

    # Find stage metadata for current offer_id
    stage_sort = None
    stage_is_current = None
    for s in stages:
        if str(s["offer_id"]) == str(offer_id):
            stage_sort = s["sort"]
            stage_is_current = s["current"]
            break

    # Inject images into details for the adapter
    details["images_count"] = len(saved_filenames)
    details["image_paths"] = image_paths

    sibling_stages = stages
    sibling_stage_folders = [
        f"{developer_slug}/{s['slug']}"
        for s in stages
        if str(s["offer_id"]) != str(offer_id) and s["slug"]
    ]

    result = {
        "source": "rynekpierwotny.pl",
        "id": offer_id,
        "url": url,
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": f"/Public/USI/{developer_slug}/{investment_slug}/",
        "name": details.get("name"),
        "address": details.get("address"),
        "geo_point": coords,
        "latitude": coords[1] if coords and len(coords) > 1 else (coords[0] if coords else None),
        "longitude": coords[0] if coords and len(coords) > 0 else None,
        "construction_date_upper": const_upper,
        "website": details.get("website"),
        "properties_count": details.get("properties"),
        "images_count": len(saved_filenames),
        "image_paths": image_paths,
        "groups_id": groups_id,
        "groups_name": groups.get("name"),
        "stage_sort": stage_sort,
        "stage_is_current": stage_is_current,
        "sibling_stages": sibling_stages,
        "sibling_stage_folders": sibling_stage_folders,
        "raw_details": details,
    }

    return result
