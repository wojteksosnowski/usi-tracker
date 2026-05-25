import logging
from pathlib import Path
from datetime import datetime
from python_worker.config import USI_DATA_DIR, get_scraper_config
from usi_scrapers.fetcher import Fetcher
from usi_scrapers import api as scraper_api
from python_worker.url_parser import parse_url
from python_worker.portal_matcher import filter_new_investments
from python_worker.logger_utils import log_to_processing_log

from python_worker.services.investment_service import InvestmentService

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, data_dir: Path = USI_DATA_DIR):
        self.data_dir = data_dir
        self.config = get_scraper_config()
        self.fetcher = Fetcher(self.config) if self.config else None
        self.isvc = InvestmentService(data_dir=data_dir)

    def discover_for_developer(self, job_id=None, dev_slug=None, job_manager=None, download=False, auto_register=True):
        """
        Discovers and optionally registers new investments for a developer.
        Saves a snapshot of found items to Public/USIdev/{dev}/discovery.json.
        """
        # If called from CLI: discover_for_developer(slug, download=True)
        # If called from JobManager: discover_for_developer(job_id, slug, ...)
        if dev_slug is None and job_id is not None:
            dev_slug = job_id
            job_id = None

        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir, self.data_dir.parent / "USIdev")
        dev = dm.get_developer(dev_slug)
        if not dev:
            raise ValueError(f"Developer {dev_slug} not found")

        mapping = dev.get("portal_mapping", {})
        if job_manager and job_id:
            job_manager.update_progress(job_id, 10, "Szukam nowych inwestycji...")

        found_total = 0
        all_discovered = []
        new_items_to_download = []

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
                all_discovered.extend(filtered)
                
                new_found = [item for item in filtered if item.get("is_new")]
                
                for item in new_found:
                    # If we are going to download immediately, skip pre-registration
                    # process_batch will handle registration ONLY after successful download.
                    # This prevents 'skeleton' fragments if download fails.
                    if auto_register and not download:
                        self._register_new_investment(dev_slug, item, portal_key)
                        item["registered"] = True # Mark as registered in snapshot
                    elif auto_register and download:
                        # We mark as registered in snapshot because they are targeted for immediate ingestion
                        item["registered"] = True
                        
                    new_items_to_download.append((portal, item))
                found_total += len(new_found)
            except Exception as e:
                logger.error(f"{portal_name} discovery failed: {e}")
            
            current_progress += progress_step

        # Save snapshot of ALL items found in this run
        self._save_discovery_snapshot(dev_slug, all_discovered)

        ingested_total = 0
        if download and new_items_to_download:
            logger.info(f"Triggering bulk download for {len(new_items_to_download)} new investments...")

            # Group by portal
            by_portal = {}
            for portal, item in new_items_to_download:
                if portal not in by_portal: by_portal[portal] = []
                by_portal[portal].append(item)

            for p, items in by_portal.items():
                def progress_wrapper(report):
                    if job_manager and job_id:
                        msg = f"[{p.upper()}] {report['message']}"
                        job_manager.update_progress(job_id, int(current_progress), msg)

                try:
                    ingested_total += self.isvc.process_batch(p, items, on_progress_callback=progress_wrapper)
                except Exception as e:
                    logger.error(f"Bulk download for {p} failed: {e}")

        if job_manager and job_id:
            count = ingested_total if download else found_total
            msg = f"Zarejestrowano {count} nowych inwestycji." if count else "Brak nowych inwestycji."
            job_manager.update_progress(job_id, 100, msg)

        return ingested_total if download else found_total

    def get_unregistered_count(self, dev_slug: str, identifiers: dict = None) -> int:
        """Returns count of items in discovery.json that are not yet registered."""
        try:
            dev_dir = self.data_dir.parent / "USIdev" / dev_slug
            discovery_file = dev_dir / "discovery.json"
            if not discovery_file.exists():
                return 0
            
            import json
            with open(discovery_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Recalculate 'registered' status against current DB to be accurate
            if identifiers is None:
                from python_worker.developer_manager import DeveloperManager
                dm = DeveloperManager(self.data_dir)
                identifiers = dm.get_existing_identifiers()
            
            rp_ids = identifiers.get("rp_ids", set())
            oto_ids = identifiers.get("oto_ids", set())
            oto_slugs = identifiers.get("oto_slugs", set())
            to_ids = identifiers.get("to_ids", set())
            
            count = 0
            for item in data.get("items", []):
                portal = item.get("portal")
                is_registered = False
                if portal == "rp":
                    is_registered = str(item.get("id")) in rp_ids
                elif portal == "otodom" or portal == "oto":
                    is_registered = str(item.get("id")) in oto_ids or item.get("slug") in oto_slugs
                elif portal in ("to", "tabelaofert"):
                    is_registered = str(item.get("id")) in to_ids
                
                if not is_registered:
                    count += 1
            return count
        except Exception as e:
            logger.debug(f"Error getting unregistered count for {dev_slug}: {e}")
            return 0

    def _save_discovery_snapshot(self, dev_slug, items):
        """Saves discovery results to a JSON file in the developer's directory."""
        try:
            from python_worker.config import USI_DEV_DIR
            dev_dir = Path(USI_DEV_DIR) / dev_slug
            dev_dir.mkdir(parents=True, exist_ok=True)
            discovery_file = dev_dir / "discovery.json"
            
            data = {
                "dev_slug": dev_slug,
                "checked_at": datetime.now().isoformat(),
                "items": items
            }
            import json
            with open(discovery_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved discovery snapshot for {dev_slug} ({len(items)} items)")
        except Exception as e:
            logger.error(f"Failed to save discovery snapshot for {dev_slug}: {e}")

    def _register_new_investment(self, dev_slug, item, portal):
        """Helper to create a skeleton usi_*.json for a newly discovered investment."""
        inv_slug = item.get("slug")
        url = item.get("url")
        
        # If slug is missing in discovery result, try to parse it from URL
        if not inv_slug and url:
            parsed = parse_url(url)
            inv_slug = parsed.get("investment_slug")
            
        # Determine source key
        portal_key = "rp" if portal == "rp" else ("oto" if portal == "otodom" else "to")
        
        if not inv_slug:
            # Last resort fallback if both discovery and parsing failed
            # Mandate: Never slugify name. Use 'unknown' to avoid polluting DB with guessed slugs.
            inv_slug = "unknown"
            logger.warning(f"No slug from URL/discovery for '{item['name']}' (portal={portal}) - using 'unknown'")
        
        # Extract vendor ID for ID-first registration
        vendor_id = None
        if portal == "rp":
            vendor = item.get("vendor")
            if isinstance(vendor, dict):
                vendor_id = vendor.get("id")
        elif portal in ("otodom", "oto"):
            vendor_id = item.get("agency_id") or item.get("developer_id") or item.get("vendor_id")
        elif portal in ("to", "tabelaofert"):
            vendor_id = item.get("developer_id") or item.get("vendor_id")

        # Delegate registration to InvestmentService (which now handles canonical slugs from library)
        return self.isvc.register_investment(
            portal=portal_key,
            developer_name=dev_slug.replace("-", " ").title(), # Folder name as dev name hint
            inv_slug=inv_slug,
            name=item["name"],
            item_id=item.get("id"),
            url=url,
            allow_existing=True,
            vendor_id=vendor_id,
            force_dev_slug=dev_slug
        )

    def discovery_by_portal(self, portal, identifier=None, limit=None, pages=None):
        """
        Discovers new investments on a portal for global or specific scan.
        Supports both IDs (developer scan) and URLs (listing scan).
        """
        if pages:
            # Calculate limit based on portal-specific page sizes
            # OTO: 72/page, RP: 30/page, TO: 20/page
            page_sizes = {"rp": 30, "oto": 72, "to": 20}
            size = page_sizes.get(portal, 50)
            try:
                limit = int(pages) * size
            except (ValueError, TypeError):
                limit = None

        logger.info(f"Triggering discovery for portal: {portal} (Identifier: {identifier}, Pages: {pages}, Calculated Limit: {limit})")
        portal_key = "rp" if portal == "rp" else ("otodom" if portal == "oto" else "to")
        
        try:
            # USI-Scrapers v0.7.0+ standardized API
            if portal_key == "rp":
                results = scraper_api.discover_rp_investments(self.config, self.fetcher, identifier=identifier, limit=limit)
            elif portal_key == "otodom":
                results = scraper_api.discover_otodom_investments(self.config, self.fetcher, identifier=identifier, limit=limit)
            else: # to
                results = scraper_api.discover_to_investments(self.config, self.fetcher, identifier=identifier, limit=limit)

            logger.info(f"Scraper library returned {len(results)} items for {portal}")
            
            filtered = filter_new_investments(results, portal_key)
            logger.info(f"Filtered results: {len(filtered)} items")
            return filtered
        except Exception as e:
            logger.error(f"Error during discovery for {portal}: {e}", exc_info=True)
            raise
