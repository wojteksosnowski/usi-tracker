import logging
from pathlib import Path
from datetime import datetime
from python_worker.config import USI_DATA_DIR, get_scraper_config
from usi_scrapers.fetcher import Fetcher
from usi_scrapers import api as scraper_api
from python_worker.url_parser import parse_url
from python_worker.portal_matcher import filter_new_investments
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, data_dir: Path = USI_DATA_DIR):
        self.data_dir = data_dir
        self.config = get_scraper_config()
        self.fetcher = Fetcher(self.config) if self.config else None

    def discover_for_developer(self, job_id, dev_slug, job_manager=None, download=False):
        """
        Discovers and registers new investments for a developer.
        Called via JobManager.start_job — job_id is the first positional arg by convention.
        """
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir, self.data_dir.parent / "USIdev")
        dev = dm.get_developer(dev_slug)
        if not dev:
            raise ValueError(f"Developer {dev_slug} not found")

        mapping = dev.get("portal_mapping", {})
        if job_manager and job_id:
            job_manager.update_progress(job_id, 10, "Szukam nowych inwestycji...")

        found_total = 0
        new_items = []

        # Portals to scan — use `or {}` to handle null values stored in JSON
        rp_m  = mapping.get("rp")  or {}
        oto_m = mapping.get("oto") or {}
        to_m  = mapping.get("to")  or {}
        portals = [
            ("rp",  rp_m.get("id") or rp_m.get("slug")),
            ("oto", oto_m.get("agency_ids", []) or ([oto_m["agency_id"]] if oto_m.get("agency_id") else [])),
            ("to",  to_m.get("agency_id") or to_m.get("slug")),
        ]

        if all(not ident for _, ident in portals):
            if job_manager and job_id:
                job_manager.update_progress(job_id, 100, "Brak powiązań portalowych — nic do sprawdzenia.")
            return 0

        progress_step = 80 / len(portals) if portals else 0
        current_progress = 10

        for portal, identifier in portals:
            if not identifier: continue
            
            portal_name = "RynekPierwotny" if portal == "rp" else ("Otodom" if portal == "oto" else "TabelaOfert")
            if job_manager and job_id:
                job_manager.update_progress(job_id, int(current_progress), f"Sprawdzam {portal_name}...")
            
            try:
                # Handle multiple agency IDs for Otodom
                ids = identifier if isinstance(identifier, list) else [identifier]
                results = []
                for idx in ids:
                    results.extend(scraper_api.list_investments(self.config, self.fetcher, portal, str(idx)))
                
                portal_key = "rp" if portal == "rp" else ("otodom" if portal == "oto" else "to")
                filtered = filter_new_investments(results, portal_key)
                new_found = [item for item in filtered if item.get("is_new")]
                
                for item in new_found:
                    self._register_new_investment(dev_slug, item, portal_key)
                    new_items.append((portal, item))
                found_total += len(new_found)
            except Exception as e:
                logger.error(f"{portal_name} discovery failed: {e}")
            
            current_progress += progress_step

        if download and new_items:
            logger.info(f"Downloading raw JSONs for {len(new_items)} new investments...")
            from python_worker.main import download_raw_json
            for portal, item in new_items:
                identifier = item.get("id") if portal == "rp" else item.get("url")
                download_raw_json(portal, identifier, dev_slug, item["slug"])

        if job_manager and job_id:
            msg = f"Zarejestrowano {found_total} nowych inwestycji." if found_total else "Brak nowych inwestycji."
            job_manager.update_progress(job_id, 100, msg)
        
        return found_total

    def _register_new_investment(self, dev_slug, item, portal):
        """Helper to create a skeleton usi_*.json for a newly discovered investment."""
        inv_slug = item["slug"]
        inv_dir = self.data_dir / dev_slug / inv_slug
        inv_dir.mkdir(parents=True, exist_ok=True)
        
        usi_file = inv_dir / f"usi_{inv_slug}.json"
        
        # Determine source key
        portal_key = "rp" if portal == "rp" else ("oto" if portal == "otodom" else "to")
        identifier_key = "id" if portal == "rp" else "url"
        identifier_val = item.get("id") if portal == "rp" else item.get("url")
        
        import json
        if usi_file.exists():
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {
                "investment_slug": inv_slug,
                "developer_slug": dev_slug,
                "name": item["name"],
                "sources": {},
                "audit": {"created_at": datetime.now().isoformat()}
            }
        
        if portal_key not in data["sources"]:
            data["sources"][portal_key] = {identifier_key: identifier_val}
            with open(usi_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            log_to_processing_log(dev_slug, inv_slug, f"Discovered and registered from {portal} ({identifier_key}: {identifier_val})")
            logger.info(f"REGISTERED NEW {portal} Investment: {item['name']} in {dev_slug}/{inv_slug}")

    def discovery_by_portal(self, portal, identifier=None):
        """
        Discovers new investments on a portal for global or specific scan.
        """
        logger.info(f"Triggering discovery for portal: {portal} (ID: {identifier})")
        portal_key = "rp" if portal == "rp" else ("otodom" if portal == "oto" else "to")
        
        try:
            results = scraper_api.list_investments(self.config, self.fetcher, portal, identifier)
            logger.info(f"Scraper library returned {len(results)} items for {portal}")
            
            filtered = filter_new_investments(results, portal_key)
            logger.info(f"Filtered results: {len(filtered)} items")
            return filtered
        except Exception as e:
            logger.error(f"Error during discovery for {portal}: {e}", exc_info=True)
            raise
