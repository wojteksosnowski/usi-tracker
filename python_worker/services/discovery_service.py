import logging
from pathlib import Path
from datetime import datetime
from python_worker.config import USI_DATA_DIR, get_shared_config, get_shared_fetcher, get_shared_scraper_gateway
from python_worker.url_parser import parse_url
from python_worker.portal_matcher import filter_new_investments
from python_worker.logger_utils import log_to_processing_log

from python_worker.services.investment_service import InvestmentService

logger = logging.getLogger(__name__)

class DiscoveryService:
    def __init__(self, data_dir: Path = USI_DATA_DIR, scraper_gateway=None):
        self.data_dir = data_dir
        self.gateway = scraper_gateway or get_shared_scraper_gateway()
        self.isvc = InvestmentService(data_dir=data_dir)

    def discover_for_developer(self, system_id, job_id=None, job_manager=None, download=False, auto_register=True):
        """
        Discovers and optionally registers new investments for a developer by ID.
        Saves a snapshot of found items to Public/USIdev/{dev}/discovery.json.
        """
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir, self.data_dir.parent / "USIdev")
        dev = dm.get_developer_by_id(system_id)
        if not dev:
            raise ValueError(f"Developer with ID {system_id} not found")

        dev_slug = dev.get("developer_slug")
        if not dev_slug:
             raise ValueError(f"Developer {system_id} has no associated slug.")

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
                    results.extend(self.gateway.list_investments(portal, str(idx)))
                
                portal_key = "rp" if portal == "rp" else ("otodom" if portal == "oto" else "to")
                filtered = filter_new_investments(results, portal_key, dm.get_existing_identifiers())
                all_discovered.extend(filtered)
                
                new_found = [item for item in filtered if item.get("is_new")]
                
                for item in new_found:
                    if auto_register and not download:
                        # Determine source key
                        portal_key_isvc = "rp" if portal == "rp" else ("oto" if portal == "otodom" else "to")
                        vendor_id = self.gateway.resolve_path(item, "vendor.id|ad.agency.id|agency_id|developer_id")
                        item_id = item.get("id") or item.get("hash_id")
                        
                        self.isvc.register_investment(
                            portal=portal_key_isvc,
                            developer_name=item.get("developer_name") or item.get("developer"),
                            name=item.get("name") or item.get("title") or f"Inwestycja {portal_key_isvc.upper()} {item_id}",
                            item_id=item_id,
                            url=item.get("url"),
                            allow_existing=True,
                            vendor_id=vendor_id
                        )
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
        from python_worker.developer_repository import DeveloperRepository
        repo = DeveloperRepository(self.data_dir, self.data_dir.parent / "USIdev")
        repo.save_discovery_snapshot(system_id, all_discovered)

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

    def get_unregistered_count(self, system_id: str, identifiers: dict = None) -> int:
        """Returns count of items in discovery.json that are not yet registered."""
        from python_worker.developer_manager import DeveloperManager
        return DeveloperManager(self.data_dir).get_unregistered_count(system_id, identifiers)

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
            # Wywołanie przez bramę
            results = self.gateway.discover_investments(portal_key, identifier=identifier, limit=limit)

            logger.info(f"Scraper library returned {len(results)} items for {portal}")
            
            from python_worker.developer_manager import DeveloperManager
            dm = DeveloperManager(self.data_dir)
            filtered = filter_new_investments(results, portal_key, dm.get_existing_identifiers())
            logger.info(f"Filtered results: {len(filtered)} items")
            return filtered
        except Exception as e:
            logger.error(f"Error during discovery for {portal}: {e}", exc_info=True)
            raise
