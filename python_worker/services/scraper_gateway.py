# python_worker/services/scraper_gateway.py
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from usi_scrapers import api as scraper_api
from usi_scrapers import resolve_path as lib_resolve_path
from python_worker.config import get_shared_config, get_shared_fetcher

logger = logging.getLogger(__name__)

PORTAL_MAPPING = {
    "rynekpierwotny": "rp",
    "rp": "rp",
    "otodom": "oto",
    "oto": "oto",
    "tabelaofert": "to",
    "to": "to"
}

class ScraperGateway:
    @staticmethod
    def normalize_portal_name(raw_portal: str) -> str:
        """Przekształca luźną nazwę portalu na kanoniczny identyfikator systemowy."""
        raw_cleaned = str(raw_portal).lower().strip()
        
        for indicator, canonical in PORTAL_MAPPING.items():
            if indicator in raw_cleaned:
                return canonical
                
        raise ValueError(f"Unsupported or unrecognized portal: {raw_portal}")

    def __init__(self, config=None, fetcher=None):
        self._config = config or get_shared_config()
        self._fetcher = fetcher or get_shared_fetcher()

    def has_local_raw(self, portal: str, portal_id: str) -> bool:
        return scraper_api.has_local_raw(self._config, portal=portal, portal_id=str(portal_id))

    def download_raw(self, portal: str, identifier: str) -> Any:
        return scraper_api.download_raw(self._config, self._fetcher, portal, identifier)

    def load_raw(self, portal: str, identifier: str) -> Optional[Dict[str, Any]]:
        config = self._config
        return scraper_api.load_raw(config, portal, str(identifier))

    def ingest_investment_by_url(self, portal: str, url: str) -> Any:
        return scraper_api.ingest_investment_by_url(self._config, self._fetcher, portal, url)

    def refresh_investment_by_id(self, portal: str, identifier: str) -> Any:
        return scraper_api.refresh_investment_by_id(self._config, self._fetcher, portal, identifier)

    def resolve_prefix(self, portal: str) -> str:
        return scraper_api.resolve_prefix(portal)

    def download_raw_dev(self, portal: str, identifier: str) -> Any:
        # Bezwzględny rygor ID-only dla rp i oto (muszą być numeryczne)
        if portal in ("rp", "oto") and not str(identifier).isdigit():
            logger.error(f"Identifier for portal {portal} must be numeric, got: {identifier}")
            return None
        return scraper_api.download_raw_dev(self._config, self._fetcher, portal, str(identifier))

    def process_batch(self, portal: str, targets: List[str], on_progress=None) -> List[Any]:
        """
        Inteligentny dispatcher dla zadań seryjnych.
        Automatycznie wybiera tryb Ingest (URL) lub Refresh (ID).
        """
        if not targets:
            return []
            
        # Sprawdzamy pierwszy element, aby zdecydować o trybie
        if str(targets[0]).startswith("http"):
            return scraper_api.process_batch_ingest(
                self._config, self._fetcher, portal, targets, on_progress=on_progress
            )
        else:
            return scraper_api.process_batch_refresh(
                self._config, self._fetcher, portal, targets, on_progress=on_progress
            )

    def process_batch_ingest(self, portal: str, urls: List[str], on_progress=None) -> List[Any]:
        return scraper_api.process_batch_ingest(self._config, self._fetcher, portal, urls, on_progress=on_progress)

    def process_batch_refresh(self, portal: str, portal_ids: List[str], on_progress=None) -> List[Any]:
        return scraper_api.process_batch_refresh(self._config, self._fetcher, portal, portal_ids, on_progress=on_progress)

    def list_investments(self, portal: str, identifier: Optional[str] = None) -> List[Dict[str, Any]]:
        ident_str = str(identifier) if identifier is not None else None
        return scraper_api.list_investments(self._config, self._fetcher, portal, ident_str)

    def discover_investments(self, portal_key: str, identifier: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        if portal_key == "rp":
            return scraper_api.discover_rp_investments(self._config, self._fetcher, identifier=identifier, limit=limit)
        elif portal_key == "otodom":
            return scraper_api.discover_otodom_investments(self._config, self._fetcher, identifier=identifier, limit=limit)
        else:
            return scraper_api.discover_to_investments(self._config, self._fetcher, identifier=identifier, limit=limit)

    def save_images(self, urls: List[str], target_dir: Path) -> List[str]:
        from usi_scrapers.utils.images import save_images as lib_save_images
        return lib_save_images(urls, target_dir, self._config)

    @staticmethod
    def resolve_path(data: Dict[str, Any], path_str: str) -> Any:
        return lib_resolve_path(data, path_str)

    @staticmethod
    def generate_portal_mapping(portal: str, vendor_id: str) -> Dict[str, Any]:
        """Returns the canonical portal_mapping structure for a given vendor_id."""
        clean_id = str(vendor_id)
        if portal == "rp":
            return {"id": clean_id}
        elif portal == "oto":
            return {"agency_id": clean_id, "agency_ids": [clean_id]}
        elif portal == "to":
            return {"agency_id": clean_id}
        return {}

    @staticmethod
    def extract_developer_meta(raw_data: Dict[str, Any], portal: str) -> Dict[str, Any]:
        meta = scraper_api.extract_developer_meta(raw_data, portal)
        if not meta.get("id"):
            logger.debug(f"extract_developer_meta: Primary mapping failed for {portal}. Trying fallback via mapping...")
            mapping = scraper_api.get_mapping(portal)
            developer_id_path = mapping.get("developer_id")
            if developer_id_path:
                vid = lib_resolve_path(raw_data, developer_id_path)
                if vid:
                    meta["id"] = str(vid)
            
            # Ostateczny fallback dla nazwy dewelopera w TO, jeśli nadal brak
            if portal == "to" and not meta.get("name"):
                meta["name"] = raw_data.get("developer_name") or raw_data.get("vendor_name") or raw_data.get("brand", {}).get("name")
        
        return meta

    @staticmethod
    def get_mapping(portal: str) -> Dict[str, Any]:
        return scraper_api.get_mapping(portal)
