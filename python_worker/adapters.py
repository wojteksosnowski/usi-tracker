import json
import logging
import re
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

def get_val(data, key, default=None):
    """
    Helper to unwrap nested Coda/RP JSON values recursively.
    Handles both {"value": ...} and {"type": "obj", "value": ...} patterns.
    """
    if data is None:
        return default
    
    val = data.get(key, default)
    
    # Recursive unwrapping
    while isinstance(val, dict) and "value" in val:
        val = val["value"]
    
    return val

class RPAdapter:
    @staticmethod
    def transform(raw_data: dict, investment_slug: str, developer_slug: str) -> dict:
        # Handle top-level Coda wrapper if present
        if isinstance(raw_data, dict) and "value" in raw_data:
            raw_data = raw_data["value"]

        # Geo point extraction with deep unwrapping
        geo = get_val(raw_data, "geo_point")
        coords = get_val(geo, "coordinates") if isinstance(geo, dict) else None
        
        # RP coordinates are [lng, lat]
        lat_lng = [None, None]
        if isinstance(coords, list) and len(coords) >= 2:
            lat_lng = [coords[1], coords[0]]

        # Extract specifications
        upper_date = get_val(raw_data, "construction_date_upper")
        if not upper_date:
            range_val = get_val(raw_data, "construction_date_range")
            upper_date = get_val(range_val, "upper") if isinstance(range_val, dict) else None
        
        delivery_str, dq, dy = None, None, None
        if upper_date:
            try:
                dt = datetime.fromisoformat(upper_date.split("T")[0])
                dq = (dt.month - 1) // 3 + 1
                dy = dt.year
                delivery_str = f"{dq} kw. {dy}"
            except:
                delivery_str = str(upper_date)

        price_range = get_val(raw_data, "price_m2_range")
        
        return {
            "investment_slug": investment_slug,
            "developer_slug": developer_slug,
            "name": get_val(raw_data, "name"),
            "developer": get_val(get_val(raw_data, "vendor"), "name"),
            "status": "Brak",
            "sources": {
                "rp": {
                    "id": str(get_val(raw_data, "id")),
                    "url": get_val(raw_data, "url"),
                    "last_sync": datetime.now().isoformat()
                }
            },
            "location": {
                "coords": lat_lng,
                "address": get_val(raw_data, "address"),
                "city": None,
                "district": get_val(raw_data, "district")
            },
            "specifications": {
                "units_count": get_val(raw_data, "properties"),
                "delivery_date": delivery_str,
                "delivery_quarter": dq,
                "delivery_year": dy
            },
            "financials": {
                "price_min": get_val(price_range, "lower") if isinstance(price_range, dict) else None,
                "price_max": get_val(price_range, "upper") if isinstance(price_range, dict) else None,
                "price_avg": get_val(price_range, "average") if isinstance(price_range, dict) else None
            },
            "amenities": {
                "labels": [], 
                "raw_codes": get_val(raw_data, "facilities", [])
            },
            "images_count": get_val(raw_data, "images_count", 0),
            "image_paths": get_val(raw_data, "image_paths", [])
        }

class OtodomAdapter:
    @staticmethod
    def transform(raw_data: dict, investment_slug: str, developer_slug: str) -> dict:
        if isinstance(raw_data, dict) and "value" in raw_data:
            raw_data = raw_data["value"]
            
        if isinstance(raw_data, dict) and "ad" in raw_data:
            raw_data = raw_data["ad"]

        # Otodom stores lat/lon in location.coordinates
        loc = get_val(raw_data, "location", {})
        coords = get_val(loc, "coordinates", {})
        lat = get_val(coords, "latitude")
        lng = get_val(coords, "longitude")
        
        # Fallback to mapDetails if coordinates not present
        if not lat or not lng:
            map_details = get_val(loc, "mapDetails", {})
            lat = get_val(map_details, "lat")
            lng = get_val(map_details, "lon")
            
        lat_lng = [lat, lng]

        # Delivery
        delivery = get_val(raw_data, "investmentEstimatedDelivery", {})
        dq = get_val(delivery, "quarter")
        dy = get_val(delivery, "year")
        delivery_str = f"{dq} kw. {dy}" if dq and dy else None

        # Address
        address_obj = get_val(loc, "address", {})
        street = get_val(get_val(address_obj, "street", {}), "name", "")
        city = get_val(get_val(address_obj, "city", {}), "name", "")
        district = get_val(get_val(address_obj, "district", {}), "name", "")
        address = f"{street}, {city}" if street and city else street or city or None

        # Characteristics
        characteristics = get_val(raw_data, "characteristics", [])
        char_dict = {c.get("key"): c.get("value") for c in characteristics if isinstance(c, dict)}
        
        try:
            units_count = int(char_dict.get("number_of_properties")) if char_dict.get("number_of_properties") else None
        except (ValueError, TypeError):
            units_count = None
            
        try:
            price_min = float(char_dict.get("price_per_m_from")) if char_dict.get("price_per_m_from") else None
        except (ValueError, TypeError):
            price_min = None

        return {
            "investment_slug": investment_slug,
            "developer_slug": developer_slug,
            "name": get_val(raw_data, "title"),
            "developer": get_val(get_val(raw_data, "agency"), "name"),
            "status": "Brak",
            "sources": {
                "oto": {
                    "id": str(get_val(raw_data, "id")),
                    "url": get_val(raw_data, "url"),
                    "last_sync": datetime.now().isoformat()
                }
            },
            "location": {
                "coords": lat_lng,
                "address": address,
                "city": city,
                "district": district
            },
            "specifications": {
                "units_count": units_count,
                "delivery_date": delivery_str,
                "delivery_quarter": dq,
                "delivery_year": dy
            },
            "financials": {
                "price_min": price_min,
                "price_max": None,
                "price_avg": None
            },
            "amenities": {
                "labels": get_val(raw_data, "features", []),
                "matched": []
            },
            "images_count": get_val(raw_data, "images_count", 0),
            "image_paths": get_val(raw_data, "image_paths", [])
        }

from .here_maps import enrich_with_here_map, geocode_address

class TOAdapter:
    @staticmethod
    def transform(raw_data: dict, investment_slug: str, developer_slug: str) -> dict:
        # TabelaOfert raw_data is the schema.org Product dict
        brand = raw_data.get("brand", {})
        developer_name = brand.get("name") if isinstance(brand, dict) else None
        
        # Address and Coordinates from first offer
        offers_list = raw_data.get("offers", {}).get("offers", [])
        first_offer = offers_list[0] if isinstance(offers_list, list) and len(offers_list) > 0 else {}
        item_offered = first_offer.get("itemOffered", {})
        address_obj = item_offered.get("address", {})
        
        street = address_obj.get("streetAddress")
        city = address_obj.get("addressLocality")
        district = address_obj.get("addressRegion")

        # Fallback to extracted data from scraper
        ext_loc = raw_data.get("_extracted_location", {})
        if not street: street = ext_loc.get("address") # Scraper address includes city usually
        if not city: city = ext_loc.get("city")
        if not district: district = ext_loc.get("region")

        address = ", ".join(filter(None, [street, city])) or None
        if street and city and city in street: address = street # Avoid "Street, City, City"
        
        geo = item_offered.get("geo", {})
        lat = geo.get("latitude")
        lng = geo.get("longitude")

        if lat is None: lat = ext_loc.get("latitude")
        if lng is None: lng = ext_loc.get("longitude")
        
        # Fallback to geocoding if STILL missing
        if (lat is None or lng is None) and address:
            logger.info(f"Missing coordinates for {investment_slug}, attempting geocoding for: {address}")
            lat, lng = geocode_address(address)
            if lat:
                logger.info(f"Geocoded {address} to {lat}, {lng}")

        lat_lng = [float(lat) if lat else None, float(lng) if lng else None]

        # Delivery Date from additionalProperty
        delivery_str = None
        dq, dy = None, None
        for prop in raw_data.get("additionalProperty", []):
            if prop.get("name") == "Termin oddania":
                delivery_str = prop.get("value")
                # Try to parse "IV kwartał 2024" or similar
                if delivery_str:
                    m = re.search(r"([IVX]+)\s+kwarta.\s+(\d{4})", delivery_str, re.IGNORECASE)
                    if m:
                        roman = m.group(1).upper()
                        roman_map = {"I": 1, "II": 2, "III": 3, "IV": 4}
                        dq = roman_map.get(roman)
                        dy = int(m.group(2))
                break

        # Price
        agg_offers = raw_data.get("offers", {})
        try:
            price_min = float(agg_offers.get("lowPrice") or 0) or None
            price_max = float(agg_offers.get("highPrice") or 0) or None
        except:
            price_min, price_max = None, None

        return {
            "investment_slug": investment_slug,
            "developer_slug": developer_slug,
            "name": raw_data.get("name"),
            "developer": developer_name,
            "status": "Brak",
            "sources": {
                "to": {
                    "id": None, # TO ID usually in URL
                    "url": raw_data.get("url"),
                    "last_sync": datetime.now().isoformat()
                }
            },
            "location": {
                "coords": lat_lng,
                "address": address,
                "city": city,
                "district": district
            },
            "specifications": {
                "units_count": agg_offers.get("offerCount"),
                "delivery_date": delivery_str,
                "delivery_quarter": dq,
                "delivery_year": dy
            },
            "financials": {
                "price_min": price_min,
                "price_max": price_max,
                "price_avg": None
            },
            "amenities": {
                "labels": [],
                "raw_codes": [p.get("name") for p in raw_data.get("additionalProperty", [])]
            },
            "images_count": raw_data.get("images_count", 0),
            "image_paths": raw_data.get("image_paths", [])
        }

class Merger:
    @staticmethod
    def _detect_changes(old: dict, new: dict) -> list:
        """Compares significant fields and returns a list of change objects."""
        changes = []
        
        # Mapping of (flat_key, path_in_new)
        # We compare simplified structures for convenience
        fields = [
            ("financials.price_avg", ["financials", "price_avg"]),
            ("financials.price_min", ["financials", "price_min"]),
            ("financials.price_max", ["financials", "price_max"]),
            ("specifications.units_count", ["specifications", "units_count"]),
            ("specifications.delivery_date", ["specifications", "delivery_date"]),
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
            "name": base.get("name"),
            "developer": base.get("developer"),
            "status": (meta_ratings or {}).get("status") or (existing_data or {}).get("status") or "Brak",
            "sources": {},
            "location": base.get("location", {}).copy(),
            "specifications": base.get("specifications", {}).copy(),
            "financials": base.get("financials", {}).copy(),
            "amenities": base.get("amenities", {}).copy(),
            "ratings": meta_ratings or (existing_data or {}).get("ratings") or {},
            "images_count": base.get("images_count", 0),
            "image_paths": base.get("image_paths", []),
            "audit": {
                "created_at": existing_audit.get("created_at") or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "history": existing_audit.get("history", [])
            }
        }

        # Preserve existing source info (URLs, IDs) if new data is missing them
        existing_sources = (existing_data or {}).get("sources", {})
        
        if rp_data:
            result["sources"]["rp"] = rp_data["sources"].get("rp")
            # Restore lost URL if missing in new RP data
            if not result["sources"]["rp"].get("url") and existing_sources.get("rp", {}).get("url"):
                result["sources"]["rp"]["url"] = existing_sources["rp"]["url"]
        elif "rp" in existing_sources:
            result["sources"]["rp"] = existing_sources["rp"]

        if oto_data:
            result["sources"]["oto"] = oto_data["sources"].get("oto")
            if not result["sources"]["oto"].get("url") and existing_sources.get("oto", {}).get("url"):
                result["sources"]["oto"]["url"] = existing_sources["oto"]["url"]
        elif "oto" in existing_sources:
            result["sources"]["oto"] = existing_sources["oto"]

        if to_data:
            result["sources"]["to"] = to_data["sources"].get("to")
            if not result["sources"]["to"].get("url") and existing_sources.get("to", {}).get("url"):
                result["sources"]["to"]["url"] = existing_sources["to"]["url"]
        elif "to" in existing_sources:
            result["sources"]["to"] = existing_sources["to"]

        # Data enrichment from other sources
        for other in [rp_data, oto_data, to_data]:
            if not other: continue
            
            # 1. Location Merge
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

            # 2. Specifications Merge
            other_spec = other.get("specifications", {})
            curr_spec = result["specifications"]
            if not curr_spec.get("delivery_date") and other_spec.get("delivery_date"):
                curr_spec["delivery_date"] = other_spec["delivery_date"]
                curr_spec["delivery_quarter"] = other_spec.get("delivery_quarter")
                curr_spec["delivery_year"] = other_spec.get("delivery_year")
            if not curr_spec.get("units_count") and other_spec.get("units_count"):
                curr_spec["units_count"] = other_spec["units_count"]

            # 3. Financials Merge
            other_fin = other.get("financials", {})
            curr_fin = result["financials"]
            if not curr_fin.get("price_min") and other_fin.get("price_min"):
                curr_fin["price_min"] = other_fin["price_min"]
            if not curr_fin.get("price_max") and other_fin.get("price_max"):
                curr_fin["price_max"] = other_fin["price_max"]
            if not curr_fin.get("price_avg") and other_fin.get("price_avg"):
                curr_fin["price_avg"] = other_fin["price_avg"]

            # 4. Amenities Combine
            all_labels = set(result["amenities"].get("labels", []))
            other_amen = other.get("amenities", {})
            if isinstance(other_amen.get("labels"), list):
                all_labels.update(other_amen["labels"])
            result["amenities"]["labels"] = list(all_labels)
            
            # Combine raw_codes for RP
            all_codes = set(result["amenities"].get("raw_codes", []))
            if isinstance(other_amen.get("raw_codes"), list):
                all_codes.update(other_amen["raw_codes"])
            result["amenities"]["raw_codes"] = list(all_codes)

            # 5. Images Merge (prefer source with more images)
            if other.get("images_count", 0) > result.get("images_count", 0):
                result["images_count"] = other["images_count"]
                result["image_paths"] = other.get("image_paths", [])

        # Detect changes and update history
        if existing_data:
            changes = Merger._detect_changes(existing_data, result)
            if changes or event:
                result["audit"]["history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "event": event or "Data Update",
                    "changes": changes
                })
        else:
            # First time creation
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
