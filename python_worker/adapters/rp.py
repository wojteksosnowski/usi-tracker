import re
from datetime import datetime
from python_worker.adapters.base import BaseAdapter
from python_worker.adapters.utils import get_val

class RPAdapter(BaseAdapter):
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
        
        # Extract images from gallery if present
        image_urls = []
        # Support both _raw_gallery (from download_raw) and gallery (if already in data)
        gallery_data = raw_data.get("_raw_gallery") or raw_data.get("gallery")
        if isinstance(gallery_data, dict):
            gallery_items = gallery_data.get("gallery", [])
            for item in gallery_items:
                img_data = item.get("image", {})
                if not isinstance(img_data, dict): continue
                
                # Find highest g_img_X resolution
                g_keys = [k for k in img_data.keys() if k.startswith("g_img_")]
                if g_keys:
                    # Extract numbers and sort to find max
                    sorted_keys = sorted(g_keys, key=lambda x: int(re.search(r"\d+", x).group() or 0), reverse=True)
                    img_url = img_data.get(sorted_keys[0])
                else:
                    img_url = img_data.get("url") # Fallback to generic url if present
                
                if img_url:
                    image_urls.append(img_url)
        
        # Add main image if not in gallery
        main_img_data = get_val(raw_data, "main_image", {})
        if isinstance(main_img_data, dict):
            m_keys = [k for k in main_img_data.keys() if k.startswith("m_img_")]
            if m_keys:
                sorted_m = sorted(m_keys, key=lambda x: int(re.search(r"\d+", x).group() or 0), reverse=True)
                main_image = main_img_data.get(sorted_m[0])
            else:
                main_image = main_img_data.get("url")
            
            if main_image and main_image not in image_urls:
                image_urls.insert(0, main_image)

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
            "images_count": get_val(raw_data, "images_count", len(image_urls)),
            "image_paths": get_val(raw_data, "image_paths", []),
            "image_urls": image_urls
        }
