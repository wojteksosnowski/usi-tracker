import json
import logging
from datetime import datetime
from pathlib import Path

from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log
from python_worker.developer_manager import DeveloperManager
from python_worker.services.amenity_scorer import compute_amenity_score, suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images
from python_worker.api.utils import _calculate_distance
import python_worker.investment_index as inv_index

logger = logging.getLogger(__name__)

PORTAL_NAMES = {"rp": "RynekPierwotny", "oto": "Otodom", "to": "TabelaOfert"}
PORTAL_FULL_DOMAINS = {"rp": "rynekpierwotny.pl", "oto": "otodom.pl", "to": "tabelaofert.pl"}
IDENTIFIER_PRIORITIES = {
    "rp": ["id", "url"],
    "oto": ["url", "id"],
    "to": ["url", "id"]
}
PORTAL_VENDOR_ID_KEYS = {
    "rp": lambda vid: {"id": str(vid)},
    "to": lambda vid: {"agency_id": str(vid)},
    "oto": lambda vid: {"agency_id": str(vid), "agency_ids": [str(vid)]}
}

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
        
        # 2. SPÓJNA INICJALIZACJA Z JEDNEGO ŹRÓDŁA (Podejście współdzielone/Singleton)
        from python_worker.config import get_shared_config, get_shared_fetcher, get_shared_tech_manager
        self._lib_config = get_shared_config()
        self._fetcher = get_shared_fetcher()          # Inicjalizacja raz na żywotność serwera
        self._tech_manager = get_shared_tech_manager()  # Inicjalizacja raz na żywotność serwera
        self._image_sync = None
            
        from python_worker.services.investment_identity import InvestmentIdentityResolver
        self.resolver = InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)
        
        from python_worker.services.developer_resolver import DeveloperResolver
        self.developer_resolver = DeveloperResolver(self.dm, self, self.identity)

    # 3. CZYSZCZENIE GETTERÓW/SETTERÓW (Są teraz prostsze i bezpieczne)
    @property
    def lib_config(self):
        return self._lib_config

    @property
    def fetcher(self):
        return self._fetcher

    @fetcher.setter
    def fetcher(self, value):
        self._fetcher = value

    @property
    def tech_manager(self):
        return self._tech_manager

    @tech_manager.setter
    def tech_manager(self, value):
        self._tech_manager = value

    @property
    def image_sync(self):
        if self._image_sync is None:
            from python_worker.services.image_sync import ImageSyncService
            self._image_sync = ImageSyncService(self.tech_manager, self.public_usi_dir)
        return self._image_sync

    def _check_investment_exists(self, portal, item_id):
        if not item_id:
            return False
        
        full_portal = PORTAL_FULL_DOMAINS.get(portal)
        if not full_portal:
            return False
            
        # Bezpośrednie, szybkie użycie czystego API (import wewnątrz by uniknąć problemów z sys.path)
        from usi_scrapers import api as scraper_api
        data = scraper_api.get_raw_data(self.lib_config, portal=full_portal, portal_id=str(item_id))
        return data is not None

    def register_investment(self, portal, developer_name, name, item_id=None, url=None, allow_existing=False, vendor_id=None, force_dev_slug=None):

        dev_slug, resolved_developer_name, inv_slug_from_url = self.developer_resolver.resolve_developer_for_registration(
            portal, developer_name, url, vendor_id, force_dev_slug
        )
        
        inv_slug = inv_slug_from_url
        
        # Resolve investment directory via TechnicalDataManager
        if self.tech_manager and portal and item_id:
            inv_dir = self.tech_manager.get_investment_path(portal, str(item_id))
            inv_slug = inv_dir.name
        else:
            if not inv_slug:
                from slugify import slugify
                inv_slug = slugify(name) if name else (str(item_id) if item_id else "unknown")
            inv_dir = self.data_dir / dev_slug / inv_slug

        # 1. Check if investment already exists (any file format)
        existing_file = None
        if portal and item_id:
            target_anchor = inv_dir / f"usi_{portal}_{item_id}.json"
            if target_anchor.exists():
                existing_file = target_anchor
        
        if not existing_file:
            usi_files = [f for f in inv_dir.glob("usi_*.json") if "usi_dev_" not in f.name]
            if usi_files:
                existing_file = usi_files[0]

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
        if self._check_investment_exists(portal, item_id):
            logger.info(f"Investment with ID {item_id} ({portal}) already exists in system. Skipping registration.")
            return None, None

        if not inv_dir:
             raise RuntimeError(f"Could not determine investment directory for {portal}/{item_id}")
             
        inv_dir.mkdir(parents=True, exist_ok=True)

        # Canonical filename and source construction
        if portal in PORTAL_FULL_DOMAINS and item_id:
            filename = f"usi_{portal}_{item_id}.json"
            sources = {portal: {"id": str(item_id), "url": url}}
            if vendor_id:
                sources[portal].update(PORTAL_VENDOR_ID_KEYS.get(portal, lambda v: {})(vendor_id))
        else:
            filename = f"usi_{inv_slug}.json"
            sources = {}
            if portal in PORTAL_FULL_DOMAINS:
                sources[portal] = {"url": url}
                if vendor_id:
                    sources[portal].update(PORTAL_VENDOR_ID_KEYS.get(portal, lambda v: {})(vendor_id))

        # Diagnostic signals for initial classification
        initial_raw = {"url": url, "name": name}
        if portal == "rp" and item_id:
            initial_raw["type"] = None # Placeholder for classification

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
            inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=skeleton["usi_inv_id"])
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
                
            # 2. Save using high-level API (resolves path internally via TechnicalDataManager)
            # We use portal_id to ensure the library can find or create the correct folder
            # without the tracker explicitly providing a filesystem path.
            # Pass full 'res' (envelope) to allow internal slug extraction if new.
            scraper_api.save_raw(self.lib_config, res, portal, portal_id=identifier)
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
        m = resources["metadata"]
        dev_slug = m.get("developer_slug") or "unknown"
        inv_slug = m.get("investment_slug") or inv_dir.name
        
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
            fields = IDENTIFIER_PRIORITIES.get(portal, ["url", "id"])
            identifier = next((sources[portal].get(f) for f in fields if sources[portal].get(f)), None)
                
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
                # Use high-level API for saving raw data (ID-only aware)
                # Pass full response 'res' as envelope - library will extract slugs if needed for new investments,
                # or resolve via ID for existing ones.
                scraper_api.save_raw(self.lib_config, res, raw_prefix, portal_id=identifier)

                raw_data = res["raw_details"]
                # Transform unified data using the FOLDER slug (dev_slug)
                unified_data = AdapterFactory.get_adapter(raw_prefix).transform(raw_data, inv_slug, dev_slug)
                return unified_data, portal_name, None
            else:
                error_msg = res.get("error", "Unknown error") if isinstance(res, dict) else "No valid response"
                logger.error(f"[{portal_name}] {system_id}: {error_msg}")
                log_to_processing_log(dev_slug, inv_slug, f"Fetch failed — {portal_name}: {error_msg}")
                return None, None, f"{portal_name} ({error_msg})"

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
        
        m = resources["metadata"]
        dev_slug = m.get("developer_slug") or "unknown"
        inv_slug = m.get("investment_slug") or inv_dir.name

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

        unified_data_map = {"rp": None, "oto": None, "to": None}
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

            portal_name = PORTAL_NAMES.get(portal, portal)
            raw_prefix = portal

            unified_data, fetched_src, failed_src = self._fetch_and_transform_portal_data(
                system_id, portal, portal_name, raw_prefix, sources, use_local_raw
            )
            
            if unified_data:
                unified_data_map[portal] = unified_data
            if fetched_src:
                fetched_sources.append(fetched_src)
            if failed_src:
                failed_sources.append(failed_src)


        if any(unified_data_map.values()):
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
            new_unified = Merger.merge(unified_data_map["rp"], unified_data_map["oto"], unified_data_map["to"], ratings, existing_data=usi_data, event=event)

            # Technical layer: Image synchronization via library
            all_urls = new_unified.get("image_urls", [])
            self.image_sync.sync_investment_images(system_id, new_unified, all_urls, skip_images, usi_data, resources)

            # Backfill developer ID into portal_mapping if missing
            self.developer_resolver.backfill_developer_mapping(system_id, new_unified)

            # Compute amenities and metadata on save
            am_data = new_unified.get("amenities", {})
            labels = am_data.get("labels", [])
            raw_codes = am_data.get("raw_codes", [])
            score_data = compute_amenity_score(labels, raw_codes)
            
            new_unified["amenities_score"] = score_data["score"]
            new_unified["amenities_matched"] = score_data["matched"]
            new_unified["suggested_udogodnienia"] = suggest_udogodnienia(score_data["score"])
            
            # Use resolve_images to finalize photos list
            if resources:
                new_unified["photos"] = resolve_images(new_unified, inv_dir, self.public_usi_dir, resources, fast_index=False)
            else:
                new_unified["photos"] = resolve_images(new_unified, inv_dir, self.public_usi_dir, fast_index=False)

            new_unified["images_count"] = len(new_unified["photos"])

            # Task 06.01.02: Pre-calculate nearby investments if coords changed or missing
            old_coords = usi_data.get("location", {}).get("coords")
            new_coords = new_unified.get("location", {}).get("coords")

            needs_recalc = False
            if not usi_data.get("nearby_investments"):
                needs_recalc = True
            elif old_coords != new_coords:
                needs_recalc = True

            if needs_recalc:
                new_unified["nearby_investments"] = self._calculate_nearby_investments(system_id, new_coords)
            else:
                new_unified["nearby_investments"] = usi_data.get("nearby_investments", [])

            # Check deletion list
            deletion_file = inv_dir / "deletion_list.json"
            if deletion_file.exists():
                try:
                    dl = json.loads(deletion_file.read_text())
                    new_unified["photos_to_delete"] = len(dl.get("paths", []))
                except Exception:
                    new_unified["photos_to_delete"] = 0
            else:
                new_unified["photos_to_delete"] = 0

            # Save to canonical new-format path; fall back to existing file path
            self.repo.save_investment_json(system_id, new_unified)
            if not skip_index:
                try:
                    import python_worker.investment_index as inv_index
                    inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=system_id)
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

    def _calculate_nearby_investments(self, inv_id, coords, limit=12, max_dist_km=5.0):
        """Calculates and returns a list of nearby investments from the global index."""
        if not coords or coords[0] is None or coords[0] == 0:
            return []
            
        lat1, lon1 = coords
        all_invs = inv_index.get_index(self.data_dir)
        
        nearby = []
        # Rough bounding box check (5km is approx 0.05 lat, 0.08 lon at 52N)
        for other in all_invs:
            if other.get("usi_inv_id") == inv_id:
                continue
            
            other_coords = other.get("coords")
            if not other_coords or other_coords[0] is None or other_coords[0] == 0:
                continue
            
            lat2, lon2 = other_coords
            if abs(lat2 - lat1) > 0.06 or abs(lon2 - lon1) > 0.1:
                continue
                
            dist = _calculate_distance(lat1, lon1, lat2, lon2)
            if dist <= max_dist_km:
                nearby.append({
                    "usi_inv_id": other.get("usi_inv_id"),
                    "distance": round(dist, 2),
                    "name": other.get("name"),
                    "developer": other.get("developer"),
                    "slug": other.get("slug")
                })
        
        nearby.sort(key=lambda x: x["distance"])
        return nearby[:limit]
        
    def _prepare_batch_identifiers(self, portal, investments):
        """Prepares identifiers and metadata for a batch without registering skeletons yet."""
        from python_worker.url_parser import parse_url
        
        to_process = []
        targets = []

        for item in investments:
            fields = IDENTIFIER_PRIORITIES.get(portal, ["url", "id"])
            ident = next((item.get(f) for f in fields if item.get(f)), None)
            url = item.get("url")
            
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
                    if portal in PORTAL_VENDOR_ID_KEYS:
                        initial_pm[portal] = PORTAL_VENDOR_ID_KEYS[portal](vendor_id)

                    self.dm.create_developer_file({
                        "developer_slug": dev_slug,
                        "name": dev_name or f"Deweloper {portal.upper()} {vendor_id}",
                        "portal_mapping": initial_pm
                    })
                    logger.info(f"Pre-created developer profile {dev_slug} for '{dev_name}' to bypass API resolution errors.")

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
        targets, to_process = self._prepare_batch_identifiers(portal, investments)
        if not targets:
            return False

        # USUNIĘTO: Nadpisywanie konfiguracji i tworzenie nowego Fetchera na jedno żądanie!
        # Teraz bezpiecznie używamy centralnego self.fetcher oraz globalnego scraper_api
        from usi_scrapers import api as scraper_api

        batch_results = scraper_api.process_batch(
            self.lib_config, self.fetcher, portal, targets, on_progress=on_progress_callback
        )
        success_count = 0
        raw_prefix = portal

        for info, data in zip(to_process, batch_results):
            try:
                dev_slug, inv_slug, vendor_id, item_id = self._merge_batch_info(info, data)
                if not dev_slug or not inv_slug:
                    logger.warning(f"Missing slugs for {info['ident']} - skipping.")
                    continue

                inv_dir = self.data_dir / dev_slug / inv_slug
                if not list(inv_dir.glob(f"raw_{raw_prefix}_*.json")):
                    if data and isinstance(data, dict) and "error" not in data:
                        scraper_api.save_raw(self.lib_config, data, raw_prefix, portal_id=item_id)
                        if "image_urls" in data and self.tech_manager:
                            target_image_dir = self.tech_manager.get_image_path(portal, item_id)
                            if target_image_dir:
                                target_image_dir.mkdir(parents=True, exist_ok=True)
                                self.tech_manager.sync_images(data["image_urls"], target_image_dir)
                    else:
                        logger.warning(f"Batch download failed for {inv_slug} - skipping registration.")
                        continue

                res = self.register_investment(
                    portal=info["portal"],
                    developer_name=info["dev_name"] or dev_slug.replace("-", " ").title(),
                    name=info["name"] or (data.get("title") if isinstance(data, dict) else None),
                    item_id=item_id,
                    url=info["url"],
                    allow_existing=True,
                    vendor_id=vendor_id,
                    force_dev_slug=dev_slug
                )
                
                if res:
                    self.update_investment(res["system_id"], use_local_raw=True, skip_images=True, skip_index=True)
                    success_count += 1
            except Exception as e:
                logger.error(f"Error finalizing batch item {info.get('ident')}: {e}")

        return success_count > 0

    def _merge_batch_info(self, info, data):
        dev_slug = info.get("dev_slug")
        inv_slug = info.get("inv_slug")
        vendor_id = info.get("vendor_id")
        item_id = info.get("item_id")
        if data and isinstance(data, dict):
            dev_slug = data.get("developer_slug") or dev_slug
            inv_slug = data.get("investment_slug") or inv_slug
            item_id = data.get("id") or item_id
            vendor_id = data.get("vendor_id") or data.get("agency_id") or vendor_id
        return dev_slug, inv_slug, vendor_id, item_id

