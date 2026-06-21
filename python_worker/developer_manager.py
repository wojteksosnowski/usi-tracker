import logging
from pathlib import Path

from python_worker.developer_repository import DeveloperRepository
from python_worker.developer_indexer import DeveloperIndexer
from python_worker.developer_merge_manager import DeveloperMergeManager

logger = logging.getLogger(__name__)

class DeveloperManager:
    """Facade over Developer modules"""
    def __init__(self, data_dir: Path, dev_dir: Path = None):
        self.repo = DeveloperRepository(data_dir, dev_dir)
        self.indexer = DeveloperIndexer(self.repo)
        self.merger = DeveloperMergeManager(self.repo, self.indexer)

    @property
    def dev_dir(self): return self.repo.dev_dir

    @property
    def data_dir(self): return self.repo.data_dir

    # Repository Delegation
    def get_developer(self, usi_dev_id: str): 
        """MANDAT ID-ONLY: Pobiera dewelopera wyłącznie po identyfikatorze USI (DEV-...)."""
        return self.repo.get_developer(usi_dev_id)
    
    def get_developer_by_id(self, usi_dev_id: str): return self.repo.get_developer_by_id(usi_dev_id)
    def get_developer_resources(self, usi_dev_id: str): return self.repo.get_developer_resources(usi_dev_id)
    def list_developers(self, only_merged: bool = False): return self.repo.list_developers(only_merged, self.indexer.get_existing_identifiers())
    def save_raw_json(self, data: dict, portal_id: str, portal_prefix: str): 
        return self.repo.save_raw_json(data, portal_id, portal_prefix)
    def save_dev_raw_json(self, data: dict, portal_prefix: str, portal_id: str): 
        return self.repo.save_dev_raw_json(data, portal_prefix, portal_id)
    def create_developer_file(self, *args, **kwargs): return self.repo.create_developer_file(*args, **kwargs)
    def append_dev_log(self, *args, **kwargs): return self.repo.append_dev_log(*args, **kwargs)
    def log_event(self, *args, **kwargs): return self.repo.log_event(*args, **kwargs)
    def get_total_pending_count(self): return self.repo.get_total_pending_count(self.indexer.get_existing_identifiers())

    def get_unregistered_count(self, system_id: str, identifiers: dict = None) -> int:
        """Returns count of items in discovery.json that are not yet registered."""
        try:
            dev = self.get_developer_by_id(system_id)
            if not dev: return 0
            
            dev_dir = dev.get("directory")
            if not dev_dir: return 0
            
            return self.get_unregistered_count_from_dir(Path(dev_dir), identifiers)
        except Exception as e:
            logger.debug(f"Error getting unregistered count for {system_id}: {e}")
            return 0

    def get_unregistered_count_from_dir(self, dev_dir: Path, identifiers: dict = None) -> int:
        """
        Ultra-wydajne liczenie nieobsłużonych inwestycji bezpośrednio z katalogu.
        Omija lookupy dewelopera, co pozwala na masowe przetwarzanie tysięcy rekordów.
        """
        try:
            discovery_file = dev_dir / "discovery.json"
            if not discovery_file.exists():
                return 0
            
            import json
            with open(discovery_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                return 0

            # Recalculate 'registered' status against current DB to be accurate
            if identifiers is None:
                identifiers = self.get_existing_identifiers()
            
            rp_ids = identifiers.get("rp_ids", set())
            oto_ids = identifiers.get("oto_ids", set())
            to_ids = identifiers.get("to_ids", set())
            
            count = 0
            for item in data.get("items", []):
                portal = item.get("portal")
                is_registered = False
                if portal == "rp":
                    is_registered = str(item.get("id")) in rp_ids
                elif portal in ("otodom", "oto"):
                    is_registered = str(item.get("id")) in oto_ids
                elif portal in ("to", "tabelaofert"):
                    is_registered = str(item.get("id")) in to_ids
                
                if not is_registered:
                    count += 1
            return count
        except Exception as e:
            logger.error(f"Error in get_unregistered_count_from_dir: {e}")
            return 0
    def get_existing_identifiers(self): return self.indexer.get_existing_identifiers()
    def invalidate_identifiers_cache(self): return self.indexer.invalidate_identifiers_cache()
    def find_developer_by_id(self, *args, **kwargs): return self.indexer.find_developer_by_id(*args, **kwargs)
    def find_by_portal_id(self, *args, **kwargs): return self.indexer.find_by_portal_id(*args, **kwargs)

    # Merge Manager Delegation
    def merge_by_id(self, *args, **kwargs): return self.merger.merge_by_id(*args, **kwargs)
    def unmerge_by_id(self, *args, **kwargs): return self.merger.unmerge_by_id(*args, **kwargs)

    def auto_merge_from_investments(self, target_entry: dict, source_entry: dict) -> None:
        """Automatycznie scala deweloperów na podstawie połączonych inwestycji."""
        if not target_entry or not source_entry:
            return

        t_dev_id = target_entry.get("usi_dev_id")
        s_dev_id = source_entry.get("usi_dev_id")
        
        # Jeśli identyfikatory są identyczne lub któregoś brakuje – brak podstaw do łączenia
        if not t_dev_id or not s_dev_id or t_dev_id == s_dev_id:
            return

        t_dev = self.get_developer_by_id(t_dev_id)
        s_dev = self.get_developer_by_id(s_dev_id)
        
        if not t_dev or not s_dev:
            return

        t_master = t_dev.get("master_id") or t_dev_id
        s_master = s_dev.get("master_id") or s_dev_id
        
        # Jeśli nie mają wspólnego mianownika (mastera) – wykonaj automatyczne złączenie!
        if t_master != s_master:
            logger.info(f"Automatyczne łączenie deweloperów {t_dev_id} <- {s_dev_id} z powodu scalenia ich inwestycji.")
            self.merge_by_id(t_dev_id, s_dev_id)
