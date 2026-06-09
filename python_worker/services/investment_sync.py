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

PORTAL_NAMES = {"rp": "RynekPierwotny", "oto": "Otodom", "to": "TabelaOfert"}
IDENTIFIER_PRIORITIES = {
    "rp": ["id", "url"],
    "oto": ["id", "url"],
    "to": ["id", "url"]
}
PORTAL_VENDOR_ID_KEYS = {
    "rp": lambda vid: {"id": str(vid)},
    "to": lambda vid: {"agency_id": str(vid)},
    "oto": lambda vid: {"agency_id": str(vid), "agency_ids": [str(vid)]}
}

class InvestmentSyncService:
    def __init__(self, identity_resolver, data_dir: Path, public_usi_dir: Path, developer_manager=None, investment_repo=None, scraper_gateway=None):
        self.data_dir = data_dir
        self.public_usi_dir = public_usi_dir
        self.identity = identity_resolver
        self.repo = investment_repo or InvestmentRepository(identity_resolver, data_dir)
        self.dm = developer_manager or DeveloperManager(self.data_dir)
        
        self.gateway = scraper_gateway or get_shared_scraper_gateway()
        self.developer_resolver = DeveloperResolver(self.dm, self.identity)
        self._tech_manager = get_shared_tech_manager()
        self._image_sync = None

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

    def _resolve_inv_dir(self, portal: str, item_id: str, dev_slug: str, inv_slug: str) -> Path:
        """Resolves investment directory prioritizing library tech_manager."""
        inv_dir = None
        if self.tech_manager and portal and item_id:
            resolved = self.tech_manager.get_investment_path(portal, str(item_id))
            if resolved: inv_dir = Path(resolved)
            
        if not inv_dir:
            inv_dir = self.data_dir / dev_slug / (inv_slug or str(item_id) or "unknown")
            
        return inv_dir

    def register_investment(self, portal, developer_name, name, item_id=None, url=None, allow_existing=False, vendor_id=None, force_dev_slug=None, skip_disk=False, skip_index=False):
        """
        Registers a new investment skeleton.
        ID-ONLY: Priority for portal ID resolution.
        """
        dev_slug, _, inv_slug_from_url, usi_dev_id = self.developer_resolver.resolve_developer_for_registration(
            portal, developer_name, url, vendor_id, force_dev_slug
        )
        
        inv_dir = self._resolve_inv_dir(portal, item_id, dev_slug, inv_slug_from_url or slugify(name))
        inv_slug = inv_dir.name

        # 2. Check for existing investment
        existing_file = self._find_existing_anchor(inv_dir, portal, item_id)
        if existing_file:
            if not allow_existing:
                raise ValueError(f"Investment already exists: {dev_slug}/{inv_slug}")
            try:
                data = json.loads(existing_file.read_text(encoding="utf-8"))
                return dev_slug, inv_slug, data.get("usi_inv_id"), data
            except Exception:
                pass

        # 3. Create skeleton
        inv_dir.mkdir(parents=True, exist_ok=True)
        system_id = f"{portal}_{item_id}" if item_id else inv_slug
        skeleton = {
            "usi_inv_id": system_id,
            "investment_slug": inv_slug,
            "developer_slug": dev_slug,
            "usi_dev_id": usi_dev_id,
            "name": name,
            "reviewed": False,
            "sources": {portal: {"id": str(item_id), "url": url}} if item_id else {},
            "specifications": {"segment": None},
            "status": "Brak",
            "audit": {"created_at": datetime.now().isoformat()}
        }

        if vendor_id and portal in PORTAL_VENDOR_ID_KEYS and item_id:
            skeleton["sources"][portal].update(PORTAL_VENDOR_ID_KEYS[portal](vendor_id))

        if skip_disk:
            return dev_slug, inv_slug, skeleton["usi_inv_id"], skeleton

        self.repo.create_investment_skeleton(skeleton["usi_inv_id"], portal, str(item_id) if item_id else None, skeleton)
        
        if not skip_index:
            self._update_indices_after_registration(skeleton["usi_inv_id"], inv_slug, dev_slug)

        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        return dev_slug, inv_slug, skeleton["usi_inv_id"], skeleton

    def _find_existing_anchor(self, inv_dir, portal, item_id):
        """Helper to find existing usi_*.json file in a directory."""
        if not inv_dir: return None
        
        if portal and item_id:
            target = inv_dir / f"usi_{portal}_{item_id}.json"
            if target.exists(): return target
            
        if inv_dir.exists():
            candidates = [f for f in inv_dir.glob("usi_*.json") if "usi_dev_" not in f.name]
            if candidates: return sorted(candidates)[0]
        return None

    def _update_indices_after_registration(self, system_id, inv_slug, dev_slug):
        """Helper to trigger index updates."""
        try:
            inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=system_id)
        except Exception as _ie:
            logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")
        
        self.dm.invalidate_identifiers_cache()

    def download_raw_json(self, portal: str, identifier: str, system_id: str):
        try:
            return self.gateway.download_raw(portal, identifier)
        except Exception as e:
            logger.error(f"Download raw failed for {portal}/{identifier}: {e}")
            return False


    def _resolve_portal_identifier(self, portal_data: dict, portal_key: str) -> Optional[str]:
        """Resolves the best identifier (URL or ID) for a portal."""
        fields = IDENTIFIER_PRIORITIES.get(portal_key, ["url", "id"])
        return next((portal_data.get(f) for f in fields if portal_data.get(f)), None)

    def _fetch_and_transform_portal_data(self, system_id, portal, portal_name, raw_prefix, sources, use_local_raw, resources=None):
        """Fetches raw portal data (local or remote) and transforms it."""
        if not resources:
            resources = self.identity.get_investment_resources(system_id)
            
        if not resources:
            return None, None, f"{portal_name} (No resources)"

        m = resources["metadata"]
        identifier = self._resolve_portal_identifier(sources[portal], portal)
        if not identifier: return None, None, None

        try:
            if use_local_raw:
                 raw_data = self.gateway.load_raw(portal, str(identifier))
            else:
                method = self.gateway.ingest_investment_by_url if str(identifier).startswith("http") else self.gateway.refresh_investment_by_id
                res = method(portal, identifier)
                raw_data = res if (res and "error" not in res) else None
                if not raw_data: return None, None, f"{portal_name} ({res.get('error', 'Unknown error') if res else 'Empty response'})"
                    
            if not raw_data: return None, None, None

            unified_data = AdapterFactory.get_adapter(raw_prefix).transform(raw_data, m.get("investment_slug"), m.get("developer_slug"))
            return unified_data, portal_name, None
        except Exception as e:
            logger.error(f"Sync error for {portal}/{identifier}: {e}")
            return None, None, f"{portal_name} ({str(e)})"

    def update_investment(self, system_id, use_local_raw=False, skip_images=False, skip_index=False, skip_log=False, initial_data=None, fast_mode=False):
        """
        Orchestrates the update of an investment:
        1. Scrapes raw data (or loads local)
        2. Transforms to unified USI schema
        3. Merges with existing data and ratings
        4. Synchronizes images
        """
        resources = self.identity.get_investment_resources(system_id)
        
        # MANDAT THIN-CLIENT: Jeśli brak w indeksie, wyznaczamy zasoby ręcznie (np. świeżo zarejestrowany batch)
        if not resources and initial_data and initial_data.get("sources"):
            p_key = list(initial_data["sources"].keys())[0]
            p_id = initial_data["sources"][p_key].get("id")
            
            inv_dir = self._resolve_inv_dir(p_key, p_id, initial_data.get("developer_slug"), initial_data.get("investment_slug"))
            images_dir = self.tech_manager.get_image_path(p_key, str(p_id)) if self.tech_manager and p_id else None
            
            resources = {
                "id": system_id,
                "base_dir": inv_dir,
                "files": {
                    "anchor": inv_dir / f"usi_{system_id}.json",
                    "raw": inv_dir / f"raw_{p_key}_{p_id}.json"
                },
                "images_dir": images_dir,
                "metadata": {
                    "portal": p_key,
                    "portal_id": p_id,
                    "developer_slug": inv_dir.parent.name,
                    "investment_slug": inv_dir.name
                }
            }

        if not resources:
            logger.warning(f"Investment resources not found skipping ID: {system_id}")
            return False
            
        inv_dir = resources["base_dir"]
        actual_file = resources["files"].get("anchor")
        m = resources["metadata"]
        dev_slug = m.get("developer_slug") or "unknown"
        inv_slug = m.get("investment_slug") or inv_dir.name
        
        usi_data = initial_data if (initial_data and isinstance(initial_data, dict)) else {}
        if not usi_data and actual_file and actual_file.exists():
            with open(actual_file, "r", encoding="utf-8") as f:
                usi_data = json.load(f)

        sources = usi_data.get("sources", {})
        if not sources and m.get("portal") and m.get("portal_id"):
            sources[m["portal"]] = {"id": str(m["portal_id"])}

        unified_data_map = {"rp": None, "oto": None, "to": None}
        fetched_sources, failed_sources = [], []

        for portal in ["rp", "oto", "to"]:
            if portal not in sources: continue

            unified_data, fetched_src, failed_src = self._fetch_and_transform_portal_data(
                system_id, portal, PORTAL_NAMES.get(portal, portal), portal, sources, use_local_raw, resources=resources
            )
            
            if unified_data: unified_data_map[portal] = unified_data
            if fetched_src: fetched_sources.append(fetched_src)
            if failed_src: failed_sources.append(failed_src)


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
            if not skip_images:
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
            
            # KLUCZOWA ZMIANA: Przekazujemy fast_mode, żeby resolve_images nie orało dysku przez glob()
            new_unified["photos"] = resolve_images(new_unified, inv_dir, self.public_usi_dir, resources, fast_index=fast_mode)
            new_unified["images_count"] = len(new_unified["photos"])

            # Kalkulacja sąsiedztwa (wyłączona w trybie masowym fast_mode)
            if fast_mode:
                new_unified["nearby_investments"] = usi_data.get("nearby_investments", [])
            else:
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
            self.repo.save_investment_json(system_id, new_unified, anchor_path=actual_file)
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
        """Calculates nearby investments using the global index with a bounding box optimization."""
        if not coords or not coords[0]: return []

        lat1, lon1 = coords
        all_invs = inv_index.get_index(self.data_dir)
        nearby = []

        for other in all_invs:
            if other.get("usi_inv_id") == inv_id: continue
            
            other_coords = other.get("coords")
            if not other_coords or not other_coords[0]: continue

            lat2, lon2 = other_coords
            # Fast bounding box check (~5-7km)
            if abs(lat2 - lat1) > 0.06 or abs(lon2 - lon1) > 0.1: continue

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
        to_process, targets = [], []

        for item in investments:
            ident = self._resolve_portal_identifier(item, portal)
            if not ident: continue

            url = item.get("url")
            inv_slug = item.get("investment_slug") or item.get("inv_slug") or item.get("slug")
            if not inv_slug and url: inv_slug = parse_url(url).get("investment_slug")
            
            # Vendor ID extraction logic
            vendor_id = item.get("vendor_id") or item.get("agency_id") or item.get("developer_id")
            if not vendor_id and portal == "rp" and isinstance(item.get("vendor"), dict):
                vendor_id = item["vendor"].get("id")

            targets.append(str(ident))
            to_process.append({
                "ident": ident, "inv_slug": inv_slug, "url": url, "portal": portal,
                "name": item.get("name"), "item_id": item.get("id"),
                "dev_name": item.get("developer_name") or item.get("developer"),
                "vendor_id": vendor_id
            })
        
        return targets, to_process

    def process_batch(self, portal, investments, on_progress_callback=None):
        targets, to_process = self._prepare_batch_identifiers(portal, investments)
        if not targets: return 0

        # KROK 1: Masowe pobranie danych
        batch_results = self.gateway.process_batch(portal, targets, on_progress=on_progress_callback)
        saved_count = 0
        
        from usi_scrapers.mapping import transform_to_unified
        
        # KROK 2: Konsumpcja wyników
        for info, data in zip(to_process, batch_results):
            if not data or (isinstance(data, dict) and "error" in data): continue
                
            try:
                raw_payload = data.get("raw_details", data) if isinstance(data, dict) else data
                meta = transform_to_unified(portal, raw_payload, entity_type="investment") or {}
                dev_meta = self.gateway.extract_developer_meta(raw_payload, portal)
                
                # Wyznaczenie ID z priorytetem dla danych ze scrapera
                item_id = meta.get("id") or info.get("item_id")
                if not item_id and isinstance(data, dict): item_id = data.get("id") or data.get("portal_id")
                
                # Fallback: Parsowanie z URL (MANDAT ROBUSTNOŚCI)
                if not item_id and info.get("url"):
                    item_id = parse_url(info["url"]).get("item_id")
                    
                if not item_id and info.get("ident") and not str(info["ident"]).startswith("http"):
                    item_id = str(info["ident"])

                if not item_id: continue

                # KROK 4: Rejestracja i Update w trybie fast_mode (skip_index=True)
                _, _, usi_inv_id, skeleton = self.register_investment(
                    portal=portal,
                    developer_name=dev_meta.get("name") or meta.get("developer_name") or info.get("dev_name"),
                    name=meta.get("name") or info.get("name") or f"Inwestycja {portal.upper()} {item_id}",
                    item_id=item_id,
                    url=info.get("url"),
                    allow_existing=True,
                    vendor_id=dev_meta.get("id") or meta.get("vendor_id") or info.get("vendor_id"),
                    skip_index=True
                )
                
                if usi_inv_id and self.update_investment(usi_inv_id, use_local_raw=True, fast_mode=True, skip_index=True, initial_data=skeleton):
                    saved_count += 1
                else:
                    logger.warning(f"[BATCH] Update failed for {usi_inv_id}")
            except Exception as e:
                logger.error(f"[BATCH_ERROR] Błąd finalizacji dla {info.get('ident')}: {e}", exc_info=True)
                
        # OPTYMALIZACJA: Przebudowa indeksu raz na końcu batcha
        logger.info(f"[BATCH] Finished. Saving {saved_count} items and rebuilding index.")
        inv_index.rebuild(self.data_dir, self.public_usi_dir)
        self.dm.invalidate_identifiers_cache()
        return saved_count

