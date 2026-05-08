import requests
import re
import logging
from urllib.parse import unquote
from .config import SCRAPERAPI_KEY, get_scraper_config
from usi_scrapers.manager import TechnicalDataManager

logger = logging.getLogger(__name__)

def fetch_developer_site_via_scraperapi(url: str) -> str:
    """
    Fetches the developer website through ScraperAPI.
    """
    if not SCRAPERAPI_KEY:
        logger.error("SCRAPERAPI_KEY not set in config.")
        return ""
        
    scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={url}"
    logger.info(f"Fetching developer site via ScraperAPI: {url}")
    
    try:
        response = requests.get(scraper_url, timeout=60)
        response.raise_for_status()
        return response.text
    except Exception as e:
        logger.error(f"Error fetching developer site via ScraperAPI: {e}")
        return ""

def extract_links_with_regex(html: str, regex_pattern: str) -> list[str]:
    """
    Extracts image links from HTML using provided regex.
    """
    # Compile regex with ignore case and dotall for better matching
    regex = re.compile(regex_pattern, re.IGNORECASE | re.DOTALL)
    
    # Extract matches
    matches = regex.findall(html)
    
    # Clean and decode links
    links = []
    for match in matches:
        # Some regexes might return groups, we take the last one or full match
        link = match[-1] if isinstance(match, tuple) else match
        
        # Decode special chars (%2f -> /)
        link = unquote(link)
        
        # Remove whitespace
        link = link.strip()
        
        # skip empty and redundant
        if link and link not in links:
            links.append(link)
            
    return links

def grabber(url: str, regex_pattern: str, developer_slug: str, investment_slug: str) -> dict:
    """
    Grabber module: fetches developer site, extracts links using regex, and saves images.
    """
    # 1. Fetch HTML
    html = fetch_developer_site_via_scraperapi(url)
    if not html:
        return {"error": "Could not fetch HTML via ScraperAPI"}
        
    # 2. Extract Links
    links = extract_links_with_regex(html, regex_pattern)
    if not links:
        logger.warning(f"No links found for developer site {url} with regex {regex_pattern}")
        return {"error": "No links found with regex"}
        
    # 3. Save Images
    logger.info(f"Grabber found {len(links)} images for {investment_slug}")
    config = get_scraper_config()
    tm = TechnicalDataManager(config)
    saved_filenames = tm.sync_images(links, developer_slug, investment_slug)
    
    # Filter out None from saved_filenames (sync_images returns List[Optional[str]])
    saved_filenames = [f for f in saved_filenames if f]
    image_paths = [f"/Public/USI/{developer_slug}/{investment_slug}/{fname}" for fname in saved_filenames]
    
    # 4. Build Result
    result = {
        "source": "grabber",
        "url": url,
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": f"/Public/USI/{developer_slug}/{investment_slug}/",
        "regex": regex_pattern,
        "images_count": len(saved_filenames),
        "image_paths": image_paths
    }
    
    return result
