from datetime import datetime
from python_worker.adapters.base import BaseAdapter
from python_worker.adapters.utils import get_val

class OtodomAdapter(BaseAdapter):
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

        # Extract images
        image_urls = []
        images_raw = get_val(raw_data, "images", [])
        if isinstance(images_raw, list):
            for img in images_raw:
                if not isinstance(img, dict): continue
                # Common Otodom keys: large, medium, small, thumbnail
                # Prefer large, then generic url, then whatever is first
                img_url = img.get("large") or img.get("medium") or img.get("url")
                if not img_url:
                    # Take first available value that looks like a URL
                    for val in img.values():
                        if isinstance(val, str) and val.startswith("http"):
                            img_url = val
                            break
                if img_url:
                    image_urls.append(img_url)

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
            "images_count": get_val(raw_data, "images_count", len(image_urls)),
            "image_paths": get_val(raw_data, "image_paths", []),
            "image_urls": image_urls
        }
