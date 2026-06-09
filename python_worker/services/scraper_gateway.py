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
        config = self._config
        res = scraper_api.load_raw(config, portal, str(identifier))
        if res: return res
        
        # MANDAT ROBUSTNOŚCI: Fallback na ręczne przeszukanie katalogów, jeśli API zawiedzie
        # (Przydatne gdy ID w indeksie scrapera rozjechało się z ID w trackerze)
        logger.debug(f"load_raw: API failed for {portal}/{identifier}. Trying manual search...")
        from pathlib import Path
        public_dir = Path(config.public_dir)
        # Przeszukujemy USIdata w poszukiwaniu pliku raw_{portal}_{identifier}.json
        matches = list(public_dir.rglob(f"raw_{portal}_{identifier}.json"))
        if matches:
            try:
                import json
                with open(matches[0], "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return None

    def ingest_investment_by_url(self, portal: str, url: str) -> Any:
        return scraper_api.ingest_investment_by_url(self._config, self._fetcher, portal, url)

    def refresh_investment_by_id(self, portal: str, identifier: str) -> Any:
        return scraper_api.refresh_investment_by_id(self._config, self._fetcher, portal, identifier)

    def resolve_prefix(self, portal: str) -> str:
        return scraper_api.resolve_prefix(portal)

    def download_raw_dev(self, portal: str, identifier: str) -> Any:
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

    @staticmethod
    def resolve_path(target: Dict[str, Any], path_expression: str) -> Any:
        return lib_resolve_path(target, path_expression)

    @staticmethod
    def extract_developer_meta(raw_data: Dict[str, Any], portal: str) -> Dict[str, Any]:
        meta = scraper_api.extract_developer_meta(raw_data, portal)
        if not meta.get("id"):
            logger.debug(f"extract_developer_meta: Mapping failed for {portal}. Raw keys: {list(raw_data.keys())}")
            if portal == "oto":
                vid = lib_resolve_path(raw_data, "props.pageProps.ad.agency.id|agency.id")
                if vid: meta["id"] = str(vid)
            elif portal == "to":
                # Szukamy ID dewelopera w różnych miejscach dla TO
                vid = raw_data.get("klient-id") or raw_data.get("klient_id") or raw_data.get("developer_id")
                
                # Przeszukiwanie additionalProperty (częste w JSON-LD)
                if not vid and "additionalProperty" in raw_data:
                    props = raw_data["additionalProperty"]
                    if isinstance(props, list):
                        for p in props:
                            if isinstance(p, dict) and p.get("name") in ["klient-id", "klient_id", "developer_id"]:
                                vid = p.get("value")
                                break
                
                if vid: meta["id"] = str(vid)
                
                # Jeśli nadal brak ID, ale mamy dewelopera w 'brand' (JSON-LD)
                if not meta.get("id") and "brand" in raw_data:
                    brand = raw_data["brand"]
                    if isinstance(brand, dict):
                        meta["name"] = brand.get("name") or meta.get("name")
                        # Czasem ID jest zaszyte w URL brandu
                        b_url = brand.get("url")
                        if b_url and "deweloperzy/" in b_url:
                            meta["id"] = b_url.split("deweloperzy/")[-1].split("?")[0].split("/")[0]
                        elif b_url and "firmy/" in b_url:
                             meta["id"] = b_url.split("firmy/")[-1].split("?")[0].split("/")[0]

                # Sprawdzanie 'offers' (JSON-LD)
                if not meta.get("id") and "offers" in raw_data:
                    offers = raw_data["offers"]
                    if isinstance(offers, list) and len(offers) > 0:
                        seller = offers[0].get("seller")
                        if isinstance(seller, dict):
                            meta["name"] = seller.get("name") or meta.get("name")
                            s_url = seller.get("url")
                            if s_url and "deweloperzy/" in s_url:
                                meta["id"] = s_url.split("deweloperzy/")[-1].split("?")[0].split("/")[0]

                # Jeśli nadal brak, szukamy czegokolwiek co wygląda jak klient-id w logu biblioteki
                # (Jeśli biblioteka v1.3.0 to wyciągnęła, to musi to być w raw_data pod jakimś kluczem)
                if not meta.get("id"):
                    for k, v in raw_data.items():
                        if "id" in k.lower() and isinstance(v, (str, int)) and str(v).isdigit():
                             logger.debug(f"TO: Potential ID found in key {k}: {v}")

                # Jeśli mapping zwrócił nazwę inwestycji jako nazwę dewelopera, czyścimy ją
                if meta.get("name") and ("Zakątek" in meta["name"] or "Inwestycja" in meta["name"]):
                    meta["name"] = None
        
        # Ostateczny fallback dla nazwy dewelopera w TO
        if portal == "to" and not meta.get("name"):
            meta["name"] = raw_data.get("developer_name") or raw_data.get("vendor_name") or raw_data.get("brand", {}).get("name")
            
        return meta

    @staticmethod
    def get_mapping(portal: str) -> Dict[str, Any]:
        return scraper_api.get_mapping(portal)
