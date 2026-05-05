import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.scraper_rp import discover_rp_investments
from python_worker.scraper_otodom import discover_otodom_investments, discover_otodom_listing
from python_worker.scraper_to import discover_to_investments
from python_worker.url_parser import parse_url
from python_worker.portal_matcher import filter_new_investments

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, data_dir: Path = USI_DATA_DIR):
        self.data_dir = data_dir

    def discover_for_developer(self, dev_slug, job_manager=None, job_id=None):
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir, self.data_dir.parent / "USIdev")
        dev = dm.get_developer(dev_slug)
        if not dev: 
            raise ValueError(f"Developer {dev_slug} not found")
        
        mapping = dev.get("portal_mapping", {})
        if job_manager and job_id:
            job_manager.update_progress(job_id, 10, "Starting discovery...")
        
        found_total = 0
        
        # 1. RP
        rp_map = mapping.get("rp") or {}
        rp_id = rp_map.get("id") or rp_map.get("slug")
        if rp_id:
            if job_manager and job_id:
                job_manager.update_progress(job_id, 20, f"Scanning RynekPierwotny ({rp_id})...")
            try:
                res = discover_rp_investments(rp_id)
                found_total += len(res)
            except Exception as e:
                logger.error(f"RP discovery failed: {e}")

        # 2. Otodom
        oto_map = mapping.get("oto") or {}
        oto_url = oto_map.get("url")
        if oto_url:
            if job_manager and job_id:
                job_manager.update_progress(job_id, 50, f"Scanning Otodom...")
            try:
                parsed = parse_url(oto_url)
                if parsed.get("agency_id"):
                    res = discover_otodom_investments(parsed["agency_id"])
                    found_total += len(res)
            except Exception as e:
                logger.error(f"Otodom discovery failed: {e}")

        # 3. TO
        to_map = mapping.get("to") or {}
        to_slug = to_map.get("slug")
        if to_slug:
            if job_manager and job_id:
                job_manager.update_progress(job_id, 80, f"Scanning TabelaOfert...")
            try:
                res = discover_to_investments(to_slug)
                found_total += len(res)
            except Exception as e:
                logger.error(f"TO discovery failed: {e}")

        if job_manager and job_id:
            job_manager.update_progress(job_id, 100, f"Finished. Found {found_total} potential investments.")
        
        return found_total

    def discovery_by_portal(self, portal, identifier=None):
        """
        Discovers new investments on a portal.
        """
        if portal == "rp":
            results = discover_rp_investments(identifier if identifier else None)
            return filter_new_investments(results, "rp")
        elif portal == "oto":
            from python_worker.config import OTODOM_DISCOVERY_URLS
            if identifier:
                results = discover_otodom_investments(identifier)
            else:
                results = []
                seen_slugs = set()
                for url in OTODOM_DISCOVERY_URLS:
                    try:
                        batch = discover_otodom_listing(url)
                        for item in batch:
                            if item["slug"] not in seen_slugs:
                                results.append(item)
                                seen_slugs.add(item["slug"])
                    except Exception as e:
                        logger.warning(f"Failed global discovery for {url}: {e}")
            return filter_new_investments(results, "otodom")
        elif portal == "to":
            results = discover_to_investments(identifier if identifier else None)
            return filter_new_investments(results, "to")
        else:
            raise ValueError(f"Unsupported portal: {portal}")
