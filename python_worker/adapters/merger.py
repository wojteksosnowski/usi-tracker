import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class Merger:
    @staticmethod
    def _detect_changes(old: Dict[str, Any], new: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Compares significant fields and returns a list of change objects."""
        changes: List[Dict[str, Any]] = []
        
        fields = [
            ("financials.price_avg", ["financials", "price_avg"]),
            ("financials.price_min", ["financials", "price_min"]),
            ("financials.price_max", ["financials", "price_max"]),
            ("financials.price_m2_min", ["financials", "price_m2_min"]),
            ("financials.price_m2_max", ["financials", "price_m2_max"]),
            ("specifications.units_count", ["specifications", "units_count"]),
            ("specifications.ceiling_height", ["specifications", "ceiling_height"]),
            ("specifications.ceiling_height_min", ["specifications", "ceiling_height_min"]),
            ("specifications.ceiling_height_max", ["specifications", "ceiling_height_max"]),
            ("specifications.delivery_date", ["specifications", "delivery_date"]),
            ("specifications.segment", ["specifications", "segment"]),
            ("location.coords", ["location", "coords"]),
            ("images_count", ["images_count"]),
            ("status", ["status"]),
        ]

        def get_nested(d: Any, path: List[str]) -> Any:
            for k in path:
                if not isinstance(d, dict): 
                    return None
                d = d.get(k)
            return d

        for key, path in fields:
            old_val = get_nested(old, path)
            new_val = get_nested(new, path)
            
            if old_val != new_val and new_val is not None:
                changes.append({
                    "field": key,
                    "old": old_val,
                    "new": new_val
                })
        
        return changes

    @staticmethod
    def merge(
        rp_data: Optional[Dict[str, Any]] = None, 
        oto_data: Optional[Dict[str, Any]] = None, 
        to_data: Optional[Dict[str, Any]] = None, 
        meta_ratings: Optional[Dict[str, Any]] = None, 
        existing_data: Optional[Dict[str, Any]] = None, 
        event: Optional[str] = None
    ) -> Dict[str, Any]:
        """Merges unified data from multiple sources into a single USI Unified JSON."""
        
        # Słowniki wejściowe rp_data, oto_data, to_data MUSZĄ być już 
        # zunifikowane przez usi_scrapers.mapping.transform_to_unified()
        
        base = rp_data or oto_data or to_data or existing_data or {}
        if not base: 
            return {}

        existing_audit = (existing_data or {}).get("audit", {})
        
        result = {
            "investment_slug": base.get("investment_slug"),
            "developer_slug": base.get("developer_slug"),
            "usi_dev_id": base.get("usi_dev_id") or (existing_data or {}).get("usi_dev_id"),
            "name": base.get("name") or (existing_data or {}).get("name"),
            "developer": base.get("developer_name") or base.get("developer") or (existing_data or {}).get("developer"),
            "website": base.get("website") or (existing_data or {}).get("website"),
            "status": (meta_ratings or {}).get("status") or (existing_data or {}).get("status") or "Brak",
            "sources": {},
            "location": base.get("location", {}).copy() if base.get("location") else {},
            "specifications": base.get("specifications", {}).copy() if base.get("specifications") else {},
            "financials": base.get("financials", {}).copy() if base.get("financials") else {},
            "amenities": {"labels": [], "raw_codes": []},
            "ratings": meta_ratings or (existing_data or {}).get("ratings") or {},
            "images_count": base.get("images_count") or 0,
            "image_paths": base.get("image_paths") or [],
            "image_urls": base.get("image_urls") or [],
            "audit": {
                "created_at": existing_audit.get("created_at") or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "history": existing_audit.get("history", [])
            }
        }

        # Agregacja unikalnych adresów URL zdjęć i ujednoliconych udogodnień
        all_image_urls = set(result["image_urls"])
        all_labels = set()
        all_codes = set()

        # Przetwarzanie kaskadowe danych z portali (Zasada: Słabsze źródła nie nadpisują silniejszych)
        # transform_to_unified gwarantuje, że podstruktury 'location', 'financials' mają stały schemat
        for portal, portal_data in [("to", to_data), ("oto", oto_data), ("rp", rp_data)]:
            if not portal_data:
                continue
                
            # Fallback dla starszych (płaskich) kluczy z transform_to_unified
            flat_mappings = {
                "location": ["city", "street", "address", "region", "latitude", "longitude"],
                "specifications": ["units_count", "ceiling_height_min", "ceiling_height_max", "ceiling_height", "segment", "delivery_date", "delivery_quarter", "delivery_year"],
                "financials": ["price_min", "price_max", "price_m2_min", "price_m2_max"]
            }
            
            for section in ("location", "specifications", "financials"):
                if section not in portal_data:
                    portal_data[section] = {}
                
                for flat_key in flat_mappings[section]:
                    if flat_key in portal_data and portal_data[flat_key] is not None:
                        portal_data[section][flat_key] = portal_data[flat_key]

            # Scalanie słowników sekwencyjnych (RP na końcu ma najwyższy priorytet nadpisywania)
            for section in ("location", "specifications", "financials"):
                if portal_data.get(section):
                    for field, value in portal_data[section].items():
                        if value is not None:
                            result[section][field] = value

            # Zbieranie kolekcji
            if isinstance(portal_data.get("image_urls"), list):
                all_image_urls.update(portal_data["image_urls"])
            elif isinstance(portal_data.get("gallery"), list):
                all_image_urls.update(portal_data["gallery"])
            
            amen = portal_data.get("amenities") or {}
            if isinstance(amen, list):
                all_labels.update(amen)
            elif isinstance(amen, dict):
                if isinstance(amen.get("labels"), list):
                    all_labels.update(amen["labels"])
                if isinstance(amen.get("raw_codes"), list):
                    all_codes.update(amen["raw_codes"])

            # Przepisanie źródeł przy użyciu Gateway
            src_info = portal_data.get("sources", {}).get(portal) or {}
            vid = src_info.get("vendor_id") or src_info.get("id") or portal_data.get("id")
            if vid:
                result["sources"][portal] = {"id": str(vid)}
                if src_info.get("url"):
                    result["sources"][portal]["url"] = src_info["url"]

        # Przywrócenie stanu historycznego z bazy dla brakujących danych sieciowych
        if existing_data:
            existing_sources = existing_data.get("sources", {})
            for k, v in existing_sources.items():
                if k not in result["sources"]:
                    result["sources"][k] = v

            # Fallback dla sekcji z bazy danych
            for section in ("location", "specifications", "financials"):
                ex_sec = existing_data.get(section) or {}
                for field, value in ex_sec.items():
                    if result[section].get(field) is None and value is not None:
                        result[section][field] = value

            # Odzyskanie metadanych systemowych trackera
            for field in ("master_id", "suggestions", "issue_reports", "reviewed", "usi_inv_id"):
                if field in existing_data:
                    result[field] = existing_data[field]

            # Odzyskanie lokalnych danych obrazów
            for field in ("image_paths", "images_count", "photos"):
                if field in existing_data and not result.get(field):
                    result[field] = existing_data[field]

            ex_amen = existing_data.get("amenities") or {}
            if ex_amen.get("labels"):
                all_labels.update(ex_amen["labels"])

        # Zapisanie kolekcji
        result["image_urls"] = sorted(list(all_image_urls))
        result["amenities"]["labels"] = list(all_labels)
        result["amenities"]["raw_codes"] = list(all_codes)

        # Wymóg biznesowy: Nadpisanie segmentu przez Meta Ratings (Najwyższy priorytet)
        if meta_ratings and meta_ratings.get("Segment"):
            result["specifications"]["segment"] = meta_ratings["Segment"]

        # Logowanie historii zmian (Audit Trail)
        if existing_data:
            changes = Merger._detect_changes(existing_data, result)
            if changes or event:
                result["audit"]["history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "event": event or "Data Update",
                    "changes": changes
                })
        else:
            result["audit"]["history"] = [{
                "timestamp": result["audit"]["created_at"],
                "event": "Created",
                "changes": []
            }]

        return result
