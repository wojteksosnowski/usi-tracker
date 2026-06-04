import json
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("USIWorker.InvestmentRepo")

class InvestmentRepository:
    """
    Repository for storing and retrieving canonical investment JSON files (`usi_*.json`) 
    and related artifacts (ratings, POI data).
    Enforces the ID-only architecture by resolving IDs to physical paths using InvestmentIdentityResolver.
    """
    def __init__(self, identity_resolver, data_dir: Path):
        self.identity = identity_resolver
        self.data_dir = data_dir

    def _get_anchor_path(self, system_id: str) -> Path:
        res = self.identity.get_investment_resources(system_id)
        if not res or not res.get("files") or not res["files"].get("anchor"):
            raise FileNotFoundError(f"Investment {system_id} not found or no physical anchor.")
        return res["files"]["anchor"]

    def _get_dir_from_system_id(self, system_id: str) -> Path:
        return self._get_anchor_path(system_id).parent

    def get_investment_json(self, system_id: str) -> dict | None:
        """Loads the canonical unified JSON for the investment."""
        try:
            target_file = self._get_anchor_path(system_id)
            if target_file.exists():
                with open(target_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except FileNotFoundError:
            return None
        return None

    def save_investment_json(self, system_id: str, data: dict):
        """Saves the canonical unified JSON for the investment."""
        target_file = self._get_anchor_path(system_id)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def create_investment_skeleton(self, dev_slug: str, inv_slug: str, portal: str, skeleton_data: dict, item_id: str = None) -> Path:
        """
        Creates a new investment directory and its initial usi_*.json file.
        This is a special case where the system_id might not yet be resolvable 
        because the directory doesn't exist yet.
        """
        inv_dir = self.data_dir / dev_slug / inv_slug
        inv_dir.mkdir(parents=True, exist_ok=True)
        filename = f"usi_{portal}_{item_id}.json" if item_id else f"usi_{portal}_{inv_slug}.json"
        target_file = inv_dir / filename
        
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(skeleton_data, f, indent=2, ensure_ascii=False)
        return target_file

    def get_ratings(self, system_id: str) -> dict:
        """Gets ratings for the investment."""
        try:
            target_dir = self._get_dir_from_system_id(system_id)
            ratings_file = target_dir / "ratings.json"
            if ratings_file.exists():
                with open(ratings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except FileNotFoundError:
            pass
        return {}

    def save_ratings(self, system_id: str, ratings_data: dict, inv_slug: str = None):
        """Saves ratings for the investment. Supports (system_id, ratings) and (dev, inv, ratings)."""
        if inv_slug:
            target_dir = self.data_dir / system_id / inv_slug
        else:
            target_dir = self._get_dir_from_system_id(system_id)
            
        ratings_file = target_dir / "ratings.json"
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(ratings_file, "w", encoding="utf-8") as f:
            json.dump(ratings_data, f, indent=2, ensure_ascii=False)

    def get_poi_data(self, system_id: str) -> dict | None:
        """Gets the reports_poi.json file data."""
        try:
            target_dir = self._get_dir_from_system_id(system_id)
            poi_file = target_dir / "reports_poi.json"
            if poi_file.exists():
                with open(poi_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except FileNotFoundError:
            pass
        return None

    def save_poi_data(self, system_id: str, poi_data: dict):
        """Saves the reports_poi.json file data."""
        target_dir = self._get_dir_from_system_id(system_id)
        poi_file = target_dir / "reports_poi.json"
        with open(poi_file, "w", encoding="utf-8") as f:
            json.dump(poi_data, f, indent=2, ensure_ascii=False)

    def mark_as_deleted(self, system_id: str, deleted_items: list[str], inv_slug: str = None):
        """Saves the deleted properties list. Supports (system_id, items) and (dev, inv, items)."""
        if inv_slug:
            target_dir = self.data_dir / system_id / inv_slug
        else:
            target_dir = self._get_dir_from_system_id(system_id)
            
        deletion_file = target_dir / "deletion_list.json"
        target_dir.mkdir(parents=True, exist_ok=True)
        with open(deletion_file, "w", encoding="utf-8") as f:
            from datetime import datetime
            json.dump({"paths": deleted_items, "updated_at": datetime.now().isoformat()}, f, indent=2, ensure_ascii=False)

    def get_deleted_items(self, system_id: str) -> list[str]:
        """Gets the list of manually deleted property IDs."""
        try:
            target_dir = self._get_dir_from_system_id(system_id)
            deletion_file = target_dir / "deletion_list.json"
            if deletion_file.exists():
                with open(deletion_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data.get("paths", [])
                    return data
        except FileNotFoundError:
            pass
        return []
