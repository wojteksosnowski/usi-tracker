import json
from pathlib import Path
from functools import lru_cache

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.developer_manager import DeveloperManager

# Import our new modular components
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_editor import InvestmentEditorService

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
        
        # Shared Dependencies
        self.dm = DeveloperManager(self.data_dir)
        
        # Subsystems
        self.identity = InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)
        self.sync = InvestmentSyncService(self.identity, self.data_dir, self.public_usi_dir, self.dm)
        self.editor = InvestmentEditorService(self.identity, self.data_dir, self.public_usi_dir)

    # ---------------------------------------------------------
    # Identity & Path Resolution (Delegated)
    # ---------------------------------------------------------
    def get_investment_resources(self, inv_id: str) -> dict | None:
        """Universal ID-to-File mapping for investments."""
        return self.identity.get_investment_resources(inv_id)

    # ---------------------------------------------------------
    # Viewing Data
    # ---------------------------------------------------------
    def get_investment(self, dev_slug: str, inv_slug: str, portal: str | None = None, system_id: str | None = None) -> dict | None:
        """Loads an investment via ID-Only architecture."""
        from python_worker.api.utils import _load_investment
        return _load_investment(
            dev_slug, inv_slug,
            data_dir=self.data_dir,
            public_usi_dir=self.public_usi_dir,
            portal=portal,
            system_id=system_id
        )

    @lru_cache(maxsize=128)
    def get_unified_view(self, inv_id: str) -> dict:
        """Dynamically aggregates data into a virtual master view."""
        resources = self.get_investment_resources(inv_id)
        if not resources or not resources["files"].get("anchor"):
            return {}

        anchor = json.loads(resources["files"]["anchor"].read_text())
        return self._aggregate_anchors([anchor])

    def _aggregate_anchors(self, anchors: list[dict]) -> dict:
        master = {
            "master_id": f"MASTER-{anchors[0]['usi_inv_id']}",
            "merged_anchors": [a.get("portal_id", "unknown") for a in anchors],
            "data": []
        }
        
        for anchor in anchors:
            portal = anchor.get("portal")
            sources = anchor.get("sources") or {}
            if not portal and sources:
                for p in ("rp", "oto", "to"):
                    if p in sources:
                        portal = p
                        break
                if not portal:
                    portal = list(sources.keys())[0] if sources else "unknown"

            raw_path = self.public_usi_dir.parent / "USIdata" / anchor.get("raw_file", "")
            meta_path = self.public_usi_dir.parent / "USIdata" / anchor.get("meta_file", "")
            
            raw_data = self._load_json(raw_path)
            meta_data = self._load_json(meta_path)
            
            master["data"].append({
                "portal": portal,
                "raw": raw_data,
                "meta": meta_data
            })
        return master

    def _load_json(self, path: Path) -> dict:
        if not path.exists() or not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    # ---------------------------------------------------------
    # Sync & Updates (Delegated)
    # ---------------------------------------------------------
    def register_investment(self, *args, **kwargs):
        return self.sync.register_investment(*args, **kwargs)

    def update_investment(self, system_id, use_local_raw=False, skip_images=False, skip_index=False, skip_log=False):
        return self.sync.update_investment(system_id, use_local_raw, skip_images, skip_index, skip_log)

    def process_batch(self, portal, investments, on_progress_callback=None):
        return self.sync.process_batch(portal, investments, on_progress_callback)

    # ---------------------------------------------------------
    # Editor Operations (Delegated)
    # ---------------------------------------------------------
    def save_ratings(self, system_id, payload):
        return self.editor.save_ratings(system_id, payload)

    def mark_as_reviewed(self, system_id):
        return self.editor.mark_as_reviewed(system_id)

    def add_report(self, system_id, note):
        return self.editor.add_report(system_id, note)

    def mark_deleted_photos(self, system_id, paths):
        return self.editor.mark_deleted_photos(system_id, paths)
