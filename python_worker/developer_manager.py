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

    # Repository Delegation
    def get_developer(self, dev_slug: str): return self.repo.get_developer(dev_slug)
    def get_developer_by_id(self, usi_dev_id: str): return self.repo.get_developer_by_id(usi_dev_id)
    def get_developer_resources(self, usi_dev_id: str): return self.repo.get_developer_resources(usi_dev_id)
    def list_developers(self, only_merged: bool = False): return self.repo.list_developers(only_merged)
    def save_raw_json(self, *args, **kwargs): return self.repo.save_raw_json(*args, **kwargs)
    def save_dev_raw_json(self, *args, **kwargs): return self.repo.save_dev_raw_json(*args, **kwargs)
    def create_developer_file(self, *args, **kwargs): return self.repo.create_developer_file(*args, **kwargs)
    def append_dev_log(self, *args, **kwargs): return self.repo.append_dev_log(*args, **kwargs)
    def log_event(self, *args, **kwargs): return self.repo.log_event(*args, **kwargs)
    def resolve_dev_slug(self, *args, **kwargs): return self.repo.resolve_dev_slug(*args, **kwargs)
    def resolve_id_to_slug(self, *args, **kwargs): return self.repo.resolve_id_to_slug(*args, **kwargs)
    def get_total_pending_count(self): return self.repo.get_total_pending_count()

    # Indexer Delegation
    def generate_usi_id(self, prefix: str): return self.indexer.generate_usi_id(prefix)
    def get_existing_identifiers(self): return self.indexer.get_existing_identifiers()
    def find_developer_by_id(self, *args, **kwargs): return self.indexer.find_developer_by_id(*args, **kwargs)
    def find_by_portal_id(self, *args, **kwargs): return self.indexer.find_by_portal_id(*args, **kwargs)

    # Merge Manager Delegation
    def merge_by_id(self, *args, **kwargs): return self.merger.merge_by_id(*args, **kwargs)
    def unmerge_by_id(self, *args, **kwargs): return self.merger.unmerge_by_id(*args, **kwargs)
    def add_suggestion(self, *args, **kwargs): return self.merger.add_suggestion(*args, **kwargs)
    def dismiss_suggestion_by_id(self, *args, **kwargs): return self.merger.dismiss_suggestion_by_id(*args, **kwargs)
