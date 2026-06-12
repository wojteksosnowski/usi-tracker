import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Merger:
    @staticmethod
    def _detect_changes(old: dict, new: dict) -> list:
        """Compares significant fields and returns a list of change objects."""
        changes = []
        
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

        def get_nested(d, path):
            for k in path:
                if not isinstance(d, dict): return None
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
    def merge(rp_data: dict = None, oto_data: dict = None, to_data: dict = None, meta_ratings: dict = None, existing_data: dict = None, event: str = None) -> dict:
        """Merges data from multiple sources into a single USI Unified JSON."""
        # Start with a base, prefer RP > Otodom > TO
        base = rp_data or oto_data or to_data or existing_data or {}
        if not base: return {}

        existing_audit = (existing_data or {}).get("audit", {})
        
        result = {
            "investment_slug": base.get("investment_slug"),
            "developer_slug": base.get("developer_slug"),
            "usi_dev_id": base.get("usi_dev_id") or (existing_data or {}).get("usi_dev_id"),
            "name": base.get("name"),
            "developer": base.get("developer"),
            "website": base.get("website") or (existing_data or {}).get("website"),
            "status": (meta_ratings or {}).get("status") or (existing_data or {}).get("status") or "Brak",
            "sources": {},
            "location": base.get("location", {}).copy() if base.get("location") else {},
            "specifications": base.get("specifications", {}).copy() if base.get("specifications") else {},
            "financials": base.get("financials", {}).copy() if base.get("financials") else {},
            "amenities": base.get("amenities", {}).copy() if base.get("amenities") else {},

            "ratings": meta_ratings or (existing_data or {}).get("ratings") or {},
            "images_count": base.get("images_count", 0),
            "image_paths": base.get("image_paths", []),
            "image_urls": base.get("image_urls", []),
            "audit": {
                "created_at": existing_audit.get("created_at") or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "history": existing_audit.get("history", [])
            }
        }

        existing_sources = (existing_data or {}).get("sources", {})
        all_image_urls = set(result.get("image_urls", []))

        from python_worker.services.scraper_gateway import ScraperGateway
        
        for portal, portal_data in [("rp", rp_data), ("oto", oto_data), ("to", to_data)]:
            if portal_data:
                src_info = portal_data["sources"].get(portal) or {}
                vid = src_info.get("vendor_id") or src_info.get("id") or src_info.get("agency_id")
                
                # Próba pobrania z istniejących źródeł jeśli brakuje
                if not vid and portal in existing_sources:
                    ex_src = existing_sources[portal]
                    vid = ex_src.get("vendor_id") or ex_src.get("id") or ex_src.get("agency_id")

                url = src_info.get("url") or existing_sources.get(portal, {}).get("url")

                # Budowanie struktury przez Gateway
                if vid:
                    result["sources"][portal] = ScraperGateway.generate_portal_mapping(portal, str(vid))
                else:
                    result["sources"][portal] = src_info.copy()

                if url:
                    result["sources"][portal]["url"] = url
                
                if "image_urls" in portal_data:
                    all_image_urls.update(portal_data["image_urls"])
            elif portal in existing_sources:
                result["sources"][portal] = existing_sources[portal]

        result["image_urls"] = sorted(list(all_image_urls))

        for other in [rp_data, oto_data, to_data]:
            if not other: continue
            
            other_loc = other.get("location", {})
            curr_loc = result["location"]
            if not curr_loc.get("coords") or curr_loc["coords"][0] is None:
                if other_loc.get("coords") and other_loc["coords"][0] is not None:
                    curr_loc["coords"] = other_loc["coords"]
            if not curr_loc.get("address") and other_loc.get("address"):
                curr_loc["address"] = other_loc["address"]
            if not curr_loc.get("city") and other_loc.get("city"):
                curr_loc["city"] = other_loc["city"]
            if not curr_loc.get("district") and other_loc.get("district"):
                curr_loc["district"] = other_loc["district"]

            other_spec = other.get("specifications", {})
            curr_spec = result["specifications"]
            if not curr_spec.get("delivery_date") and other_spec.get("delivery_date"):
                curr_spec["delivery_date"] = other_spec["delivery_date"]
                curr_spec["delivery_quarter"] = other_spec.get("delivery_quarter")
                curr_spec["delivery_year"] = other_spec.get("delivery_year")
            if not curr_spec.get("units_count") and other_spec.get("units_count"):
                curr_spec["units_count"] = other_spec["units_count"]
            if not curr_spec.get("ceiling_height_min") and other_spec.get("ceiling_height_min"):
                curr_spec["ceiling_height_min"] = other_spec["ceiling_height_min"]
            if not curr_spec.get("ceiling_height_max") and other_spec.get("ceiling_height_max"):
                curr_spec["ceiling_height_max"] = other_spec["ceiling_height_max"]
            if not curr_spec.get("segment") and other_spec.get("segment"):
                curr_spec["segment"] = other_spec["segment"]

            # Priority 1: Meta ratings 'Segment' takes precedence
            if meta_ratings and meta_ratings.get("Segment"):
                curr_spec["segment"] = meta_ratings["Segment"]
            
            # Priority 2: Existing data 'segment' takes precedence over portal data
            elif (existing_data or {}).get("specifications", {}).get("segment"):
                curr_spec["segment"] = existing_data["specifications"]["segment"]

            other_fin = other.get("financials", {})
            curr_fin = result["financials"]
            for fld in ("price_min", "price_max", "price_avg", "price_m2_min", "price_m2_max", "rent_price_min", "rent_price_max"):
                if not curr_fin.get(fld) and other_fin.get(fld):
                    curr_fin[fld] = other_fin[fld]
            
            # Fallback for price_avg if it is still missing but we have price_min
            if not curr_fin.get("price_avg") and curr_fin.get("price_min"):
                curr_fin["price_avg"] = curr_fin["price_min"]

            all_labels = set(result["amenities"].get("labels", []))
            other_amen = other.get("amenities", {})
            if isinstance(other_amen.get("labels"), list):
                all_labels.update(other_amen["labels"])
            result["amenities"]["labels"] = list(all_labels)
            
            all_codes = set(result["amenities"].get("raw_codes", []))
            if isinstance(other_amen.get("raw_codes"), list):
                all_codes.update(other_amen["raw_codes"])
            result["amenities"]["raw_codes"] = list(all_codes)

            other_paths = other.get("image_paths", [])
            # Interesują nas wyłącznie ścieżki lokalne (nie zaczynające się od http)
            local_paths = [p for p in other_paths if not str(p).startswith(("http://", "https://"))]
            
            if local_paths and len(local_paths) > len(result.get("image_paths", [])):
                result["image_paths"] = local_paths
                result["images_count"] = len(local_paths)

        # Priority override: Meta ratings 'Segment' takes precedence
        if meta_ratings and meta_ratings.get("Segment"):
            result["specifications"]["segment"] = meta_ratings["Segment"]

        # Preserve existing_data values for fields that came back null from portals
        if existing_data:
            ex_loc = existing_data.get("location") or {}
            if not result["location"].get("address") and ex_loc.get("address"):
                result["location"]["address"] = ex_loc["address"]
            if not result["location"].get("city") and ex_loc.get("city"):
                result["location"]["city"] = ex_loc["city"]
            if not result["location"].get("district") and ex_loc.get("district"):
                result["location"]["district"] = ex_loc["district"]
            if result["location"].get("coords", [None])[0] is None and \
                    ex_loc.get("coords", [None])[0] is not None:
                result["location"]["coords"] = ex_loc["coords"]

            ex_spec = existing_data.get("specifications") or {}
            if not result["specifications"].get("units_count") and ex_spec.get("units_count"):
                result["specifications"]["units_count"] = ex_spec["units_count"]
            if not result["specifications"].get("ceiling_height") and ex_spec.get("ceiling_height"):
                result["specifications"]["ceiling_height"] = ex_spec["ceiling_height"]
            if not result["specifications"].get("ceiling_height_min") and ex_spec.get("ceiling_height_min"):
                result["specifications"]["ceiling_height_min"] = ex_spec["ceiling_height_min"]
            if not result["specifications"].get("ceiling_height_max") and ex_spec.get("ceiling_height_max"):
                result["specifications"]["ceiling_height_max"] = ex_spec["ceiling_height_max"]
            if not result["specifications"].get("delivery_date") and ex_spec.get("delivery_date"):
                result["specifications"]["delivery_date"] = ex_spec["delivery_date"]
                result["specifications"]["delivery_quarter"] = ex_spec.get("delivery_quarter")
                result["specifications"]["delivery_year"] = ex_spec.get("delivery_year")

            ex_fin = existing_data.get("financials") or {}
            for fld in ("price_min", "price_max", "price_avg", "price_m2_min", "price_m2_max", "rent_price_min", "rent_price_max"):
                if not result["financials"].get(fld) and ex_fin.get(fld):
                    result["financials"][fld] = ex_fin[fld]

            ex_amen = existing_data.get("amenities") or {}
            ex_labels = ex_amen.get("labels") or []
            if ex_labels and not result["amenities"].get("labels"):
                result["amenities"]["labels"] = list(ex_labels)
            elif ex_labels:
                merged_labels = set(result["amenities"].get("labels", [])) | set(ex_labels)
                result["amenities"]["labels"] = list(merged_labels)

            ex_ids = existing_data.get("usi_inv_id")
            if ex_ids and not result.get("usi_inv_id"):
                result["usi_inv_id"] = ex_ids
            ex_dev_id = existing_data.get("usi_dev_id")
            if ex_dev_id and not result.get("usi_dev_id"):
                result["usi_dev_id"] = ex_dev_id
            if not result.get("developer") and existing_data.get("developer"):
                result["developer"] = existing_data["developer"]
            if not result.get("developer_slug") and existing_data.get("developer_slug"):
                result["developer_slug"] = existing_data["developer_slug"]
                
            for field in ("master_id", "suggestions", "issue_reports", "reviewed"):
                if field in existing_data:
                    result[field] = existing_data[field]

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
            if event:
                result["audit"]["history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "event": event,
                    "changes": []
                })

        return result


        return result
