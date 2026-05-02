import re
import requests
import logging
import random
import json
from .config import SCRAPERAPI_KEY, USI_DATA_DIR
from .logger_utils import log_to_processing_log
from .scraper_rp import scrape_rynek_pierwotny
from .scraper_otodom import scrape_otodom, discover_otodom_listing
from .scraper_to import fetch_to_html, scrape_tabelaofert
from .config import SCRAPERAPI_KEY, USI_DATA_DIR, OTODOM_DISCOVERY_URLS

logger = logging.getLogger(__name__)

def get_random_prime_delay() -> float:
    """Returns a random prime number between 300 and 700, converted to seconds."""
    primes = [
        307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397,
        401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491,
        499, 503, 509, 521, 523, 541, 547, 557, 563, 569, 571, 577, 587, 593, 599, 601,
        607, 613, 617, 619, 631, 641, 643, 647, 653, 659, 661, 673, 677, 683, 691
    ]
    return random.choice(primes) / 1000.0

def fetch_recent_rp_investments(test_mode=False, limit=None):
    """
    Fetches recent investments from RynekPierwotny.pl and processes them.
    Returns a list of processed result objects (path and data).
    """
    url = "https://rynekpierwotny.pl/api/v2/offers/offer/?s=offer-list&display_type=1&distance=5&for_sale=true&limited_presentation=false&page=1&page_size=30&show_on_listing=true&type=1"
    logger.info(f"Fetching recent RynekPierwotny investments from {url}")
    
    processed_results = []
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        results = data.get("results", [])
        
        if test_mode and len(results) > 3:
            logger.info("Test mode active: sampling 3 random items from RP listing.")
            results = random.sample(results, 3)
        elif limit is not None and len(results) > limit:
            results = results[:limit]
            
        logger.info(f"Processing {len(results)} investments on RynekPierwotny listing.")
        
        for item in results:
            offer_id = str(item.get("id"))
            dev_slug = item.get("developer", {}).get("slug", "unknown")
            inv_slug = item.get("slug", "unknown")
            
            logger.info(f"Processing RP listing item: {inv_slug} (ID: {offer_id})")
            result = scrape_rynek_pierwotny(offer_id, dev_slug, inv_slug, None)
            
            # Save JSON result to USIdata in structured folder
            if "error" not in result:
                # Use the developer_slug returned by the scraper (extracted from detailed vendor data)
                actual_dev_slug = result.get("developer_slug", dev_slug)
                actual_inv_slug = result.get("investment_slug", inv_slug)
                
                result_dir = USI_DATA_DIR / actual_dev_slug / actual_inv_slug
                result_dir.mkdir(parents=True, exist_ok=True)
                
                filename = f"app_result_manual_rp_{offer_id}.json"
                result_path = result_dir / filename
                with open(result_path, 'w') as f:
                    json.dump(result, f, indent=4)
                logger.info(f"Saved JSON result to {result_path}")
                
                # Save raw details as a separate file for Coda
                raw_filename = "rp_details.json"
                raw_path = result_dir / raw_filename
                with open(raw_path, 'w') as f:
                    json.dump(result.get("raw_details", {}), f, indent=4)
                log_to_processing_log(actual_dev_slug, actual_inv_slug, f"Saved data from listing (Source: {result.get('source')})")
                logger.info(f"Saved raw details to {raw_path}")
                
                # Add to summary list
                coda_path = f"/Public/USIdata/{actual_dev_slug}/{actual_inv_slug}/{filename}"
                processed_results.append({
                    "path": coda_path,
                    "data": result
                })
            
    except Exception as e:
        logger.error(f"Error fetching RP listing: {e}")
        
    return processed_results

def fetch_recent_otodom_investments(test_mode=False, limit=None):
    """
    Fetches recent investments from Otodom.pl and processes them.
    Returns a list of processed result objects (path and data).
    """
    processed_results = []
    all_items = []

    for url in OTODOM_DISCOVERY_URLS:
        logger.info(f"Fetching recent Otodom investments from {url}")
        items = discover_otodom_listing(url)
        all_items.extend(items)
        
        # Apply rate limit between listing pages
        delay = get_random_prime_delay()
        logger.info(f"Rate limiting: sleeping for {delay*1000:.0f}ms")
        time.sleep(delay)
        
    if test_mode and len(all_items) > 3:
        logger.info("Test mode active: sampling 3 random items from Otodom listing.")
        all_items = random.sample(all_items, 3)
    elif limit is not None and len(all_items) > limit:
        all_items = all_items[:limit]
        
    logger.info(f"Found {len(all_items)} investments on Otodom listing.")
    
    for item in all_items:
        slug = item.get("slug")
        if not slug:
            continue
            
        full_url = f"https://www.otodom.pl/pl/inwestycja/{slug}"
        # For Otodom listings, we don't have the developer slug initially, 
        # but scraping will extract it if available.
        logger.info(f"Processing Otodom listing item: {slug}")
        
        # Apply rate limit before each detail scrape
        delay = get_random_prime_delay()
        logger.info(f"Rate limiting: sleeping for {delay*1000:.0f}ms before scraping {slug}")
        time.sleep(delay)
        
        result = scrape_otodom(full_url, "unknown", slug)
        
        # Save JSON result to USIdata in structured folder
        if "error" not in result:
            # Use the actual slugs from result (extracted from details)
            actual_dev_slug = result.get("developer_slug", "unknown")
            actual_inv_slug = result.get("investment_slug", slug)

            result_dir = USI_DATA_DIR / actual_dev_slug / actual_inv_slug
            result_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"app_result_manual_oto_{slug}.json"
            result_path = result_dir / filename
            with open(result_path, 'w') as f:
                json.dump(result, f, indent=4)
            logger.info(f"Saved JSON result to {result_path}")
            
            # Save raw details as a separate file for Coda
            raw_filename = "oto_details.json"
            raw_path = result_dir / raw_filename
            with open(raw_path, 'w') as f:
                json.dump(result.get("raw_details", {}), f, indent=4)
            log_to_processing_log(actual_dev_slug, actual_inv_slug, f"Saved data from listing (Source: {result.get('source')})")
            logger.info(f"Saved raw details to {raw_path}")
            
            # Add to summary list
            coda_path = f"/Public/USIdata/{actual_dev_slug}/{actual_inv_slug}/{filename}"
            processed_results.append({
                "path": coda_path,
                "data": result
            })
            
    return processed_results

def fetch_recent_to_investments(limit=None):
    listing_url = "https://tabelaofert.pl/nowe-mieszkania"
    logger.info(f"Fetching recent TabelaOfert investments from {listing_url}")

    html = fetch_to_html(listing_url)
    if not html:
        logger.error("Could not fetch TabelaOfert listing HTML.")
        return []

    urls = list(dict.fromkeys(
        re.findall(r"https://tabelaofert\.pl/inwestycja/[^\"\\]+,i\d+", html)
    ))
    if not urls:
        logger.error("No investment URLs found in TabelaOfert listing.")
        return []

    if limit is not None:
        urls = urls[:limit]

    logger.info(f"Processing {len(urls)} investments from TabelaOfert listing.")
    processed_results = []

    for inv_url in urls:
        m = re.search(r"/inwestycja/(.+),i(\d+)", inv_url)
        if not m:
            continue
        inv_slug = m.group(1)
        to_id = m.group(2)

        logger.info(f"Processing TO listing item: {inv_slug}")
        result = scrape_tabelaofert(inv_url, "unknown", inv_slug)

        if "error" not in result:
            actual_dev_slug = result.get("developer_slug", "unknown")
            actual_inv_slug = result.get("investment_slug", inv_slug)

            result_dir = USI_DATA_DIR / actual_dev_slug / actual_inv_slug
            result_dir.mkdir(parents=True, exist_ok=True)

            filename = f"app_result_manual_to_{to_id}.json"
            result_path = result_dir / filename
            with open(result_path, "w") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            logger.info(f"Saved JSON result to {result_path}")

            raw_path = result_dir / "to_details.json"
            with open(raw_path, "w") as f:
                json.dump(result.get("raw_details", {}), f, indent=4, ensure_ascii=False)
            log_to_processing_log(actual_dev_slug, actual_inv_slug, f"Saved data from listing (Source: {result.get('source')})")
            logger.info(f"Saved raw details to {raw_path}")

            coda_path = f"/Public/USIdata/{actual_dev_slug}/{actual_inv_slug}/{filename}"
            processed_results.append({"path": coda_path, "data": result})
        else:
            logger.warning(f"Skipping {inv_url}: {result.get('error')}")

    return processed_results


def fetch_all_recent(test_mode=False, limit_per_portal=None):
    """
    Runs both RP and Otodom listing fetches and generates a summary JSON.
    """
    logger.info("Starting automatic fetch of recent investments...")
    
    all_results = []
    
    rp_results = fetch_recent_rp_investments(test_mode=test_mode, limit=limit_per_portal)
    all_results.extend(rp_results)

    oto_results = fetch_recent_otodom_investments(test_mode=test_mode, limit=limit_per_portal)
    all_results.extend(oto_results)

    to_results = fetch_recent_to_investments(limit=limit_per_portal)
    all_results.extend(to_results)
    
    # Generate app_latest_results.json (Full)
    summary_path = USI_DATA_DIR / "app_latest_results.json"
    brief_summary_path = USI_DATA_DIR / "app_latest_results_brief.json"
    
    try:
        # Full content
        with open(summary_path, 'w') as f:
            json.dump(all_results, f, indent=4)
        logger.info(f"Full batch summary generated: {summary_path}")

        # Brief content (exclude raw_details)
        brief_results = []
        for item in all_results:
            brief_item = {
                "path": item["path"],
                "data": {k: v for k, v in item["data"].items() if k != "raw_details"}
            }
            brief_results.append(brief_item)

        with open(brief_summary_path, 'w') as f:
            json.dump(brief_results, f, indent=4)
        logger.info(f"Brief batch summary generated: {brief_summary_path}")

    except Exception as e:
        logger.error(f"Error generating summary files: {e}")
        
    logger.info(f"Automatic fetch completed with {len(all_results)} items.")
