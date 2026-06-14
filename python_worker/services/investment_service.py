import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.developer_manager import DeveloperManager
from python_worker.api.utils import load_json
from python_worker.investment_index import get_investment_index

# Import our new modular components
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_editor import InvestmentEditorService
from python_worker.investment_repository import InvestmentRepository

class InvestmentService:
    """
    Facade for Investment Operations.
    Delegates functionality to specialized services:
    - IdentityResolver (resolves ID to physical paths)
    - SyncService (handles fetching, merging, image synchronization)
    - EditorService (handles saving ratings, reviews, reports)
    """
    def __init__(self, data_dir: Path = None, public_usi_dir: Path = None):
        self.data_dir = data_dir or Path(USI_DATA_DIR)
        self.public_usi_dir = public_usi_dir or Path(PUBLIC_USI_DIR)
        self._cache = {}
        
        # Shared Dependencies
        self.dm = DeveloperManager(self.data_dir)
        
        # Subsystems
        self.identity = InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)
        self.repo = InvestmentRepository(self.identity, self.data_dir)
        self.sync = InvestmentSyncService(self.identity, self.data_dir, self.public_usi_dir, self.dm, self.repo)
        self.editor = InvestmentEditorService(self.identity, self.data_dir, self.public_usi_dir, self.repo)

    # ---------------------------------------------------------
    # Identity & Path Resolution (Delegated)
    # ---------------------------------------------------------
    def get_investment_resources(self, inv_id: str) -> dict | None:
        """Universal ID-to-File mapping for investments."""
        return self.identity.get_investment_resources(inv_id)

    # ---------------------------------------------------------
    # Viewing Data
    # ---------------------------------------------------------
    def get_investment(self, system_id: str) -> dict | None:
        """Loads an investment by system_id using non-blocking fast index path."""
        if not system_id:
            return None

        resources = self.get_investment_resources(system_id)
        if not resources:
            logger.warning(f"get_investment: Resources not found for ID {system_id}")
            return None

        from python_worker.api.utils import _load_investment
        return _load_investment(
            system_id=system_id,
            data_dir=self.data_dir,
            public_usi_dir=self.public_usi_dir,
            fast_index=True,
        )

    def get_unified_view(self, inv_id: str) -> dict:
        """Dynamically aggregates data into a virtual master view."""
        if inv_id in self._cache:
            return self._cache[inv_id]

        resources = self.get_investment_resources(inv_id)
        if not resources or not resources["files"].get("anchor"):
            return {}

        anchor = json.loads(resources["files"]["anchor"].read_text())
        view = self._aggregate_anchors([anchor])
        self._cache[inv_id] = view
        return view

    def invalidate_cache(self, inv_id: str = None):
        """Invalidates cache entries and syncs to index."""
        if inv_id:
            self._cache.pop(inv_id, None)
            from python_worker.api.utils import _load_investment
            from python_worker.investment_index import get_investment_index
            entry = _load_investment(system_id=inv_id, fast_index=True)
            if entry:
                entry.pop("image_urls", None)
                entry.pop("nearby_investments", None)
                get_investment_index().add_or_update(inv_id, entry)
        else:
            # Czyszczenie pamięci podręcznej RAM serwisu - operacja O(1)
            self._cache.clear()
            # POPRAWKA: Usunięto destrukcyjne, samobójcze wywołanie get_investment_index().rebuild()

    def list_nearby_by_coordinates(self, lat: float, lon: float, max_dist_km: float = 5.0, limit: int = 12) -> list[dict]:
        """Pobiera inwestycje z indeksu na podstawie dynamicznego filtra przestrzennego."""
        return get_investment_index().get_near_coordinates(lat, lon, max_dist_km, limit)

    def list_investments_filtered(self, **kwargs) -> list[dict]:
        """Filters all investments using the global index."""
        index = get_investment_index()
        all_invs = index.get_all()
        if not kwargs:
            return all_invs
        
        filtered = all_invs
        for key, value in kwargs.items():
            if value is None or value == "":
                continue

            if key == 'onlyUnreviewed' and value is True:
                filtered = [i for i in filtered if not i.get('reviewed', False)]
            elif key == 'onlyNoPhotos' and value is True:
                filtered = [i for i in filtered if not i.get('photos') or len(i.get('photos', [])) == 0]
            elif key == 'dev':
                filtered = [i for i in filtered if i.get('developer_slug') == value]
            elif key == 'search':
                s = str(value).lower()
                filtered = [i for i in filtered if s in str(i.get('name') or '').lower() or s in str(i.get('developer') or '').lower()]
            elif key == 'sources' and isinstance(value, list):
                if len(value) == 0: continue
                filtered = [i for i in filtered if any(str(p).lower() in [str(s).lower() for s in value] for p in i.get('sources', {}).keys())]
            elif key == 'segments' and isinstance(value, list):
                if len(value) == 0: continue
                filtered = [i for i in filtered if i.get('segment') in value]
            elif key == 'cities' and isinstance(value, list):
                if len(value) == 0: continue
                filtered = [i for i in filtered if str(i.get('city') or '').lower() in [str(c).lower() for c in value]]
            elif key in ['reviewed', 'developer_slug', 'portal', 'status']:
                filtered = [i for i in filtered if i.get(key) == value]
            else:
                pass
        return filtered

    def rebuild_index(self) -> int:
        """Rebuilds the global investment index."""
        from python_worker.investment_index import get_investment_index
        return get_investment_index().rebuild()

    def _aggregate_anchors(self, anchors: list[dict]) -> dict:
        master = {
            "master_id": f"MASTER-{anchors[0]['usi_inv_id']}",
            "merged_anchors": [a.get("portal_id", "unknown") for a in anchors],
            "data": []
        }
        
        from python_worker.services.scraper_gateway import ScraperGateway
        gateway = ScraperGateway()
        
        for anchor in anchors:
            portal = anchor.get("portal")
            sources = anchor.get("sources") or {}
            portal_id = anchor.get("portal_id")

            if not portal and sources:
                for p in ("rp", "oto", "to"):
                    if p in sources:
                        portal = p
                        break
                if not portal:
                    portal = list(sources.keys())[0] if sources else "unknown"

            raw_data = gateway.load_raw(portal, str(portal_id)) if portal and portal_id else None
            
            resources = self.identity.get_investment_resources(anchor.get("usi_inv_id", ""))
            meta_data = {}
            if resources and resources["files"].get("meta"):
                meta_data = load_json(resources["files"]["meta"])
            
            master["data"].append({
                "portal": portal,
                "raw": raw_data,
                "meta": meta_data
            })
        return master

    # ---------------------------------------------------------
    # Sync & Updates (Delegated)
    # ---------------------------------------------------------
    def register_investment(self, portal=None, developer_name=None, name=None, item_id=None, url=None, vendor_id=None, payload=None, **kwargs):
        if payload is not None:
            dev_name = payload.get("developer_name")
            if dev_name and dev_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper", ""):
                dev_name = None
            
            try:
                # Call sync service which now handles full ingestion and update
                dev_slug, inv_slug, usi_inv_id, data, path = self.sync.register_investment(
                    portal=portal,
                    developer_name=dev_name,
                    name=payload.get("name"),
                    item_id=payload.get("id"),
                    url=payload.get("url"),
                    vendor_id=payload.get("vendor_id"),
                    allow_existing=True # Standard for UI trigger
                )
                
                return {
                    "ok": True, 
                    "usi_inv_id": usi_inv_id, 
                    "slug": f"{dev_slug}/{inv_slug}",
                    "message": "Rejestracja zakończona sukcesem"
                }
            except Exception as e:
                logger.error(f"Registration failed: {e}")
                return {"ok": False, "error": str(e)}
            
        # Fallback for direct calls without payload
        return self.sync.register_investment(
            portal=portal,
            developer_name=developer_name,
            name=name,
            item_id=item_id,
            url=url,
            vendor_id=vendor_id,
            **kwargs
        )

    def download_raw_json(self, portal: str, identifier: str, system_id: str):
        return self.sync.download_raw_json(portal, identifier, system_id)

    def update_investment(self, system_id, use_local_raw=False, skip_images=False, skip_index=False, skip_log=False):
        result = self.sync.update_investment(system_id, use_local_raw, skip_images, skip_index, skip_log)
        self.invalidate_cache(system_id)
        return result

    def process_batch(self, portal, investments, on_progress_callback=None):
        return self.sync.process_batch(portal, investments, on_progress_callback)

    # ---------------------------------------------------------
    # Editor Operations (Delegated)
    # ---------------------------------------------------------
    def save_ratings(self, system_id, payload):
        success = self.editor.save_ratings(system_id, payload)
        if success: self.invalidate_cache(system_id)
        return success

    def mark_as_reviewed(self, system_id):
        success = self.editor.mark_as_reviewed(system_id)
        if success: self.invalidate_cache(system_id)
        return success

    def add_report(self, system_id, note):
        success = self.editor.add_report(system_id, note)
        if success: self.invalidate_cache(system_id)
        return success

    def mark_deleted_photos(self, system_id, paths):
        success = self.editor.mark_deleted_photos(system_id, paths)
        if success: self.invalidate_cache(system_id)
        return success
