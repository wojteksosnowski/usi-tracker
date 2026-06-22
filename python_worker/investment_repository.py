import json
import logging
from pathlib import Path
from datetime import datetime
from python_worker.config import get_shared_tech_manager

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

    def save_investment_json(self, system_id: str, data: dict, anchor_path: Path = None):
        """Saves the canonical unified JSON for the investment atomically."""
        target_file = anchor_path or self._get_anchor_path(system_id)
        import tempfile
        import os
        fd, temp_path = tempfile.mkstemp(dir=target_file.parent, prefix=".", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, target_file)

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
        except json.JSONDecodeError as e:
            logger.error(f"Corrupted ratings.json for {system_id}: {e}. Backing up and starting fresh.")
            try:
                import shutil
                shutil.copy(ratings_file, target_dir / "ratings.json.corrupted")
            except Exception:
                pass
        return {}

    def save_ratings(self, system_id: str, ratings_data: dict):
        """Saves ratings for the investment."""
        target_dir = self._get_dir_from_system_id(system_id)
            
        ratings_file = target_dir / "ratings.json"
        target_dir.mkdir(parents=True, exist_ok=True)
        import tempfile
        import os
        fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix=".", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(ratings_data, f, indent=2, ensure_ascii=False)
        os.replace(temp_path, ratings_file)

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

    def mark_as_deleted(self, system_id: str, deleted_items: list[str]):
        """Saves the deleted properties list."""
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
        except Exception:
            pass
        return []
    def get_all_system_ids(self) -> list[str]:
        """Pobiera wszystkie identyfikatory inwestycji z indeksu."""
        from python_worker.investment_index import get_investment_index, load
        idx = get_investment_index()
        # Jeśli indeks w pamięci jest pusty, wymusza ładowanie
        entries = idx.get_all() if getattr(idx, "_index", None) else load(self.data_dir)
        return [entry.get("usi_inv_id") for entry in entries if entry.get("usi_inv_id")]

    def get_master_data(self, master_id: str, inv_dir: Path) -> tuple[list, str | None]:
        """
        Wczytuje lokalny rekord scalenia Master (T3) przy użyciu globalnego mechanizmu.
        Zwraca listę jednostek składowych oraz kanoniczny identyfikator Master (primary_id).
        """
        from python_worker.investment_merger import InvestmentMerger
        im = InvestmentMerger(self.data_dir)
        
        # Omijamy primary_id i pozwalamy na wyszukanie w indeksie
        master_data, master_path = im._load_master_file(master_id)
        
        if not master_data:
            return [], None
            
        members = master_data.get("members", [])
        master_usi_inv_id = members[0].get("usi_inv_id") if members else None
        return members, master_usi_inv_id
