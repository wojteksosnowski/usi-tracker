import json
import logging
import re
from datetime import datetime
from pathlib import Path

# External libraries (ensuring config is imported first to patch sys.path)
from python_worker.config import (
    get_shared_config, get_shared_fetcher, get_shared_tech_manager,
    USI_DATA_DIR, PUBLIC_USI_DIR, get_shared_scraper_gateway
)

from slugify import slugify

from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log
from python_worker.developer_manager import DeveloperManager
from python_worker.investment_repository import InvestmentRepository
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.developer_resolver import DeveloperResolver
from python_worker.services.image_sync import ImageSyncService
from python_worker.services.amenity_scorer import compute_amenity_score, suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images
from python_worker.api.utils import _calculate_distance
from python_worker.url_parser import parse_url
import python_worker.investment_index as inv_index
from typing import Optional, Any

logger = logging.getLogger(__name__)

def safe_round(value: Any, digits: int = 2) -> Optional[float]:
    """
    Bezpieczna funkcja zaokrąglająca. 
    Zapobiega awarii typu: type NoneType doesn't define __round__ method.
    """
    if value is None:
        return None
    try:
        return round(float(value), digits)
    except (ValueError, TypeError):
        return None

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
    def __init__(self, identity_resolver, data_dir: Path, public_usi_dir: Path, developer_manager=None, investment_repo=None, scraper_gateway=None):
        self.repo = investment_repo or InvestmentRepository(identity_resolver, data_dir)
        self.identity = identity_resolver
        self.data_dir = data_dir
        self.public_usi_dir = public_usi_dir
        self.dm = developer_manager or DeveloperManager(self.data_dir)
        
        # Przypisanie dedykowanej bramy zamiast luźnych obiektów config/fetcher
        self.gateway = scraper_gateway or get_shared_scraper_gateway()
        self._tech_manager = get_shared_tech_manager()
        self._image_sync = None
            
        self.resolver = InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)
        self.developer_resolver = DeveloperResolver(self.dm, self.identity)

    @property
    def tech_manager(self):
        return self._tech_manager

    @tech_manager.setter
    def tech_manager(self, value):
        self._tech_manager = value

    @property
    def image_sync(self):
        if self._image_sync is None:
            self._image_sync = ImageSyncService(self.tech_manager, self.public_usi_dir)
        return self._image_sync

    def _check_investment_exists(self, portal, item_id):
        if not item_id:
            return False
        full_portal = PORTAL_FULL_DOMAINS.get(portal)
        if not full_portal:
            return False
        # Czyste, zhermetyzowane wywołanie bramy:
        return self.gateway.has_local_raw(full_portal, str(item_id))

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
            inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=skeleton["usi_inv_id"])
        except Exception as _ie:
            logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")

        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        self.dm.invalidate_identifiers_cache()
        return dev_slug, inv_slug, skeleton["usi_inv_id"]

    def download_raw_json(self, portal: str, identifier: str, system_id: str):
        try:
            return self.gateway.download_raw(portal, identifier)
        except Exception as e:
            logger.error(f"Download raw failed for {portal}/{identifier}: {e}")
            return False


    def _fetch_and_transform_portal_data(self, system_id, portal, portal_name, raw_prefix, sources, use_local_raw):
        """Fetches raw portal data (local or remote) and transforms it."""
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            return None, None, f"{portal_name} (No resources)"

        inv_dir = resources["base_dir"]
        m = resources["metadata"]
        dev_slug = m.get("developer_slug") or "unknown"
        inv_slug = m.get("investment_slug") or inv_dir.name

        # 1. Sprawdź dostępność ID lub URL
        fields = IDENTIFIER_PRIORITIES.get(portal, ["url", "id"])
        identifier = next((sources[portal].get(f) for f in fields if sources[portal].get(f)), None)
        
        if not identifier:
            return None, None, None

        # 2. Wybierz odpowiednią metodę API przez bramę
        try:
            full_portal = PORTAL_FULL_DOMAINS.get(portal, portal)
            if use_local_raw:
                 raw_data = self.gateway.load_raw(full_portal, str(identifier))
                 if not raw_data: return None, None, None
            else:
                if str(identifier).startswith("http"):
                    res = self.gateway.ingest_investment_by_url(portal, identifier)
                else:
                    res = self.gateway.refresh_investment_by_id(portal, identifier)
                
                if res and "error" not in res:
                    raw_data = res
                else:
                    error_msg = res.get("error", "Unknown error")
                    return None, None, f"{portal_name} ({error_msg})"
                    
            unified_data = AdapterFactory.get_adapter(raw_prefix).transform(raw_data, inv_slug, dev_slug)
            return unified_data, portal_name, None
        except Exception as e:
            logger.error(f"Sync error: {e}")
            return None, None, f"{portal_name} ({str(e)})"

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
            p_id_root = usi_data.get("portal_id")
            if p_root and p_id_root:
                sources[p_root] = {"id": str(p_id_root)}

            # Jeśli nadal puste, parsujemy nazwę istniejącego pliku kotwicy: usi_{portal}_{id}.json
            if not sources and actual_file and actual_file.exists():
                parts = actual_file.stem.split("_")  # usi_{portal}_{id}
                if len(parts) >= 3 and parts[0] == "usi":
                    sources[parts[1]] = {"id": parts[2]}

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

        # --- BEZWZGLĘDNE LOGOWANIE TELEMETRII I BEZPIECZNIK ---
        total_elements = len(all_invs)
        logger.info(
            f"[CRITICAL_TRACE] Starting nearby calculations for ID: {inv_id}. "
            f"Total index entries to scan: {total_elements}"
        )

        iteration_counter = 0
        MAX_ALLOWED_ITERATIONS = 100_000  # Granica bezpieczeństwa
        # -------------------------------------------------------

        for other in all_invs:
            iteration_counter += 1

            # Logowanie kontrolne co 1000 iteracji z natychmiastowym flush
            if iteration_counter % 1000 == 0:
                logger.info(
                    f"[CRITICAL_TRACE] Nearby loop active. "
                    f"Iteration: {iteration_counter}/{total_elements} for inv_id: {inv_id}"
                )

            if iteration_counter > MAX_ALLOWED_ITERATIONS:
                logger.critical(
                    f"[LOOP_DETECTED] HARD BREAKER TRIGGERED in _calculate_nearby_investments "
                    f"for inv_id: {inv_id}! Aborting after {iteration_counter} iterations."
                )
                break

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
                    "distance": safe_round(dist, 2),
                    "name": other.get("name"),
                    "developer": other.get("developer"),
                    "slug": other.get("slug")
                })

        logger.info(
            f"[CRITICAL_TRACE] Finished nearby calculations for ID: {inv_id}. "
            f"Processed {iteration_counter}/{total_elements} entries. Found: {len(nearby)} nearby."
        )
        nearby.sort(key=lambda x: x["distance"])
        return nearby[:limit]
        
    def _prepare_batch_identifiers(self, portal, investments):
        """Prepares identifiers and metadata for a batch without registering skeletons yet."""
        
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

                targets.append(str(ident))
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

        # Wywołanie przez bramę (ukrywa lib_config i fetcher)
        batch_results = self.gateway.process_batch(portal, targets, on_progress=on_progress_callback)
        success_count = 0

        # --- TELEMETRIA PACZKI ---
        total_batch_items = len(to_process)
        logger.info(
            f"[CRITICAL_TRACE] Entering batch finalization loop. "
            f"Processing {total_batch_items} items for portal: {portal!r}."
        )
        current_item_index = 0
        # -------------------------

        for info, data in zip(to_process, batch_results):
            current_item_index += 1
            logger.info(
                f"[CRITICAL_TRACE] Batch item progress: {current_item_index}/{total_batch_items} "
                f"-> identifier: {info.get('ident')!r}"
            )

            try:
                if not data or "error" in data:
                    logger.warning(
                        f"Batch item failed: {info.get('ident')} "
                        f"- {data.get('error') if data else 'No data'}"
                    )
                    continue

                dev_slug, inv_slug, vendor_id, item_id = self._merge_batch_info(info, data)
                if not dev_slug or not inv_slug:
                    logger.warning(f"Missing slugs for {info['ident']} - skipping registration.")
                    continue

                # Registration: library already saved raw files and images if successful
                res = self.register_investment(
                    portal=info["portal"],
                    developer_name=info["dev_name"] or dev_slug.replace("-", " ").title(),
                    name=info["name"] or data.get("name"),
                    item_id=item_id,
                    url=info["url"],
                    allow_existing=True,
                    vendor_id=vendor_id,
                    force_dev_slug=dev_slug
                )

                if res:
                    # register_investment returns (dev_slug, inv_slug, usi_inv_id)
                    _, _, usi_inv_id = res
                    self.update_investment(usi_inv_id, use_local_raw=True, skip_images=True, skip_index=True)
                    success_count += 1
            except Exception as e:
                logger.error(
                    f"[BATCH_ERROR] Error finalizing batch item {info.get('ident')}: {e}",
                    exc_info=True
                )

        logger.info(
            f"[CRITICAL_TRACE] Exited batch finalization loop. "
            f"Processed {current_item_index}/{total_batch_items} items. "
            f"Successfully finalized: {success_count}."
        )
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

