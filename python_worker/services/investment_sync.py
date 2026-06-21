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
from python_worker.adapters.merger import Merger
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
    "rp": ["id", "url"],
    "oto": ["id", "url"],
    "to": ["id", "url"]
}


def _enrich_rp_unified(unified: dict) -> None:
    """Post-processing po transform_to_unified dla portalu RP.
    Konwertuje płaski klucz 'construction_date_upper' (YYYY-MM-DD) na
    specifications.delivery_date (YYYY-QN), delivery_quarter i delivery_year.
    Działa in-place.
    """
    upper = unified.get("construction_date_upper")
    if not upper:
        return

    specs = unified.setdefault("specifications", {})
    # Nie nadpisuj jeśli już wypełnione
    if specs.get("delivery_date") or specs.get("delivery_quarter"):
        return

    try:
        parts = upper.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 12
        quarter = (month - 1) // 3 + 1
        specs["delivery_date"] = f"{year}-Q{quarter}"
        specs["delivery_quarter"] = quarter
        specs["delivery_year"] = year
    except (ValueError, IndexError):
        logger.warning(f"Cannot parse construction_date_upper: {upper!r}")


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
        skip_index: bool = False,
        raw_data: Optional[Dict] = None
    ) -> Tuple[str, str, str, Dict, Optional[Path]]:
        """
        Registers a new investment by ingesting data from the portal and running the update pipeline.
        Tracker delegates all I/O and folder creation to usi-scrapers.
        """
        portal = self.gateway.normalize_portal_name(portal)
        
        # 1. Bezwzględny rygor: pobieramy pełne dane przez scraper API (chyba że podano raw_data)
        if raw_data:
            pass # Use provided data
        elif url:
            raw_data = self.gateway.ingest_investment_by_url(portal, url)
        elif item_id:
            raw_data = self.gateway.refresh_investment_by_id(portal, item_id)
        else:
            raise ValueError("Rejestracja wymaga podania URL, item_id lub raw_data")

        if not raw_data or "error" in raw_data:
            raise ValueError(f"Nie udało się pobrać danych z portalu {portal}: {raw_data.get('error') if raw_data else 'Brak danych'}")

        # 2. Wyciągnięcie kluczowych identyfikatorów
        item_id = str(raw_data.get("id") or item_id)
        dev_slug = force_dev_slug or raw_data.get("developer_slug")
        inv_slug = force_inv_slug or raw_data.get("investment_slug")
        
        if not dev_slug or not inv_slug:
            resolved = self.tech_manager.get_investment_path(portal, item_id)
            if resolved:
                p = Path(resolved)
                dev_slug = dev_slug or p.parent.name
                inv_slug = inv_slug or p.name
        
        if not dev_slug or not inv_slug:
            raise ValueError(f"Nie udało się wyznaczyć slugów dla {portal}/{item_id}")

        usi_inv_id = f"{portal}_{item_id}"
        
        # Sprawdzenie czy już istnieje
        if not allow_existing:
            resources = self.identity.get_investment_resources(usi_inv_id)
            if resources and resources["files"].get("anchor"):
                raise ValueError(f"Inwestycja {usi_inv_id} już istnieje w bazie.")

        # 3. Wywołanie standardowego potoku aktualizacji (transformacja + zapis + indeks)
        initial_data = {
            "usi_inv_id": usi_inv_id,
            "sources": {portal: {"id": item_id, "url": url}},
            "developer_slug": dev_slug,
            "investment_slug": inv_slug,
            "name": name or raw_data.get("name"),
            "usi_dev_id": (self.dm.find_developer_by_id(portal, str(vendor_id)) or {}).get("usi_dev_id") if vendor_id else None
        }
        
        success = self.update_investment(
            usi_inv_id, 
            use_local_raw=True, 
            skip_index=skip_index,
            initial_data=initial_data
        )
        
        if not success:
            raise ValueError(f"Błąd przetwarzania/transformacji inwestycji {usi_inv_id}")

        # 4. Załadowanie i zwrócenie finalnego rekordu
        resources = self.identity.get_investment_resources(usi_inv_id)
        if not resources:
            resources = self._resolve_resources_manually(usi_inv_id, initial_data)
            
        anchor_file = resources["files"]["anchor"]
        final_data = json.loads(anchor_file.read_text(encoding="utf-8"))
        
        return dev_slug, inv_slug, usi_inv_id, final_data, anchor_file

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


    def _resolve_portal_identifier(self, portal_data: dict, portal_key: str, system_id: str = "") -> Optional[str]:
        """Resolves the best identifier (ID over URL) for a portal adhering to ID-only rule."""
        if system_id and system_id.startswith(f"{portal_key}_"):
            parts = system_id.split("_", 1)
            if len(parts) == 2:
                return parts[1]
                
        # Primary: numeric ID (lub agency_id dla Otodom)
        portal_id = portal_data.get("id") or portal_data.get("agency_id")
        if portal_id:
            return str(portal_id)
            
        # Fallback: URL with explicit logging
        portal_url = portal_data.get("url")
        if portal_url:
            logger.warning(f"[{system_id}] Fallback to URL for {portal_key} - missing numeric ID")
            return str(portal_url)
            
        return None

    def _fetch_and_transform_portal_data(self, system_id, portal, portal_name, raw_prefix, sources, use_local_raw, resources=None):
        """Fetches raw portal data (local or remote) and transforms it."""
        if not resources:
            resources = self.identity.get_investment_resources(system_id)
            
        if not resources:
            return None, None, f"{portal_name} (No resources)"

        metadata = resources["metadata"]
        identifier = self._resolve_portal_identifier(sources[portal], portal, system_id)
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
                    err_msg = res.get('error', 'Unknown error') if res else 'Empty response'
                    logger.warning(f"Fetch failed for {portal}/{identifier} ({err_msg}). Falling back to local raw data.")
                    raw_data = self.gateway.load_raw(portal, str(identifier))
                    if not raw_data:
                        return None, None, f"{portal_name} ({err_msg} and NO local raw fallback)"
                        
            if not raw_data:
                return None, None, None

            from usi_scrapers.mapping import transform_to_unified
            
            # W scraperach (szczególnie RP i OTO) funkcja refresh zwraca obudowany słownik,
            # gdzie właściwe dane portalu siedzą pod kluczem 'raw_details'.
            # Ponieważ load_raw ładuje pliki z dysku, które już są 'raw_details', 
            # dla spójności musimy zawsze odpakować ten słownik, jeśli istnieje.
            actual_portal_data = raw_data.get("raw_details") if isinstance(raw_data.get("raw_details"), dict) else raw_data
            
            unified_data = transform_to_unified(portal, actual_portal_data, "investment")

            # RP-specific post-enrichment: construction_date_upper → specifications.delivery_*
            if portal == "rp":
                _enrich_rp_unified(unified_data)

            unified_data["investment_slug"] = metadata.get("investment_slug")
            unified_data["developer_slug"] = metadata.get("developer_slug")
            
            # Add sources block so Merger can pick it up
            if "sources" not in unified_data:
                unified_data["sources"] = {
                    portal: {
                        "id": str(identifier),
                        "url": raw_data.get("url") if isinstance(raw_data, dict) else None
                    }
                }
                
            # Copy image paths if provided by scraper in live fetch
            if isinstance(raw_data, dict) and "image_paths" in raw_data:
                unified_data["image_paths"] = raw_data["image_paths"]

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
            
        # Zawsze przebudowujemy cache resolvera przed odświeżaniem w trybie UI, bo mógł się zdezaktualizować
        self.tech_manager.resolver.force_rebuild()
            
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

        # --- NOWA LOGIKA: Agregacja źródeł z grupy Master ---
        master_id = usi_data.get("master_id")
        if master_id:
            master_file = inv_dir / f"master_{master_id}.json"
            if master_file.exists():
                try:
                    master_meta = json.loads(master_file.read_text(encoding="utf-8"))
                    # Iterujemy po wszystkich ID powiązanych z tą grupą
                    for linked_id in master_meta.get("investments", []):
                        linked_res = self.identity.get_investment_resources(linked_id)
                        if linked_res and linked_res["files"].get("anchor").exists():
                            linked_usi = json.loads(linked_res["files"]["anchor"].read_text(encoding="utf-8"))
                            # Scalamy słowniki źródeł (np. dodajemy 'rp' do rekordu 'oto')
                            for p_k, p_v in linked_usi.get("sources", {}).items():
                                if p_k not in sources:
                                    sources[p_k] = p_v
                except Exception as e:
                    logger.error(f"Error aggregating master sources for {master_id}: {e}")
        # ----------------------------------------------------

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
        loc_dict = data.get("location", {})
        coords = loc_dict.get("coords", [None, None])
        if not coords or coords[0] is None or coords[1] is None:
            address = loc_dict.get("address", "") or ""
            city = loc_dict.get("city", "") or ""
            full_address = f"{address}, {city}".strip(", ")
            if full_address:
                import logging
                logging.getLogger(__name__).info(f"Brak współrzędnych z portalu. Uruchamiam geokodowanie ratunkowe dla: {full_address}")
                from python_worker.services.here_maps_service import HereMapsService
                from python_worker.config import get_shared_config
                from python_worker.config import HERE_API_KEY
                here_service = HereMapsService(api_key=HERE_API_KEY) 
                lat, lng = here_service.geocode_address(full_address)
                if lat and lng:
                    loc_dict["coords"] = [lat, lng]
                    data["location"] = loc_dict

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
            
            if not new_coords or not new_coords[0]:
                data["nearby_investments"] = []
            elif not old_data.get("nearby_investments") or old_coords != new_coords:
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
    def process_batch(self, portal: str, investments: List[Dict], on_progress_callback: Optional[Any] = None) -> int:
        """
        Główna pętla batch: ufa całkowicie bibliotece usi-scrapers.
        Pobiera, mapuje i zrzuca plik usi_*.json.
        """
        targets, _ = self._prepare_batch_identifiers(portal, investments)
        if not targets:
            return 0

        logger.info(f"[BATCH] Delegating {len(targets)} targets to usi-scrapers process_batch_ingest...")
        batch_results = self.gateway.process_batch(portal, targets, on_progress=on_progress_callback)
        logger.info(f"[BATCH] Gateway returned {len(batch_results)} results for {portal}")
        
        saved_count = 0

        for i, data in enumerate(batch_results):
            if not data or (isinstance(data, dict) and "error" in data):
                logger.warning(f"[BATCH] Skipping item {i} due to empty data or error")
                continue

            try:
                raw_payload = data.get("raw_details", data) if isinstance(data, dict) else data
                
                # Używamy API do wstępnego wyznaczenia ID
                m_temp = transform_to_unified(portal, raw_payload, entity_type="investment") or {}
                dev_meta = self.gateway.extract_developer_meta(raw_payload, portal)
                
                item_id = str(m_temp.get("id") or m_temp.get("numeric_id") or "")
                if not item_id:
                    logger.warning(f"[BATCH] Could not resolve item_id for item {i}")
                    continue
                    
                usi_inv_id = f"{portal}_{item_id}"
                
                # Używamy StorageResolvera z biblioteki do wyznaczenia poprawnej ścieżki (tam gdzie leży raw_*)
                resolved_path = self.tech_manager.get_investment_path(portal, item_id)
                if resolved_path:
                    dest_dir = Path(resolved_path)
                    dev_slug = dest_dir.parent.name
                    inv_slug = dest_dir.name
                else:
                    dev_slug = data.get("developer_slug") or dev_meta.get("slug") or "unknown"
                    inv_slug = data.get("investment_slug") or m_temp.get("slug") or str(item_id)
                    dest_dir = self.data_dir / dev_slug / inv_slug
                
                # ARCHITECTURAL MANDATE: Używamy poprawnych adapterów do transformacji do pełnego zunifikowanego rekordu
                # (usi_*.json musi być kanoniczny, nie może być surowym słownikiem 'm')
                from python_worker.adapters.merger import Merger

                unified_data = transform_to_unified(portal, raw_payload, "investment")
                if portal == "rp":
                    _enrich_rp_unified(unified_data)
                unified_data["investment_slug"] = inv_slug
                unified_data["developer_slug"] = dev_slug
                
                # Add sources block so Merger can pick it up
                if "sources" not in unified_data:
                    unified_data["sources"] = {
                        portal: {
                            "id": str(item_id),
                            "url": raw_payload.get("url") if isinstance(raw_payload, dict) else None
                        }
                    }
                    
                # Copy image paths if provided by scraper in live fetch
                if isinstance(raw_payload, dict) and "image_paths" in raw_payload:
                    unified_data["image_paths"] = raw_payload["image_paths"]

                target_file = dest_dir / f"usi_{usi_inv_id}.json"
                existing_data = None
                if target_file.exists():
                    try:
                        existing_data = json.loads(target_file.read_text(encoding="utf-8"))
                    except Exception:
                        pass
                        
                usi_file_data = Merger.merge(
                    rp_data=unified_data if portal == "rp" else None,
                    oto_data=unified_data if portal == "oto" else None,
                    to_data=unified_data if portal == "to" else None,
                    existing_data=existing_data,
                    event="Batch Update"
                )
                
                # Upewniamy się, że podstawowe identyfikatory są nienaruszone
                usi_file_data["usi_inv_id"] = usi_inv_id
                
                # Synchronizacja zdjęć: upewnij się, że zdjęcia pobrane w batch_ingest zostaną prawidłowo podpięte
                resources = self.identity.get_investment_resources(usi_inv_id)
                if not resources:
                    resources = self._resolve_resources_manually(usi_inv_id, {
                        "sources": {portal: {"id": item_id}},
                        "developer_slug": dev_slug,
                        "investment_slug": inv_slug
                    })
                
                all_urls = usi_file_data.get("image_urls", [])
                self.image_sync.sync_investment_images(
                    usi_inv_id, 
                    usi_file_data, 
                    all_urls, 
                    skip_images=False, 
                    usi_data=existing_data or {}, 
                    resources=resources
                )

                # Wyznaczenie ścieżki i zapis pliku
                if dest_dir:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    self.repo.save_investment_json(usi_inv_id, usi_file_data, anchor_path=target_file)
                    
                    logger.info(f"[BATCH] Registered and saved {usi_inv_id} to {target_file}")
                    saved_count += 1
                else:
                    logger.error(f"[BATCH_ERROR] Brak wyznaczonej ścieżki dla {usi_inv_id}")

            except Exception as e:
                logger.error(f"[BATCH_ERROR] Błąd finalizacji dla {portal}: {e}", exc_info=True)

        # 6. Global optimization: Single index rebuild
        if saved_count > 0:
            logger.info(f"[BATCH] Finished. Saving {saved_count} items and rebuilding index.")
            inv_index.rebuild(self.data_dir, self.public_usi_dir)
            self.dm.invalidate_identifiers_cache()

        return saved_count


