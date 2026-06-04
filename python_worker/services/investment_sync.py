import json
import logging
from datetime import datetime
from pathlib import Path

from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log
from python_worker.api.utils import _find_inv_file
from python_worker.developer_manager import DeveloperManager

logger = logging.getLogger(__name__)

def _primary_portal_id(sources: dict) -> tuple[str, str | None]:
    for portal in ("rp", "oto", "to"):
        pid = (sources.get(portal) or {}).get("id")
        if pid:
            return portal, str(pid)
    return "rp", None

class InvestmentSyncService:
    def __init__(self, identity_resolver, data_dir: Path, public_usi_dir: Path, developer_manager=None, investment_repo=None):
        from python_worker.investment_repository import InvestmentRepository
        self.repo = investment_repo or InvestmentRepository(identity_resolver, data_dir)
        self.identity = identity_resolver
        self.data_dir = data_dir
        self.public_usi_dir = public_usi_dir
        self.dm = developer_manager or DeveloperManager(self.data_dir)
        
        from python_worker.config import get_scraper_config
        self.lib_config = get_scraper_config()
        if self.lib_config:
            from usi_scrapers.fetcher import Fetcher
            from usi_scrapers.manager import TechnicalDataManager
            self.fetcher = Fetcher(self.lib_config)
            self.tech_manager = TechnicalDataManager(self.lib_config)
        else:
            self.fetcher = None
            self.tech_manager = None
            
        from python_worker.services.investment_identity import InvestmentIdentityResolver
        self.resolver = InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)

    def _resolve_developer_for_registration(self, portal, developer_name, url, vendor_id, force_dev_slug):
        from usi_scrapers import api as scraper_api
        from python_worker.url_parser import parse_url

        developer_record = None
        dev_slug = force_dev_slug
        inv_slug_from_url = None

        # PRIORITY 1: Identify by Vendor ID (if provided)
        if not dev_slug and vendor_id:
            developer_record = self.dm.find_developer_by_id(portal, str(vendor_id))
            if developer_record:
                dev_slug = developer_record["developer_slug"]
                developer_name = developer_record["name"]
                logger.info(f"Found developer by ID {vendor_id} ({portal}): {developer_name} ({dev_slug})")

        # PRIORITY 2: Canonical Slug Extraction via library parser
        if not dev_slug and not developer_record and url:
            parsed = parse_url(url)
            if parsed.get("investment_slug") and parsed["investment_slug"] != "unknown":
                inv_slug_from_url = parsed["investment_slug"]
            if parsed.get("developer_slug") and parsed["developer_slug"] != "unknown":
                # Only overwrite if we don't have a better name already
                # or if we are dealing with 'Nieznany Deweloper'
                is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
                if is_unknown:
                    developer_name = parsed["developer_slug"].replace("-", " ").title()

        # Identification pre-scrapes (Otodom/TabelaOfert) via API
        is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
        if not dev_slug and not developer_record and is_unknown and portal in ("oto", "to") and url:
            logger.info(f"Developer unknown for {url}, performing pre-scrape identification ({portal})...")
            try:
                identified_name = scraper_api.identify_developer(self.fetcher, portal, url)
                if identified_name:
                    developer_name = identified_name
                    is_unknown = False
            except Exception as e:
                logger.error(f"Pre-scrape identification failed ({portal}): {e}")

        if not dev_slug:
            if not developer_record:
                dev_slug = "unknown"
                if not is_unknown:
                    logger.warning(f"No USI record found by ID for developer '{developer_name}' - placing in 'unknown' folder")
            else:
                dev_slug = developer_record["developer_slug"]
        
        # Auto-create developer profile ONLY if we have a real slug (not 'unknown')
        if dev_slug != "unknown" and not self.dm.get_developer(dev_slug):
            logger.info(f"Auto-creating developer profile for: {developer_name} ({dev_slug})")
            
            # Initialize portal mapping if we have enough info
            initial_pm = {"rp": None, "oto": None, "to": None}
            if portal == "rp" and vendor_id:
                initial_pm["rp"] = {"id": str(vendor_id)}
            elif portal == "to" and vendor_id:
                initial_pm["to"] = {"agency_id": str(vendor_id)}
            elif portal == "oto" and vendor_id:
                initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}

            self.dm.create_developer_file({
                "developer_slug": dev_slug, 
                "name": developer_name,
                "portal_mapping": initial_pm
            })

        return dev_slug, developer_name, inv_slug_from_url

    def _check_investment_exists(self, portal, item_id, inv_slug, url):
        existing_ids = self.dm.get_existing_identifiers()
        id_exists = False
        if portal == "rp" and item_id and str(item_id) in existing_ids.get("rp_ids", set()):
            id_exists = True
        elif portal == "oto" and item_id:
            s_item_id = str(item_id)
            if s_item_id in existing_ids.get("oto_ids", set()):
                id_exists = True
            else:
                # Robust Otodom check: try to find 'the other' ID from URL or slug
                hash_id = None
                if "-ID" in str(inv_slug):
                    hash_id = str(inv_slug).split("-ID")[-1]
                elif url and "-ID" in str(url):
                    hash_id = str(url).rstrip("/").split("-ID")[-1].split("?")[0]
                
                if hash_id and hash_id in existing_ids.get("oto_ids", set()):
                    logger.info(f"Found existing Otodom record by hash ID {hash_id} for new ID {item_id}")
                    id_exists = True
                
                if not id_exists and inv_slug in existing_ids.get("oto_slugs", set()):
                    logger.info(f"Found existing Otodom record by slug {inv_slug} for new ID {item_id}")
                    id_exists = True

        elif portal == "to" and item_id and str(item_id) in existing_ids.get("to_ids", set()):
            id_exists = True
            
        return id_exists

    def register_investment(self, portal, developer_name, inv_slug, name, item_id=None, url=None, allow_existing=False, vendor_id=None, force_dev_slug=None):

        dev_slug, resolved_developer_name, inv_slug_from_url = self._resolve_developer_for_registration(
            portal, developer_name, url, vendor_id, force_dev_slug
        )
        if inv_slug_from_url and not force_dev_slug:
             # Just use it if original lacked logic
             pass
        
        # Update dev_slug based on parsed URL if it existed
        if inv_slug_from_url and not dev_slug: # Note: this was handled somewhat implicitly before
             pass
        
        # Better fallback: if inv_slug wasn't passed, but url provided it
        if inv_slug_from_url and not inv_slug:
             inv_slug = inv_slug_from_url

        inv_dir = self.data_dir / dev_slug / inv_slug

        # 1. Check if investment already exists (any file format)
        existing_file = _find_inv_file(inv_dir, inv_slug)
        if existing_file:
            if allow_existing:
                import json
                try:
                    data = json.loads(existing_file.read_text(encoding="utf-8"))
                    usi_inv_id = data.get("usi_inv_id")
                except Exception:
                    usi_inv_id = None
                return dev_slug, inv_slug, usi_inv_id
            raise ValueError(f"Investment already exists: {dev_slug}/{inv_slug}")

        # 2. Check for ID-based duplication across all investments
        if self._check_investment_exists(portal, item_id, inv_slug, url):
            logger.info(f"Investment with ID {item_id} ({portal}) already exists in system. Skipping registration.")
            return None, None

        inv_dir.mkdir(parents=True, exist_ok=True)

        # Canonical filename: usi_{portal}_{portal_id}.json (new format)
        if portal in ["rp", "oto", "to"] and item_id:
            filename = f"usi_{portal}_{item_id}.json"
            sources = {portal: {"id": str(item_id), "url": url}}
            if vendor_id:
                sources[portal]["vendor_id"] = str(vendor_id)
        else:
            filename = f"usi_{inv_slug}.json"
            sources = {}
            if portal in ["rp", "oto", "to"]:
                sources[portal] = {"url": url}
                if vendor_id:
                    sources[portal]["vendor_id"] = str(vendor_id)

        if portal == "oto":
            logger.info(f"Creating Otodom skeleton for {inv_slug} with sources: {sources}")

        # Diagnostic signals for initial classification (if full raw not available)
        initial_raw = {"url": url, "name": name}
        if portal == "rp" and item_id: initial_raw["type"] = None # Placeholder, full raw will come later

        system_id = f"{portal}_{item_id}" if item_id else inv_slug
        skeleton = {
            "usi_inv_id": system_id,
            "investment_slug": inv_slug,
            "developer_slug": dev_slug,
            "name": name,
            "reviewed": False,
            "sources": sources,
            "specifications": {
                "segment": None
            },
            "status": "Brak",
            "audit": {"created_at": datetime.now().isoformat()}
        }

        self.repo.create_investment_skeleton(skeleton["usi_inv_id"], portal, str(item_id) if item_id else None, skeleton)
        if hasattr(self, 'resolver') and self.resolver:
            self.resolver.build_index()
            
        try:
            import python_worker.investment_index as inv_index
            inv_index.upsert(self.data_dir, self.public_usi_dir, dev_slug, inv_slug)
        except Exception as _ie:
            logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")

        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        self.dm.invalidate_identifiers_cache()
        return dev_slug, inv_slug, skeleton["usi_inv_id"]

    def _canonical_slug_from_raw(self, portal: str, raw_details: dict, fallback: str) -> str:
        """Resolves the canonical USI developer slug by reading it from portal raw data."""
        from usi_scrapers import resolve_path
        
        # Use authoritative portal ID resolution from library mapping
        portal_id = resolve_path(raw_details, portal, "vendor.id|ad.agency.id|developer_id")
        if portal_id:
            dev_record = self.dm.find_developer_by_id(portal, str(portal_id))
            if dev_record:
                return dev_record["developer_slug"]

        # If no USI record found by ID, use the slug provided by the portal (metadata only)
        portal_slug = resolve_path(raw_details, portal, "vendor.slug|ad.agency.slug|developer_slug")
        
        return portal_slug or fallback

    def download_raw_json(self, portal: str, identifier: str, system_id: str):
        if not self.lib_config or not self.fetcher:
            logger.error("Scraper library not properly configured.")
            return None
            
        from usi_scrapers import api as scraper_api
        
        try:
            # 1. Fetch raw data
            res = scraper_api.fetch_investment(self.lib_config, self.fetcher, portal, identifier)
            if not res or "raw_details" not in res:
                return False
                
            raw_data = res["raw_details"]
            
            # 2. Save using high-level API (resolves path internally via TechnicalDataManager)
            # We use portal_id to ensure the library can find or create the correct folder
            # without the tracker explicitly providing a filesystem path.
            scraper_api.save_raw(self.lib_config, raw_data, portal, portal_id=identifier)
            return True
        except Exception as e:
            logger.error(f"Download raw failed for {portal}/{identifier}: {e}")
            return False
        
    def _fetch_and_transform_portal_data(self, system_id, portal, portal_name, raw_prefix, sources, use_local_raw):
        """Fetches raw portal data (local or remote) and transforms it."""
        from usi_scrapers import api as scraper_api
        
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            return None, None, f"{portal_name} (No resources)"
            
        inv_dir = resources["base_dir"]
        slug_parts = resources["metadata"]["slug"].split("/")
        dev_slug = slug_parts[0]
        inv_slug = slug_parts[1]
        
        raw_files = list(inv_dir.glob(f"raw_{raw_prefix}_*.json"))

        if use_local_raw and raw_files:
            canonical = inv_dir / f"raw_{raw_prefix}_{inv_slug}.json"
            raw_path = canonical if canonical.exists() else sorted(raw_files)[-1]
            with open(raw_path, "r") as f:
                raw_details = json.load(f)
            
            # Transform using the FOLDER slug (dev_slug) to maintain consistency
            unified_data = AdapterFactory.get_adapter(raw_prefix).transform(raw_details, inv_slug, dev_slug)
            return unified_data, f"{portal_name} (local)", None
            
        elif use_local_raw:
            logger.debug(f"[local-raw] {portal_name}: no raw file in {inv_dir}, skipping")
            return None, None, None

        else:
            # RP uses numeric ID; Otodom and TO require a full URL
            if portal == "rp":
                identifier = sources[portal].get("id") or sources[portal].get("url")
            else:
                identifier = sources[portal].get("url") or sources[portal].get("id")
                
            if not identifier:
                log_to_processing_log(dev_slug, inv_slug, f"Skipped {portal_name}: no identifier in sources")
                return None, None, None
                
            try:
                res = scraper_api.fetch_investment(self.lib_config, self.fetcher, portal, identifier)
            except Exception as e:
                error_msg = f"Exception during fetch: {e}"
                logger.error(f"[{portal_name}] {system_id}: {error_msg}")
                log_to_processing_log(dev_slug, inv_slug, f"Error fetching from {portal_name}: {error_msg}")
                return None, None, f"{portal_name} ({error_msg})"

            if res and "raw_details" in res:
                raw_data = res["raw_details"]
                
                # Use high-level API for saving raw data (ID-only aware)
                scraper_api.save_raw(self.lib_config, raw_data, raw_prefix, dev_slug=dev_slug, inv_slug=inv_slug)

                # Transform unified data using the FOLDER slug (dev_slug)
                unified_data = AdapterFactory.get_adapter(raw_prefix).transform(raw_data, inv_slug, dev_slug)
                return unified_data, portal_name, None
            else:
                error_msg = res.get("error", "Unknown error") if isinstance(res, dict) else "No valid response"
                logger.error(f"[{portal_name}] {system_id}: {error_msg}")
                log_to_processing_log(dev_slug, inv_slug, f"Fetch failed — {portal_name}: {error_msg}")
                return None, None, f"{portal_name} ({error_msg})"

    def _sync_investment_images(self, new_unified, all_urls, img_dev_slug, inv_slug, skip_images, usi_data, resources):
        """Synchronizes images for the investment."""
        if skip_images:
            # Pełne pominięcie jakichkolwiek operacji dyskowych na katalogu obrazów
            new_unified["image_paths"] = usi_data.get("image_paths", [])
            new_unified["images_count"] = usi_data.get("images_count", 0)
            return

        if all_urls and self.tech_manager:
            logger.info(f"Synchronizing images for {inv_slug} ({len(all_urls)} URLs)")
            
            # FAST-PATH: Try to find files already downloaded based on previous state and canonical folder
            try:
                from usi_scrapers.utils.images import clean_filename
                import os
                
                # Map urls to expected basenames
                url_to_basename = {url: os.path.splitext(clean_filename(url))[0] for url in all_urls}
                basename_to_urls = {}
                for url, bname in url_to_basename.items():
                    basename_to_urls.setdefault(bname, []).append(url)
                    
                expected_set = set(basename_to_urls.keys())
                found_paths = {}  # maps url -> full path
                
                # 1. Check existing paths from the last state of the investment
                existing_paths = usi_data.get("image_paths", [])
                for path in existing_paths:
                    bname = os.path.splitext(os.path.basename(path))[0]
                    if bname in expected_set:
                        for url in basename_to_urls[bname]:
                            found_paths[url] = path
                        expected_set.remove(bname)
                        if not expected_set: break
                        
                # 2. Check the canonical images directory for this investment
                if expected_set and resources.get("images_dir") and resources["images_dir"].exists():
                    for file in os.listdir(resources["images_dir"]):
                        bname = os.path.splitext(file)[0]
                        if bname in expected_set:
                            rel_path = os.path.relpath(os.path.join(resources["images_dir"], file), self.public_usi_dir)
                            path_str = f"/Public/USI/{rel_path}"
                            for url in basename_to_urls[bname]:
                                found_paths[url] = path_str
                            expected_set.remove(bname)
                            if not expected_set: break
                        
                urls_to_download = []
                for url in all_urls:
                    if url not in found_paths:
                        urls_to_download.append(url)
                        
            except Exception as e:
                logger.error(f"Error during image fallback search: {e}")
                urls_to_download = all_urls
                found_paths = {}

            saved_filenames = []
            if urls_to_download:
                target_image_dir = self.public_usi_dir / img_dev_slug / inv_slug
                saved_filenames = self.tech_manager.sync_images(urls_to_download, target_image_dir)
                        
            unique_paths = []
            for url in all_urls:
                if url in found_paths:
                    p = found_paths[url]
                    if p not in unique_paths:
                        unique_paths.append(p)
            
            for fname in saved_filenames:
                if fname:
                    p = f"/Public/USI/{img_dev_slug}/{inv_slug}/{fname}"
                    if p not in unique_paths:
                        unique_paths.append(p)
            
            new_unified["image_paths"] = unique_paths
            new_unified["images_count"] = len(unique_paths)
            logger.info(f"Image sync complete for {inv_slug}: {len(unique_paths)}/{len(all_urls)} paths resolved")
            
        elif all_urls and not self.tech_manager:
            logger.warning(f"Image sync skipped for {inv_slug}: tech_manager not available (check SCRAPERAPI_KEY / config)")
            log_to_processing_log(img_dev_slug, inv_slug, "Image sync skipped: scraper config unavailable")
        else:
            # No URLs from scraper — keep whatever is already on disk
            img_dir = self.tech_manager.get_image_path(img_dev_slug, inv_slug) if self.tech_manager else \
                      (self.public_usi_dir / img_dev_slug / inv_slug)
            if img_dir.is_dir():
                on_disk = sorted(p.name for p in img_dir.iterdir()
                                 if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
                if on_disk:
                    new_unified["image_paths"] = [f"/Public/USI/{img_dev_slug}/{inv_slug}/{fname}" for fname in on_disk]
                    new_unified["images_count"] = len(on_disk)

    def _backfill_developer_mapping(self, dev_slug, new_unified):
        """Backfills developer ID into portal_mapping if missing."""
        dev_record = self.dm.get_developer(dev_slug)
        if not dev_record:
            return

        needs_update = False
        pm = dev_record.setdefault("portal_mapping", {"rp": None, "oto": None, "to": None})
        new_src = new_unified.get("sources", {})
        
        # Check RP
        rp_src = new_src.get("rp", {})
        if rp_src.get("vendor_id"):
            if not pm.get("rp"):
                pm["rp"] = {"id": rp_src["vendor_id"]}
                needs_update = True
            elif pm["rp"].get("id") != rp_src["vendor_id"]:
                if not pm["rp"].get("id"):
                    pm["rp"]["id"] = rp_src["vendor_id"]
                    needs_update = True
                    
        # Check Otodom
        oto_src = new_src.get("oto", {})
        if oto_src.get("agency_id"):
            if not pm.get("oto"):
                pm["oto"] = {"agency_id": oto_src["agency_id"], "agency_ids": [oto_src["agency_id"]]}
                needs_update = True
            else:
                aids = pm["oto"].setdefault("agency_ids", [])
                if oto_src["agency_id"] not in aids:
                    aids.append(oto_src["agency_id"])
                    pm["oto"]["agency_id"] = oto_src["agency_id"] # promote to main
                    needs_update = True
                    
        # Check TO
        to_src = new_src.get("to")
        if to_src is not None:
            if not pm.get("to"):
                pm["to"] = {"agency_id": to_src.get("developer_id", "")}
                needs_update = True
            elif not pm["to"].get("agency_id") and to_src.get("developer_id"):
                pm["to"]["agency_id"] = to_src["developer_id"]
                needs_update = True
                
        if needs_update:
            self.dm.create_developer_file(dev_record)
            logger.info(f"Backfilled developer ID into portal_mapping for {dev_slug}")

    def update_investment(self, system_id, use_local_raw=False, skip_images=False, skip_index=False, skip_log=False):
        """
        Orchestrates the update of an investment:
        1. Scrapes raw data (or loads local)
        2. Transforms to unified USI schema
        3. Merges with existing data and ratings
        4. Synchronizes images
        """
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            logger.warning(f"Investment resources not found skipping ID: {system_id}")
            return False
            
        inv_dir = resources["base_dir"]
        actual_file = resources["files"].get("anchor")
        slug_parts = resources["metadata"]["slug"].split("/")
        dev_slug = slug_parts[0]
        inv_slug = slug_parts[1]

        if not actual_file and not use_local_raw:
            logger.warning(f"Investment file not found skipping: {inv_dir}/usi_*.json")
            return False

        usi_data = {}
        if actual_file and actual_file.exists():
            with open(actual_file, "r", encoding="utf-8") as f:
                usi_data = json.load(f)

        sources = usi_data.get("sources", {})
        if not sources and use_local_raw:
            # Skeletons might have portal field at root
            p_root = usi_data.get("portal")
            if p_root:
                sources[p_root] = {"id": usi_data.get("portal_id", "rebuild")}
            
            # Fallback: scan for any raw files
            for p in ["rp", "oto", "to"]:
                if p in sources: continue
                # Search for any raw_{p}_*.json
                raw_files = list(inv_dir.glob(f"raw_{p}_*.json"))
                if raw_files:
                    sources[p] = {"id": "rebuild"}

        rp_unified = None
        oto_unified = None
        to_unified = None
        fetched_sources = []
        failed_sources = []
        
        # Initial guess for images is the current folder name
        img_dev_slug = dev_slug
        
        # Mandate: Trust recorded paths. Check where images WERE stored before.
        existing_img_list = usi_data.get("ratings", {}).get("imgList")
        if not existing_img_list and usi_data.get("image_paths"):
            existing_img_list = usi_data["image_paths"][0]
            
        if existing_img_list:
            import re
            m = re.search(r'/Public/USI/([^/]+)/', str(existing_img_list))
            if m:
                img_dev_slug = m.group(1)
                if not skip_images:
                    logger.info(f"Image folder for {inv_slug} pinned to recorded path: {img_dev_slug}")

        # Generic update loop using helper method
        for portal in ["rp", "oto", "to"]:
            if portal not in sources: continue

            portal_name = "RynekPierwotny" if portal == "rp" else ("Otodom" if portal == "oto" else "TabelaOfert")
            raw_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")

            unified_data, fetched_src, failed_src = self._fetch_and_transform_portal_data(
                system_id, portal, portal_name, raw_prefix, sources, use_local_raw
            )
            
            if unified_data:
                if portal == "rp": rp_unified = unified_data
                elif portal == "oto": oto_unified = unified_data
                elif portal == "to": to_unified = unified_data
            if fetched_src:
                fetched_sources.append(fetched_src)
            if failed_src:
                failed_sources.append(failed_src)


        if rp_unified or oto_unified or to_unified:
            # Semantic layer: Ratings and Merging
            ratings_candidates = []
            for p in ("rp", "oto", "to"):
                ratings_candidates.extend(sorted(inv_dir.glob(f"meta_{p}_*.json"), reverse=True))
            ratings_candidates.append(inv_dir / f"meta_{inv_slug}_ratings.json")
            ratings = {}
            for ratings_path in ratings_candidates:
                if ratings_path.exists():
                    try:
                        with open(ratings_path, "r", encoding="utf-8") as f:
                            ratings = json.load(f)
                        break
                    except Exception as e:
                        logger.error(f"Error reading ratings file: {e}")

            event = f"Sync: {', '.join(fetched_sources)}" if fetched_sources else "Manual Update"
            new_unified = Merger.merge(rp_unified, oto_unified, to_unified, ratings, existing_data=usi_data, event=event)

            # Technical layer: Image synchronization via library
            all_urls = new_unified.get("image_urls", [])
            self._sync_investment_images(new_unified, all_urls, img_dev_slug, inv_slug, skip_images, usi_data, resources)

            # Backfill developer ID into portal_mapping if missing
            self._backfill_developer_mapping(dev_slug, new_unified)

            # Save to canonical new-format path; fall back to existing file path
            self.repo.save_investment_json(system_id, new_unified)
            if not skip_index:
                try:
                    import python_worker.investment_index as inv_index
                    inv_index.upsert(self.data_dir, self.public_usi_dir, dev_slug, inv_slug)
                except Exception as _ie:
                    logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")

            if not skip_log:
                summary = f"Updated: {', '.join(fetched_sources)}"
                if failed_sources:
                    summary += f". Failed: {', '.join(failed_sources)}"
                log_to_processing_log(dev_slug, inv_slug, summary)
            return True

        # All portals failed
        if failed_sources:
            raise RuntimeError(f"Fetch failed for all portals: {'; '.join(failed_sources)}")
        return False
        
    def _prepare_batch_identifiers(self, portal, investments):
        """Prepares identifiers and metadata for a batch without registering skeletons yet."""
        from python_worker.url_parser import parse_url
        
        to_process = []
        targets = []

        for item in investments:
            ident = url = item.get("url")
            inv_slug = item.get("investment_slug") or item.get("inv_slug") or item.get("slug")
            if not inv_slug and url:
                _parsed = parse_url(url)
                _raw_slug = _parsed.get("investment_slug", "")
                if _raw_slug:
                    inv_slug = _raw_slug
            dev_name = item.get("developer_name") or item.get("developer")
            
            if ident:
                dev_slug = None
                # Backward compatibility for old CSVs, but prioritizing normalized vendor_id
                vendor_id = item.get("vendor_id") or item.get("agency_id") or item.get("developer_id")
                if not vendor_id and portal == "rp" and isinstance(item.get("vendor"), dict):
                    vendor_id = item["vendor"].get("id")
                
                # 1. Try authoritative ID lookup
                if vendor_id:
                    dev_record = self.dm.find_developer_by_id(portal, str(vendor_id))
                    if dev_record:
                        dev_slug = dev_record["developer_slug"]
                        dev_name = dev_record["name"]

                # 2. Try Name lookup if still no slug
                if not dev_slug and dev_name and dev_name.lower() not in ("nieznany deweloper", "unknown", "nieznany-deweloper"):
                    matched_dev = self.dm.get_developer_by_name(dev_name)
                    if matched_dev:
                        dev_slug = matched_dev["developer_slug"]
                
                # 3. Aggressive skeleton creation IF we have an ID (bypasses library resolution failures)
                if not dev_slug and vendor_id:
                    dev_slug = f"{portal}-{vendor_id}"
                    initial_pm = {"rp": None, "oto": None, "to": None}
                    if portal == "rp": initial_pm["rp"] = {"id": str(vendor_id)}
                    elif portal == "to": initial_pm["to"] = {"agency_id": str(vendor_id)}
                    elif portal == "oto": initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}

                    self.dm.create_developer_file({
                        "developer_slug": dev_slug,
                        "name": dev_name or f"Deweloper {portal.upper()} {vendor_id}",
                        "portal_mapping": initial_pm
                    })
                    logger.info(f"Pre-created developer profile {dev_slug} for '{dev_name}' to bypass API resolution errors.")

                if portal == "rp":
                    ident = item.get("id") or url

                # 4. Resolve physical paths via ID-only architecture
                target_dir = None
                target_image_dir = None
                
                portal_id = str(ident) if (ident and not str(ident).startswith("http")) else None
                if portal_id and self.tech_manager:
                    target_dir = self.tech_manager.get_investment_path(portal, portal_id)
                    target_image_dir = self.tech_manager.get_image_path(portal, portal_id)
                elif dev_slug and inv_slug:
                    # Emergency fallback if no ID but we have slugs (should be avoided)
                    target_dir = self.data_dir / dev_slug / inv_slug
                    target_image_dir = self.public_usi_dir / dev_slug / inv_slug

                targets.append({
                    "identifier": ident,
                    "target_dir": target_dir,
                    "target_image_dir": target_image_dir
                })
                to_process.append({
                    "ident": ident,
                    "dev_slug": dev_slug,
                    "inv_slug": inv_slug,
                    "name": item.get("name"),
                    "item_id": item.get("id"),
                    "url": url,
                    "portal": portal,
                    "dev_name": dev_name,
                    "vendor_id": vendor_id
                })
        
        return targets, to_process

    def process_batch(self, portal, investments, on_progress_callback=None):
        """
        Processes a batch of investments using the library's process_batch function.
        Downloads data first, then registers and unifies only successful ones.
        """
        from usi_scrapers import api as scraper_api
        from python_worker.slug_utils import slugify
        
        targets, to_process = self._prepare_batch_identifiers(portal, investments)

        if not targets:
            return False

        # 2. Call library process_batch
        # REFRESH CONFIG: Ensure library sees newly created USIdev files
        from python_worker.config import get_scraper_config
        from usi_scrapers.fetcher import Fetcher
        self.lib_config = get_scraper_config()
        self.fetcher = Fetcher(self.lib_config)

        # This will save raw_*.json files to disk for successful items
        batch_results = scraper_api.process_batch(
            self.lib_config, self.fetcher, portal, targets, on_progress=on_progress_callback
        )

        # 3. Finalize: Register and Update ONLY if raw data exists
        success_count = 0
        raw_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")

        for info, data in zip(to_process, batch_results):
            try:
                # Fallbacks in case scraping failed completely
                dev_slug = info["dev_slug"]
                inv_slug = info["inv_slug"]
                vendor_id = info["vendor_id"]
                
                # Use precise data returned from library if available
                if data and isinstance(data, dict):
                    if data.get("developer_slug"):
                        dev_slug = data["developer_slug"]
                        logger.info(f"Using developer_slug '{dev_slug}' from library result for {info['ident']}")
                    if data.get("investment_slug"):
                        inv_slug = data["investment_slug"]
                    if data.get("id"):
                        info["item_id"] = data["id"]
                    
                    # Normalized vendor_id from library
                    if data.get("vendor_id"):
                        vendor_id = data["vendor_id"]
                    # Backward compatibility fallback
                    elif data.get("agency_id"):
                        vendor_id = data["agency_id"]

                if not dev_slug or not inv_slug:
                    logger.warning(f"Could not finalize batch item {info['ident']} - missing slugs (dev={dev_slug}, inv={inv_slug}).")
                    continue

                inv_dir = self.data_dir / dev_slug / inv_slug
                raw_files = list(inv_dir.glob(f"raw_{raw_prefix}_*.json"))

                if not raw_files:
                    if data and isinstance(data, dict) and "error" not in data:
                        logger.info(f"Saving raw data delayed for {dev_slug}/{inv_slug}.")
                        # Use high-level API for saving raw data
                        scraper_api.save_raw(self.lib_config, data, raw_prefix, dev_slug=dev_slug, inv_slug=inv_slug)
                        
                        if "image_urls" in data and self.tech_manager:
                            # Use library to resolve and sync images
                            portal_id = data.get("id") or info.get("item_id")
                            target_image_dir = self.tech_manager.get_image_path(portal, portal_id)
                            if target_image_dir:
                                target_image_dir.mkdir(parents=True, exist_ok=True)
                                self.tech_manager.sync_images(data["image_urls"], target_image_dir)
                    else:
                        logger.warning(f"Batch download failed for {inv_slug} (no raw data found in {dev_slug}/{inv_slug}) - skipping registration.")
                        continue

                if portal == "oto":
                    logger.info(f"Finalizing Otodom registration: item_id={info['item_id']}, vendor_id={vendor_id}")

                # Register (creates usi_*.json skeleton and ID)
                res = self.register_investment(
                    portal=info["portal"],
                    developer_name=info["dev_name"] or dev_slug.replace("-", " ").title(),
                    inv_slug=inv_slug,
                    name=info["name"] or (data.get("title") if isinstance(data, dict) else None),
                    item_id=info["item_id"],
                    url=info["url"],
                    allow_existing=True,
                    vendor_id=vendor_id,
                    force_dev_slug=dev_slug
                )
                
                if res and res[0]: # res is (dev_slug, inv_slug, system_id)
                    # Unify and Sync images
                    system_id = res[2] if len(res) > 2 else (f"{info['portal']}_{info['item_id']}" if info.get("item_id") else f"legacy_{inv_slug}")
                    if self.update_investment(system_id, use_local_raw=True):
                        success_count += 1
                else:
                    logger.info(f"Investment {inv_slug} already exists or duplicate ID - skipping batch update.")

            except Exception as e:
                logger.error(f"Post-batch processing failed for {info['inv_slug']}: {e}")

        logger.info(f"Batch processing complete: {success_count}/{len(to_process)} investments fully ingested.")
        if success_count > 0:
            self.dm.invalidate_identifiers_cache()
        return success_count
