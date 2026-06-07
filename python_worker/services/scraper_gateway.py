# python_worker/services/scraper_gateway.py
import logging
from typing import List, Dict, Any, Optional
from usi_scrapers import api as scraper_api
from usi_scrapers import resolve_path as lib_resolve_path
from python_worker.config import get_shared_config, get_shared_fetcher

logger = logging.getLogger(__name__)

class ScraperGateway:
    def __init__(self, config=None, fetcher=None):
        self._config = config or get_shared_config()
        self._fetcher = fetcher or get_shared_fetcher()

    def has_local_raw(self, portal: str, portal_id: str) -> bool:
        return scraper_api.has_local_raw(self._config, portal=portal, portal_id=str(portal_id))

    def download_raw(self, portal: str, identifier: str) -> Any:
        return scraper_api.download_raw(self._config, self._fetcher, portal, identifier)

    def load_raw(self, portal: str, identifier: str) -> Optional[Dict[str, Any]]:
        return scraper_api.load_raw(self._config, portal, str(identifier))

    def ingest_investment_by_url(self, portal: str, url: str) -> Any:
        return scraper_api.ingest_investment_by_url(self._config, self._fetcher, portal, url)

    def refresh_investment_by_id(self, portal: str, identifier: str) -> Any:
        return scraper_api.refresh_investment_by_id(self._config, self._fetcher, portal, identifier)

    def resolve_prefix(self, portal: str) -> str:
        return scraper_api.resolve_prefix(portal)

    def download_raw_dev(self, portal: str, identifier: str) -> Any:
        return scraper_api.download_raw_dev(self._config, self._fetcher, portal, str(identifier))

    def process_batch(self, portal: str, targets: List[str], on_progress=None) -> List[Any]:
        return scraper_api.process_batch(self._config, self._fetcher, portal, targets, on_progress=on_progress)

    def list_investments(self, portal: str, identifier: str) -> List[Dict[str, Any]]:
        return scraper_api.list_investments(self._config, self._fetcher, portal, str(identifier))

    def discover_investments(self, portal_key: str, identifier: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if portal_key == "rp":
            return scraper_api.discover_rp_investments(self._config, self._fetcher, identifier=identifier, limit=limit)
        elif portal_key == "otodom":
            return scraper_api.discover_otodom_investments(self._config, self._fetcher, identifier=identifier, limit=limit)
        else:
            return scraper_api.discover_to_investments(self._config, self._fetcher, identifier=identifier, limit=limit)

    @staticmethod
    def resolve_path(target: Dict[str, Any], path_expression: str) -> Any:
        return lib_resolve_path(target, path_expression)

    @staticmethod
    def extract_developer_meta(raw_data: Dict[str, Any], portal: str) -> Dict[str, Any]:
        return scraper_api.extract_developer_meta(raw_data, portal)

    @staticmethod
    def get_mapping(portal: str) -> Dict[str, Any]:
        return scraper_api.get_mapping(portal)
