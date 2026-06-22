import json
from pathlib import Path
from typing import Optional, Dict, Any
from python_worker.config import get_shared_tech_manager, PUBLIC_USI_DIR

class InvestmentIdentityResolver:
    """
    Universal ID-to-File mapping for investments.
    Returns a map of all physical files associated with a USI Investment ID.
    
    ARCHITECTURAL MANDATE: ID-ONLY PRIORITY.
    """
    def __init__(self, data_dir: Path | str, public_usi_dir: Path | str = None):
        self.data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
        # Pobieranie poprawnego katalogu bazowego zamiast nawigacji relatywnej parent.parent
        self.public_usi_dir = Path(public_usi_dir) if public_usi_dir else Path(PUBLIC_USI_DIR)
        self._tech_manager = None

    @property
    def tech_manager(self):
        if self._tech_manager is None:
            self._tech_manager = get_shared_tech_manager()
        return self._tech_manager

    def build_index(self) -> int:
        from python_worker.investment_index import rebuild
        return rebuild(self.data_dir, self.public_usi_dir)

    def generate_deterministic_id(self, portal: str, item_id: str) -> str:
        return f"{portal}_{item_id}"

    def get_investment_resources(self, inv_id: str) -> Optional[Dict[str, Any]]:
        # Master ID — bezpośrednia ścieżka do USImaster/
        if inv_id and inv_id.startswith("IM-"):
            from python_worker.investment_merger import _usi_master_dir, MASTER_FILE_PREFIX
            master_path = _usi_master_dir() / f"{MASTER_FILE_PREFIX}{inv_id}.json"
            if master_path.exists():
                return {
                    "id": inv_id,
                    "type": "master",
                    "base_dir": master_path.parent,
                    "files": {"anchor": master_path, "meta": None, "logs": []},
                    "images_dir": None,
                    "metadata": {
                        "portal": None,
                        "portal_id": None,
                        "developer_slug": "USImaster",
                        "investment_slug": inv_id,
                        "slug": f"USImaster/{inv_id}",
                    },
                }
            return None

        from python_worker.investment_index import get_entry_by_id
        entry = get_entry_by_id(inv_id)

        if not entry:
            from python_worker.investment_index import load as load_index
            index = load_index(self.data_dir)
            entry = next((e for e in index if e.get("usi_inv_id") == inv_id), None)

        if not entry:
            return None

        return self._map_resources_from_entry(entry)


    def _map_resources_from_entry(self, entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        usi_inv_id = entry.get("usi_inv_id")
        if not usi_inv_id:
            return None

        portal = entry.get("portal")
        portal_id = entry.get("portal_id")
        
        if not portal or not portal_id:
            sources = entry.get("sources") or {}
            for p in ("rp", "oto", "to"):
                if p in sources and sources[p].get("id"):
                    portal = p
                    portal_id = sources[p].get("id")
                    break
                    
        if not portal or not portal_id:
            if "_" in usi_inv_id:
                parts = usi_inv_id.split("_", 1)
                if parts[0] in ("rp", "oto", "to"):
                    portal = parts[0]
                    portal_id = parts[1]

        inv_dir = None
        images_dir = None
        folder_path = entry.get("folder_path")
        
        if folder_path:
            # Rozwiązanie ścieżki (folder_path np. 'Public/USIdata/slug')
            project_root = self.data_dir.parent.parent
            candidate_dir = project_root / folder_path if not Path(folder_path).is_absolute() else Path(folder_path)
            if candidate_dir.exists():
                inv_dir = candidate_dir
                # Zgodnie z GEMINI.md: struktury USIdata oraz USI muszą być spójne
                images_dir = Path(str(candidate_dir).replace("USIdata", "USI"))

        if not inv_dir and self.tech_manager and portal and portal_id:
            inv_dir = self.tech_manager.get_investment_path(portal, str(portal_id))
            images_dir = self.tech_manager.get_image_path(portal, str(portal_id))
        
        if not inv_dir:
            return None

        anchor_file = inv_dir / f"usi_{portal}_{portal_id}.json"
        if not anchor_file.exists():
            candidates = list(inv_dir.glob("usi_*.json"))
            if candidates:
                anchor_file = sorted(candidates)[0]

        # POPRAWKA: Nazwa pliku meta ściśle według CANONICAL.md sekcja 3.2
        meta_file = inv_dir / f"meta_{portal}_{portal_id}.json"

        return {
            "id": usi_inv_id,
            "type": "investment",
            "base_dir": inv_dir,
            "files": {
                "anchor": anchor_file if anchor_file.exists() else None,
                "meta": meta_file if meta_file.exists() else None,
                "logs": [inv_dir / "deletion_list.json"] if (inv_dir / "deletion_list.json").exists() else []
            },
            "images_dir": images_dir,
            "metadata": {
                "portal": portal,
                "portal_id": portal_id,
                "developer_slug": entry.get("developer_slug"),
                "investment_slug": entry.get("investment_slug"),
                "slug": f"{entry.get('developer_slug')}/{entry.get('investment_slug')}"
            }
        }
