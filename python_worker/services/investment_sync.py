import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict, List, Tuple

from slugify import slugify

from python_worker.config import (
    get_shared_config, get_shared_fetcher, get_shared_tech_manager,
    USI_DATA_DIR, PUBLIC_USI_DIR, get_shared_scraper_gateway
)
from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log
from python_worker.developer_manager import DeveloperManager
from python_worker.investment_repository import InvestmentRepository
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.developer_resolver import DeveloperResolver
from python_worker.services.image_sync import ImageSyncService
from python_worker.services.amenity_scorer import compute_amenity_score, suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images
from python_worker.url_parser import parse_url
import python_worker.investment_index as inv_index
from usi_scrapers.mapping import transform_to_unified  # Poprawka: przeniesione z wnętrza metody

logger = logging.getLogger(__name__)

PORTAL_NAMES: Dict[str, str] = {"rp": "RynekPierwotny", "oto": "Otodom", "to": "TabelaOfert"}
IDENTIFIER_PRIORITIES: Dict[str, List[str]] = {
    "rp": ["url", "id"],
    "oto": ["url", "id"],
    "to": ["url", "id"]
}

class InvestmentSyncService:
    def __init__(
        self, 
        identity_resolver: InvestmentIdentityResolver, 
        data_dir: Path, 
        public_usi_dir: Path, 
        developer_manager: Optional[DeveloperManager] = None, 
        investment_repo: Optional[InvestmentRepository] = None, 
        scraper_gateway: Optional[Any] = None
    ) -> None:
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
    def image_sync(self) -> ImageSyncService:
        if self._image_sync is None:
            self._image_sync = ImageSyncService(self.gateway, self.public_usi_dir)
        return self._image_sync

    def _resolve_inv_dir(self, portal: str, item_id: str, dev_slug: str, inv_slug: str) -> Path:
        """Resolves investment directory prioritizing library tech_manager."""
        inv_dir = None
        if self.tech_manager and portal and item_id:
            resolved = self.tech_manager.get_investment_path(portal, str(item_id))
            if resolved: 
                inv_dir = Path(resolved)
            
        if not inv_dir:
            inv_dir = self.data_dir / dev_slug / (inv_slug or str(item_id) or "unknown")
            
        return inv_dir

    def register_investment(
        self,
        portal: str,
        developer_name: str,
        name: str,
        item_id: Optional[str] = None,
        url: Optional[str] = None,
        allow_existing: bool = False,
        vendor_id: Optional[str] = None,
        force_dev_slug: Optional[str] = None,
        force_inv_slug: Optional[str] = None,
        skip_disk: bool = False,
        skip_index: bool = False
    ) -> Tuple[str, str, str, Dict, Optional[Path]]:
        """
        Registers a new investment skeleton.
        ID-ONLY: Priority for portal ID resolution.
        """
        # 1. BEZWZGLĘDNY RYGOR: usi-tracker nie tworzy folderów, jeśli usi-scrapers już to zrobiło
        inv_dir = None
        if self.tech_manager and portal and item_id:
            resolved = self.tech_manager.get_investment_path(portal, str(item_id))
            if resolved:
                inv_dir = Path(resolved)

        if not inv_dir and url:
            # POBIERAMY RAW, ŻEBY UZYSKAĆ SLUG Z MAPPING.PY ZAMIAST ZGADYWAĆ
            logger.info(f"Brak inv_dir, wymuszam pobranie z scrapera, aby uzyskać dokładny slug z mapping.py: {url}")
            try:
                raw_data = self.gateway.ingest_investment_by_url(portal, url)
                if raw_data and "error" not in raw_data:
                    # Po pobraniu, tech_manager będzie już znał ścieżkę
                    resolved = self.tech_manager.get_investment_path(portal, str(item_id))
                    if resolved:
                        inv_dir = Path(resolved)
                        force_dev_slug = raw_data.get("developer_slug") or force_dev_slug
                        force_inv_slug = raw_data.get("investment_slug") or force_inv_slug
            except Exception as e:
                logger.error(f"Nie udało się wymusić pobrania: {e}")

        if inv_dir:
            # SLUG POBIERAMY Z API SCAPERS, A NIE Z NAZWY FOLDERU (ROBUSTNOŚĆ NA ZMIANY ŚCIEŻEK)
            dev_slug = force_dev_slug or inv_dir.parent.name
            inv_slug = force_inv_slug or inv_dir.name
            
            # Spróbujmy wyciągnąć usi_dev_id z istniejącego indeksu
            dev_record = self.dm.find_developer_by_id(portal, str(vendor_id)) if vendor_id else None
            usi_dev_id = dev_record.get("usi_dev_id") if dev_record else None
        else:
            raise ValueError(f"USI-Tracker odmawia utworzenia folderu na ślepo bez uprzedniego zatwierdzenia przez bibliotekę usi-scrapers (brak pliku raw).")

        # 3. Check for existing investment
        existing_file = self._find_existing_anchor(inv_dir, portal, item_id)
        if existing_file:
            if not allow_existing:
                raise ValueError(f"Investment already exists: {dev_slug}/{inv_slug}")
            try:
                data = json.loads(existing_file.read_text(encoding="utf-8"))
                return dev_slug, inv_slug, data.get("usi_inv_id"), data, existing_file
            except json.JSONDecodeError as jde:
                logger.error(f"Zniszczony plik anchor JSON: {existing_file}. Błąd: {jde}")

        # 4. Create skeleton
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

        if vendor_id and item_id:
            mapping = self.gateway.generate_portal_mapping(portal, vendor_id)
            skeleton["sources"][portal].update(mapping)

        target_file = None
        if not skip_disk:
            target_file = self.repo.create_investment_skeleton(
                skeleton["usi_inv_id"], 
                portal, 
                str(item_id) if item_id else None, 
                skeleton
            )
            
            if not skip_index:
                self._update_indices_after_registration(skeleton["usi_inv_id"], inv_slug, dev_slug)

            log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
            
        return dev_slug, inv_slug, skeleton["usi_inv_id"], skeleton, target_file

    def _find_existing_anchor(self, inv_dir: Path, portal: Optional[str], item_id: Optional[str]) -> Optional[Path]:
        """Helper to find existing usi_*.json file strictly by ID match."""
        if not inv_dir or not inv_dir.exists():
            return None
        
        # Priority 1: Match filename exact ID
        if portal and item_id:
            target = inv_dir / f"usi_{portal}_{item_id}.json"
            if target.exists():
                return target
            
        # Priority 2: Read candidates and check if sources contain the exact portal and ID
        if portal and item_id:
            for f in inv_dir.glob("usi_*.json"):
                if "usi_dev_" in f.name:
                    continue
                try:
                    import json
                    data = json.loads(f.read_text(encoding="utf-8"))
                    sources = data.get("sources", {})
                    if portal in sources and str(sources[portal].get("id")) == str(item_id):
                        return f
                except Exception:
                    pass
                    
        return None

    def _update_indices_after_registration(self, system_id: str, inv_slug: str, dev_slug: str) -> None:
        """Helper to trigger index updates."""
        try:
            inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=system_id)
        except Exception as ie:
            # Zmieniono z debug na warning - niespójność indeksu to sytuacja awaryjna
            logger.warning(f"Krytyczny błąd aktualizacji indeksu dla {inv_slug}: {ie}")
        
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

        metadata = resources["metadata"]
        identifier = self._resolve_portal_identifier(sources[portal], portal)
        if not identifier:
            return None, None, None

        try:
            if use_local_raw:
                 raw_data = self.gateway.load_raw(portal, str(identifier))
            else:
                method = self.gateway.ingest_investment_by_url if str(identifier).startswith("http") else self.gateway.refresh_investment_by_id
                res = method(portal, identifier)
                raw_data = res if (res and "error" not in res) else None
                if not raw_data:
                    return None, None, f"{portal_name} ({res.get('error', 'Unknown error') if res else 'Empty response'})"
                    
            if not raw_data:
                return None, None, None

            unified_data = AdapterFactory.get_adapter(raw_prefix).transform(
                raw_data, 
                metadata.get("investment_slug"), 
                metadata.get("developer_slug")
            )
            return unified_data, portal_name, None
        except Exception as e:
            logger.error(f"Sync error for {portal}/{identifier}: {e}")
            return None, None, f"{portal_name} ({str(e)})"

    def update_investment(
        self,
        system_id: str,
        use_local_raw: bool = False,
        skip_images: bool = False,
        skip_index: bool = False,
        skip_log: bool = False,
        initial_data: Optional[Dict] = None,
        fast_mode: bool = False,
        cached_index: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
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
            resources = self._resolve_resources_manually(system_id, initial_data)

        if not resources:
            logger.warning(f"Investment resources not found skipping ID: {system_id}")
            return False
            
        inv_dir = resources["base_dir"]
        actual_file = resources["files"].get("anchor")
        metadata = resources["metadata"]
        dev_slug = metadata.get("developer_slug") or "unknown"
        inv_slug = metadata.get("investment_slug") or inv_dir.name
        
        # 1. Load current state
        usi_data = initial_data if (initial_data and isinstance(initial_data, dict)) else {}
        if not usi_data and actual_file and actual_file.exists():
            try:
                usi_data = json.loads(actual_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Error reading existing file {actual_file}: {e}")

        sources = usi_data.get("sources", {})
        if not sources and metadata.get("portal") and metadata.get("portal_id"):
            sources[metadata["portal"]] = {"id": str(metadata["portal_id"])}

        # 2. Fetch and Transform
        unified_data_map = {}
        fetched_sources, failed_sources = [], []

        for p_key in ["rp", "oto", "to"]:
            if p_key not in sources:
                continue

            unified, p_name, error = self._fetch_and_transform_portal_data(
                system_id, p_key, PORTAL_NAMES.get(p_key, p_key), p_key, sources, use_local_raw, resources
            )
            
            if unified:
                unified_data_map[p_key] = unified
                fetched_sources.append(p_name)
            elif error:
                failed_sources.append(error)

        if not unified_data_map:
            if failed_sources:
                logger.error(f"Fetch failed for {system_id}: {'; '.join(failed_sources)}")
            return False

        # 3. Semantic layer: Ratings and Merging
        ratings = self._load_best_ratings(inv_dir, inv_slug)
        event = f"Sync: {', '.join(fetched_sources)}" if fetched_sources else "Manual Update"
        
        new_unified = Merger.merge(
            unified_data_map.get("rp"), 
            unified_data_map.get("oto"), 
            unified_data_map.get("to"), 
            ratings, 
            existing_data=usi_data, 
            event=event
        )

        # 4. Technical layer: Images
        if not skip_images:
            all_urls = new_unified.get("image_urls", [])
            self.image_sync.sync_investment_images(system_id, new_unified, all_urls, skip_images, usi_data, resources)

        # 5. Enrich & Finalize
        self.developer_resolver.backfill_developer_mapping(system_id, new_unified)
        self._enrich_with_derived_data(new_unified, inv_dir, resources, usi_data, fast_mode, cached_index)

        # 6. Persistence
        if "usi_inv_id" not in new_unified or not new_unified["usi_inv_id"]:
            new_unified["usi_inv_id"] = system_id
        self.repo.save_investment_json(system_id, new_unified, anchor_path=actual_file)
        
        if not skip_index:
            self._update_indices_after_registration(system_id, inv_slug, dev_slug)

        if not skip_log:
            summary = f"Updated: {', '.join(fetched_sources)}"
            if failed_sources:
                summary += f". Failed: {', '.join(failed_sources)}"
            log_to_processing_log(dev_slug, inv_slug, summary)
            
        return True

    def _resolve_resources_manually(self, system_id: str, initial_data: Dict) -> Dict:
        """Helper to create resource map for new investments not yet in index."""
        p_key = list(initial_data["sources"].keys())[0]
        p_id = initial_data["sources"][p_key].get("id")
        
        inv_dir = self._resolve_inv_dir(p_key, p_id, initial_data.get("developer_slug"), initial_data.get("investment_slug"))
        images_dir = self.tech_manager.get_image_path(p_key, str(p_id)) if self.tech_manager and p_id else None
        
        return {
            "id": system_id,
            "base_dir": inv_dir,
            "files": {
                "anchor": inv_dir / f"usi_{system_id}.json"
            },
            "images_dir": images_dir,
            "metadata": {
                "portal": p_key,
                "portal_id": p_id,
                "developer_slug": inv_dir.parent.name,
                "investment_slug": inv_dir.name
            }
        }

    def _load_best_ratings(self, inv_dir: Path, inv_slug: str) -> Dict:
        """Finds the most recent ratings file."""
        candidates = []
        for p in ("rp", "oto", "to"):
            candidates.extend(sorted(inv_dir.glob(f"meta_{p}_*.json"), reverse=True))
        candidates.append(inv_dir / "meta_ratings.json")
        candidates.append(inv_dir / f"meta_{inv_slug}_ratings.json")
        for path in candidates:
            if path.exists():
                try:
                    return json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.error(f"Error reading ratings file {path}: {e}")
        return {}

    def _enrich_with_derived_data(self, data: Dict, inv_dir: Path, resources: Dict, old_data: Dict, fast_mode: bool, cached_index: Optional[List[Dict[str, Any]]] = None):
        """Computes scores, resolves photos, and calculates nearby investments."""
        # Amenities
        am_data = data.get("amenities", {})
        score_data = compute_amenity_score(am_data.get("labels", []), am_data.get("raw_codes", []))
        data["amenities_score"] = score_data["score"]
        data["amenities_matched"] = score_data["matched"]
        data["suggested_udogodnienia"] = suggest_udogodnienia(score_data["score"])
        
        # Photos
        data["photos"] = resolve_images(data, inv_dir, self.public_usi_dir, resources, fast_index=fast_mode)
        data["images_count"] = len(data["photos"])

        # Nearby (expensive)
        if fast_mode:
            data["nearby_investments"] = old_data.get("nearby_investments", [])
        else:
            old_coords = old_data.get("location", {}).get("coords")
            new_coords = data.get("location", {}).get("coords")
            if not old_data.get("nearby_investments") or old_coords != new_coords:
                data["nearby_investments"] = inv_index.get_nearby_investments(data.get("usi_inv_id"), new_coords, cached_index=cached_index)
            else:
                data["nearby_investments"] = old_data.get("nearby_investments", [])

        # Deletion list
        deletion_file = inv_dir / "deletion_list.json"
        data["photos_to_delete"] = 0
        if deletion_file.exists():
            try:
                deletion_list = json.loads(deletion_file.read_text(encoding="utf-8"))
                data["photos_to_delete"] = len(deletion_list.get("paths", []))
            except Exception:
                pass
        
    def _prepare_batch_identifiers(self, portal, investments):
        """Prepares identifiers and metadata for a batch without registering skeletons yet."""
        to_process, targets = [], []

        for item in investments:
            ident = self._resolve_portal_identifier(item, portal)
            if not ident:
                continue

            url = item.get("url")
            inv_slug = item.get("investment_slug") or item.get("inv_slug") or item.get("slug")
            if not inv_slug and url:
                inv_slug = parse_url(url).get("investment_slug")
            
            # Vendor ID extraction logic
            vendor_id = item.get("vendor_id") or item.get("agency_id") or item.get("developer_id")
            if not vendor_id and portal in ("otodom", "oto"):
                 vendor_id = self.gateway.resolve_path(item, "vendor.id|ad.agency.id|agency_id|developer_id")
            
            if not vendor_id and portal == "rp" and isinstance(item.get("vendor"), dict):
                vendor_id = item["vendor"].get("id")

            # MANDAT ROBUSTNOŚCI: Preferujemy URL jako identyfikator dla procesu batch.
            # Dzięki temu gateway użyje process_batch_ingest, który radzi sobie z nowymi ofertami
            # (refresh_by_id w bibliotece wywala błąd, jeśli plik nie istnieje lokalnie).
            batch_target = url if url else str(ident)
            targets.append(batch_target)
            
            to_process.append({
                "ident": ident, "inv_slug": inv_slug, "url": url, "portal": portal,
                "name": item.get("name"), "item_id": item.get("id"),
                "dev_name": item.get("developer_name") or item.get("developer"),
                "vendor_id": vendor_id
            })
        
        return targets, to_process

    def process_batch(self, portal: str, investments: List[Dict], on_progress_callback: Optional[Any] = None) -> int:
        """
        Processes a batch of investments with performance optimizations:
        - Bulk downloading via gateway
        - Local transformation
        - Rebuilding index once at the end
        """
        targets, to_process = self._prepare_batch_identifiers(portal, investments)
        if not targets:
            return 0

        # 1. Bulk download
        batch_results = self.gateway.process_batch(portal, targets, on_progress=on_progress_callback)
        logger.info(f"[BATCH] Gateway returned {len(batch_results)} results for {portal}")
        saved_count = 0
        cached_index = inv_index.get_index(self.data_dir)

        # 2. Consumption and processing
        for i, (item_info, data) in enumerate(zip(to_process, batch_results)):
            if not data or (isinstance(data, dict) and "error" in data):
                logger.warning(f"[BATCH] Skipping item {i} due to empty data or error: {data}")
                continue

            try:
                # 3. Preparation
                raw_payload = data.get("raw_details", data) if isinstance(data, dict) else data
                
                meta = transform_to_unified(portal, raw_payload, entity_type="investment") or {}
                dev_meta = self.gateway.extract_developer_meta(raw_payload, portal)

                # 4. ID Resolution (Sacred IDs)
                item_id = self._resolve_item_id_for_batch(portal, meta, item_info, data)
                if not item_id:
                    continue

                # 4.5. Vendor ID extraction
                vendor_id = dev_meta.get("id") or meta.get("vendor_id") or item_info.get("vendor_id")

                # 5. Registration and Update (fast_mode enabled)
                logger.info(f"[BATCH] Registering {portal}/{item_id}...")
                _, _, usi_inv_id, skeleton, inv_path = self.register_investment(
                    portal=portal,
                    developer_name=dev_meta.get("name") or meta.get("developer_name") or item_info.get("dev_name"),
                    name=meta.get("name") or item_info.get("name") or f"Inwestycja {portal.upper()} {item_id}",
                    item_id=item_id,
                    url=item_info.get("url") or data.get("url") or data.get("to_url"),
                    allow_existing=True,
                    vendor_id=vendor_id,
                    skip_index=True,
                    force_dev_slug=data.get("developer_slug") or dev_meta.get("slug"),
                    force_inv_slug=data.get("investment_slug")
                )
                
                logger.info(f"[BATCH] Registered as {usi_inv_id}. Proceeding to update...")

                if usi_inv_id:
                    # MANDAT ID-ONLY: Zapisujemy surowe dane na dysk przed wywołaniem update_investment(use_local_raw=True)
                    self.repo.save_raw_json(usi_inv_id, portal, item_id, raw_payload, target_dir=inv_path.parent if inv_path else None)
                    
                    ok = self.update_investment(
                        usi_inv_id, 
                        use_local_raw=True, 
                        fast_mode=True, 
                        skip_index=True, 
                        initial_data=skeleton,
                        cached_index=cached_index
                    )
                    logger.info(f"[BATCH] Update result for {usi_inv_id}: {ok}")
                    if ok:
                        saved_count += 1
                    else:
                        logger.warning(f"[BATCH] Update failed for {usi_inv_id}")
                else:
                    logger.warning(f"[BATCH] No usi_inv_id returned for {item_id}")

            except Exception as e:
                logger.error(f"[BATCH_ERROR] Błąd finalizacji dla {item_info.get('ident')}: {e}", exc_info=True)

        # 6. Global optimization: Single index rebuild
        if saved_count > 0:
            logger.info(f"[BATCH] Finished. Saving {saved_count} items and rebuilding index.")
            inv_index.rebuild(self.data_dir, self.public_usi_dir)
            self.dm.invalidate_identifiers_cache()

        return saved_count

    def _resolve_item_id_for_batch(self, portal: str, meta: Dict, info: Dict, data: Any) -> Optional[str]:
        """Strict ID resolution for batch processing."""
        
        # Priority 1: Meta from transformation
        item_id = meta.get("id") or info.get("item_id")

        # Priority 2: Direct from data dictionary
        if not item_id and isinstance(data, dict):
            item_id = data.get("id") or data.get("portal_id")

        # Priority 3: Parsing from URL
        if not item_id and info.get("url"):
            item_id = parse_url(info["url"]).get("item_id")

        # Priority 4: Identifier itself if not a URL
        if not item_id and info.get("ident") and not str(info["ident"]).startswith("http"):
            item_id = str(info["ident"])

        return str(item_id) if item_id else None


