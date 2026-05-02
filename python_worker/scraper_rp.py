import logging
import json
from pathlib import Path
from .fetcher import fetch_json, fetch_html
from .image_saver import save_images
from .stage_detector import extract_groups_id, extract_stages
from .config import USI_DATA_DIR, USI_DEV_DIR

logger = logging.getLogger(__name__)

def download_raw_rp_dev_json(vendor_id_or_slug: str, dev_slug: str) -> Path | None:
    """
    Downloads raw JSON for an RP developer profile and saves it.
    """
    profile = fetch_rp_developer_profile(vendor_id_or_slug)
    if not profile:
        logger.error(f"Failed to fetch RP developer profile for {vendor_id_or_slug}")
        return None

    from .developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    return dm.save_dev_raw_json(profile, dev_slug, "rp")

def fetch_rp_developer_profile(vendor_id_or_slug: str) -> dict:
    """
    Fetches developer profile from RynekPierwotny.pl API.
    """
    vendor_id = vendor_id_or_slug
    if not str(vendor_id_or_slug).isdigit():
        vendor_id = resolve_rp_vendor_id(vendor_id_or_slug)
        if not vendor_id:
            logger.error(f"Could not resolve vendor ID for slug: {vendor_id_or_slug}")
            return {}

    url = f"https://rynekpierwotny.pl/api/v2/vendors/vendor/{vendor_id}/?s=vendor-detail"
    logger.info(f"Fetching RynekPierwotny developer profile for ID: {vendor_id} from {url}")
    return fetch_json(url) or {}

def download_raw_rp_json(offer_id: str, dev_slug: str, inv_slug: str) -> Path | None:
    """
    Downloads raw JSON for an RP investment (details + gallery) and saves it to the database.
    Does not process images or adapt data.
    """
    details = fetch_rp_details(offer_id)
    if not details:
        logger.error(f"Failed to fetch RP details for ID {offer_id}")
        return None

    # Also fetch gallery to make the raw JSON complete
    gallery_data = fetch_json(f"https://rynekpierwotny.pl/api/v2/offers/offer/{offer_id}/?s=offer-detail-gallery")
    if gallery_data:
        details["_raw_gallery"] = gallery_data

    from .developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR)
    return dm.save_raw_json(details, dev_slug, inv_slug, "rp")

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

def discover_rp_investments(vendor_id_or_slug: str = None) -> list[dict]:
    """
    Discovers investments on RynekPierwotny.pl.
    If vendor_id_or_slug is provided, fetches offers for that vendor.
    If None, fetches recent offers using global JSONMAIN queries from config.
    Handles stage-flattening (extracts all stages from multi-stage developments).
    """
    if vendor_id_or_slug:
        vendor_id = vendor_id_or_slug
        if not vendor_id_or_slug.isdigit():
            vendor_id = resolve_rp_vendor_id(vendor_id_or_slug)
            if not vendor_id:
                logger.error(f"Could not resolve vendor ID for slug: {vendor_id_or_slug}")
                return []
        url = f"https://rynekpierwotny.pl/api/v2/offers/offer/?s=vendor-detail-offer-list&country=1&country=2&display_type=1&display_type=2&page=1&page_size=100&type=1&type=2&type=3&vendor={vendor_id}"
        logger.info(f"Discovering RP investments for vendor ID: {vendor_id}")
        data = fetch_json(url) or {}
        return _parse_rp_results(data.get("results", []))
    else:
        # Global discovery - scan all configured URLs
        from .config import RP_DISCOVERY_URLS
        all_results = []
        seen_ids = set()
        for url in RP_DISCOVERY_URLS:
            logger.info(f"Discovering RP investments via global JSONMAIN query: {url}")
            data = fetch_json(url) or {}
            batch = _parse_rp_results(data.get("results", []))
            for item in batch:
                if item["id"] not in seen_ids:
                    all_results.append(item)
                    seen_ids.add(item["id"])
        return all_results

def _parse_rp_results(results: list) -> list[dict]:
    """Helper to parse RP API results and flatten stages."""
    offers = []
    for item in results:
        # Deep helper to get value from the common {type: ..., value: ...} structure
        def get_val(obj, key):
            if not obj or not isinstance(obj, dict): return None
            v = obj.get(key)
            if isinstance(v, dict) and "value" in v:
                return v["value"]
            return v

        # Parent data
        parent_name = item.get("name")
        parent_id = str(item.get("id"))
        
        # Robust parent image extraction for Discovery (JSONMAIN)
        parent_img = None
        main_img_data = item.get("main_image")
        if main_img_data:
            if isinstance(main_img_data, str): parent_img = main_img_data
            elif isinstance(main_img_data, dict):
                parent_img = main_img_data.get("m_img_1500") or main_img_data.get("m_img_500") or main_img_data.get("image")
        
        if not parent_img:
            gallery = item.get("gallery")
            if gallery and isinstance(gallery, list) and len(gallery) > 0:
                first_img = gallery[0].get("image")
                if isinstance(first_img, dict):
                    parent_img = first_img.get("g_img_1500") or first_img.get("g_img_500") or first_img.get("image")
                elif isinstance(first_img, str):
                    parent_img = first_img

        groups = get_val(item, "groups") or {}
        stages = get_val(groups, "stages") or []
        
        if stages:
            # Stage-flattening: yield each stage as a separate discovery item
            for stage in stages:
                s_id_internal = stage.get("id")
                s_offer_val = get_val(stage, "offer")
                
                if s_offer_val:
                    s_id = str(s_offer_val.get("id"))
                    s_name = s_offer_val.get("name")
                    s_slug = s_offer_val.get("slug")
                    s_vendor_val = get_val(s_offer_val, "vendor") or {}
                    s_vendor_slug = s_vendor_val.get("slug")
                    
                    # Stage image - usually missing in discovery, use parent_img
                    s_img = None
                    s_main_photo = get_val(s_offer_val, "main_photo") or get_val(s_offer_val, "main_image")
                    if s_main_photo:
                        if isinstance(s_main_photo, str): s_img = s_main_photo
                        elif isinstance(s_main_photo, dict):
                            s_img = s_main_photo.get("image") or s_main_photo.get("m_img_1500")
                    
                    if not s_img:
                        s_img = parent_img
                    
                    offers.append({
                        "id": s_id,
                        "name": s_name,
                        "slug": s_slug,
                        "url": f"https://rynekpierwotny.pl/oferty/{s_vendor_slug}/{s_slug}-{s_id}/?show_sold_stage=true&stage={s_id_internal}",
                        "image": s_img,
                        "is_stage": True,
                        "parent_id": parent_id
                    })
        else:
            # Single-stage investment
            v_data = get_val(item, "vendor") or {}
            v_slug = v_data.get("slug")
            o_id = str(item.get("id"))
            o_slug = item.get("slug")
            
            offers.append({
                "id": o_id,
                "name": parent_name,
                "slug": o_slug,
                "url": f"https://rynekpierwotny.pl/oferty/{v_slug}/{o_slug}-{o_id}/",
                "image": parent_img,
                "is_stage": False
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
