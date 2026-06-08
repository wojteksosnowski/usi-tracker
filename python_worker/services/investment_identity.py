import json
from pathlib import Path
from python_worker.config import get_shared_tech_manager

class InvestmentIdentityResolver:
    """
    Universal ID-to-File mapping for investments.
    Returns a map of all physical files associated with a USI Investment ID.
    
    ARCHITECTURAL MANDATE: ID-ONLY PRIORITY.
    This is the primary method for resolving physical resources. Never use slugs
    for file lookup if an ID is available.
    """
    def __init__(self, data_dir: Path | str, public_usi_dir: Path | str):
        self.data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
        self.public_usi_dir = Path(public_usi_dir) if isinstance(public_usi_dir, str) else public_usi_dir
        self._tech_manager = None

    @property
    def tech_manager(self):
        if self._tech_manager is None:
            self._tech_manager = get_shared_tech_manager()
        return self._tech_manager

    def build_index(self):
        """Triggers a full rebuild of the investment index."""
        from python_worker.investment_index import rebuild
        return rebuild(self.data_dir, self.public_usi_dir)

    def generate_deterministic_id(self, portal: str, item_id: str) -> str:
        """Generates a stable system ID based on portal and source ID."""
        return f"{portal}_{item_id}"

    def get_investment_resources(self, inv_id: str) -> dict | None:
        from python_worker.investment_index import get_entry_by_id
        entry = get_entry_by_id(inv_id)
        
        if not entry:
            # Fallback if hot index is not yet populated or ID is new
            from python_worker.investment_index import load as load_index
            index = load_index(self.data_dir)
            entry = next((e for e in index if e.get("usi_inv_id") == inv_id), None)
            
        if not entry:
            return None

        return self._map_resources_from_entry(entry)

    def _map_resources_from_entry(self, entry: dict) -> dict | None:
        """Determines physical file locations. Prioritizes cached folder_path from index."""
        portal = entry.get("portal")
        portal_id = entry.get("portal_id")
        
        if not portal or not portal_id:
            sources = entry.get("sources") or {}
            for p in ("rp", "oto", "to"):
                if p in sources and sources[p].get("id"):
                    portal = p
                    portal_id = sources[p].get("id")
                    break

        # OPTIMIZATION: Use cached folder_path if available in index entry
        inv_dir = None
        images_dir = None
        folder_path = entry.get("folder_path")
        
        if folder_path:
            # folder_path in index is relative to root (e.g., Public/USIdata/dev/inv)
            # We need to ensure it's resolved relative to self.data_dir's parent
            project_root = self.data_dir.parent.parent
            candidate_dir = project_root / folder_path
            if candidate_dir.exists():
                inv_dir = candidate_dir
                # Images are usually in Public/USI/dev/inv
                images_dir = project_root / folder_path.replace("USIdata", "USI")

        # Fallback to TechnicalDataManager if not found or not in index
        if not inv_dir and self.tech_manager and portal and portal_id:
            inv_dir = self.tech_manager.get_investment_path(portal, str(portal_id))
            images_dir = self.tech_manager.get_image_path(portal, str(portal_id))
        
        if not inv_dir:
            return None

        anchor_file = inv_dir / f"usi_{portal}_{portal_id}.json"
        if not anchor_file.exists():
            # Robustness fallback (06.01.10): Find any usi_*.json in the resolved folder
            candidates = list(inv_dir.glob("usi_*.json"))
            if candidates:
                anchor_file = sorted(candidates)[0]

        raw_file = inv_dir / f"raw_{portal}_{portal_id}.json"
        if not raw_file.exists():
             # Fallback for raw files too
             raw_candidates = list(inv_dir.glob(f"raw_{portal}_*.json")) or list(inv_dir.glob("raw_*.json"))
             if raw_candidates:
                 raw_file = sorted(raw_candidates)[0]
        
        # Meta/ratings files are still partially slug-based in names, but located in ID-resolved folder
        inv_slug = entry.get("investment_slug")
        meta_file = inv_dir / f"meta_{inv_slug}_ratings.json" if inv_slug else None

        return {
            "id": entry["usi_inv_id"],
            "type": "investment",
            "base_dir": inv_dir,
            "files": {
                "anchor": anchor_file if anchor_file and anchor_file.exists() else None,
                "raw": raw_file if raw_file and raw_file.exists() else None,
                "meta": meta_file if meta_file and meta_file.exists() else None,
                "logs": [inv_dir / "deletion_list.json"] if (inv_dir / "deletion_list.json").exists() else []
            },
            "images_dir": images_dir if images_dir and images_dir.exists() else None,
            "metadata": {
                "portal": portal,
                "portal_id": portal_id,
                "developer_slug": entry.get("developer_slug"),
                "investment_slug": inv_slug,
                "slug": f"{entry.get('developer_slug')}/{inv_slug}"
            }
        }

