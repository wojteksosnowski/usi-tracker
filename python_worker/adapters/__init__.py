import re
import json
import logging
from pathlib import Path
from .merger import Merger
from usi_scrapers import resolve_path

logger = logging.getLogger(__name__)

# Load portal mapping config
try:
    _MAPPING_PATH = Path(__file__).parent.parent / "schemas" / "portal_data_mapping.json"
    with open(_MAPPING_PATH, "r") as f:
        PORTAL_MAPPING = json.load(f)["portals"]
except Exception as e:
    logger.error(f"Failed to load portal_data_mapping.json: {e}")
    PORTAL_MAPPING = {}

def _unwrap_rp(val):
    if isinstance(val, dict) and "value" in val and "type" in val:
        return _unwrap_rp(val["value"])
    return val

def _get_val(data, key, default=None):
    """Legacy helper (unwraps RP API wrapper dicts)."""
    # For RP, we often need to manually traverse if the path is simple
    if isinstance(data, dict) and key in data:
        return _unwrap_rp(data[key])
    val = resolve_path(data, key)
    return _unwrap_rp(val) if val is not None else default


def _unified_base(inv_slug, dev_slug, name, developer=None):
    return {
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "name": name,
        "developer": developer,
        "website": None,
        "sources": {},
        "location": {"coords": [None, None], "address": None, "city": None, "district": None},
        "specifications": {"delivery_date": None, "delivery_quarter": None, "delivery_year": None, "units_count": None, "ceiling_height_min": None, "ceiling_height_max": None},
        "financials": {"price_min": None, "price_max": None, "price_avg": None, "price_m2_min": None, "price_m2_max": None},
        "amenities": {"labels": [], "raw_codes": []},
        "image_urls": [],
        "images_count": 0,
        "image_paths": [],
    }


class RPAdapter:
    """
    Transforms RynekPierwotny data to the unified Merger schema.
    Accepts either a full scraper result (source="rynekpierwotny.pl")
    or a raw RP API response dict (from raw_rp_*.json on disk).
    """

    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("source") == "rynekpierwotny.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)

    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        u = _unified_base(inv_slug, dev_slug, res.get("name"))
        lat, lng = res.get("latitude"), res.get("longitude")
        u["sources"]["rp"] = {"id": res.get("id"), "url": res.get("url")}
        u["location"].update({"coords": [lat, lng], "address": res.get("address")})
        u["specifications"].update({
            "delivery_date": res.get("construction_date_upper"),
            "units_count": res.get("properties_count"),
        })
        urls = res.get("image_urls", [])
        u["image_urls"] = urls
        u["images_count"] = len(urls)
        return u

    @classmethod
    def _from_raw(cls, raw: dict, inv_slug: str, dev_slug: str) -> dict:
        cfg = PORTAL_MAPPING.get("rp", {}).get("investment", {})
        
        def get(d, p):
            val = resolve_path(d, p)
            if val is None and isinstance(p, str):
                # Fallback for dot-paths that might be hidden behind RP wrappers
                # resolve_path 0.6.0 doesn't automatically descend into 'value'
                current = d
                for part in p.split('.'):
                    if isinstance(current, dict):
                        if part in current:
                            current = current[part]
                        elif "value" in current and isinstance(current["value"], dict) and part in current["value"]:
                            current = current["value"][part]
                        else:
                            return None
                    else:
                        return None
                val = current
            return _unwrap_rp(val)
        
        name = get(raw, cfg.get("name")) or _get_val(raw, "name")
        u = _unified_base(inv_slug, dev_slug, name)

        geo = _get_val(raw, "geo_point")
        coords = _get_val(geo, "coordinates") if isinstance(geo, dict) else None
        lat = coords[1] if coords and len(coords) > 1 else None
        lng = coords[0] if coords and len(coords) > 0 else None

        construction = _get_val(raw, "construction_date_range")
        delivery = _get_val(construction, "upper") if isinstance(construction, dict) else None

        gallery_urls = []
        gallery_data = raw.get("_raw_gallery", {})
        _gallery_prio = ["g_img_2000", "g_img_1500", "g_img_500"]
        for item in (gallery_data.get("gallery") or []):
            img_obj = item.get("image", {})
            img = next((img_obj[k] for k in _gallery_prio if img_obj.get(k)), None)
            if img:
                gallery_urls.append(img)
        main = raw.get("main_image")
        if isinstance(main, dict):
            _main_prio = ["m_img_1500", "m_img_500"]
            main = next((main[k] for k in _main_prio if main.get(k)), None)
        if main:
            gallery_urls.insert(0, main)
        if not gallery_urls:
            gallery_urls = raw.get("image_urls", [])

        amenity_codes = []
        for feat in (_get_val(raw, "features") or raw.get("features") or []):
            if isinstance(feat, dict):
                code = feat.get("id") or feat.get("code")
                if code is not None:
                    amenity_codes.append(int(code))

        offer_id = str(get(raw, cfg.get("id")) or raw.get("id", ""))
        url = raw.get("url")
        website = raw.get("website")
        
        vendor_name = get(raw, cfg.get("developer_name"))
        if vendor_name:
            u["developer"] = vendor_name
        
        if not url:
            vendor_slug = get(raw, cfg.get("developer_slug")) or _get_val(raw.get("vendor"), "slug")
            offer_slug = raw.get("slug", "")
            if vendor_slug and offer_slug:
                url = f"https://rynekpierwotny.pl/oferty/{vendor_slug}/{offer_slug}-{offer_id}/"

        rp_src = {"id": offer_id, "url": url}
        vendor_id = get(raw, cfg.get("developer_id"))
        if vendor_id:
            rp_src["vendor_id"] = str(vendor_id)
            
        u["sources"]["rp"] = rp_src
        u["website"] = website
        address = _get_val(raw, "address") or raw.get("address")
        city = district = None
        if address:
            parts = [p.strip() for p in address.split(",")]
            if len(parts) >= 1:
                city = parts[0]
            if len(parts) >= 3: # City, District, Street
                district = parts[1]

        u["location"].update({
            "coords": [lat, lng],
            "address": address,
            "city": city,
            "district": district,
        })

        # Extract height and prices from config paths
        h_min = h_max = None
        try:
            h_min_cm = get(raw, cfg.get("ceiling_height_min"))
            h_max_cm = get(raw, cfg.get("ceiling_height_max"))
            if h_min_cm: h_min = round(float(h_min_cm) / 100, 2)
            if h_max_cm: h_max = round(float(h_max_cm) / 100, 2)
        except (ValueError, TypeError):
            pass
            
        try:
            p_min = get(raw, cfg.get("price_min"))
            p_max = get(raw, cfg.get("price_max"))
            # price_m2 paths not in fundamental config yet, keep for now if they are simple
            pm2_min = raw.get("stats", {}).get("ranges_price_m2_min") # Fallback to manual for extra fields
            pm2_max = raw.get("stats", {}).get("ranges_price_m2_max")
            
            u["financials"].update({
                "price_min": float(p_min) if p_min is not None else None,
                "price_max": float(p_max) if p_max is not None else None,
            })
            # Manual fallback for legacy extraction of extras
            if isinstance(_get_val(raw, "stats"), dict):
                s = _get_val(raw, "stats")
                u["financials"]["price_m2_min"] = float(s.get("ranges_price_m2_min")) if s.get("ranges_price_m2_min") else None
                u["financials"]["price_m2_max"] = float(s.get("ranges_price_m2_max")) if s.get("ranges_price_m2_max") else None
        except (ValueError, TypeError):
            pass

        u["specifications"].update({
            "delivery_date": delivery,
            "units_count": get(raw, cfg.get("units_count")) or raw.get("properties"),
            "ceiling_height_min": h_min,
            "ceiling_height_max": h_max,
        })
        u["amenities"]["raw_codes"] = amenity_codes
        u["image_urls"] = gallery_urls
        u["images_count"] = len(gallery_urls)
        return u


class OtodomAdapter:
    """
    Transforms Otodom data to the unified Merger schema.
    Accepts either a full scraper result (source="otodom.pl")
    or raw Otodom ad_data dict (from raw_oto_*.json on disk).
    """

    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("source") == "otodom.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)

    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        u = _unified_base(inv_slug, dev_slug,
                          res.get("title"), developer=res.get("agency_name"))
        lat, lng = res.get("latitude"), res.get("longitude")
        u["sources"]["oto"] = {"url": res.get("url")}
        u["location"]["coords"] = [lat, lng]
        dq, dy = res.get("delivery_quarter"), res.get("delivery_year")
        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": f"{dy}-Q{dq}" if dy and dq else None,
        })
        urls = res.get("image_urls", [])
        u["image_urls"] = urls
        u["images_count"] = len(urls)

        # Supplement from raw_details if available (scrape_otodom doesn't pre-extract all fields)
        ad = res.get("raw_details") or {}
        addr_obj = (ad.get("location") or {}).get("address") or {}
        if isinstance(addr_obj, dict):
            street = (addr_obj.get("street") or {}).get("name") or ""
            street_num = (addr_obj.get("street") or {}).get("number") or ""
            street = re.sub(r'^ul\.\s*', '', street, flags=re.IGNORECASE).strip()
            street_full = f"ul. {street} {street_num}".strip() if street else None
            u["location"]["address"] = street_full or None
            u["location"]["city"] = (addr_obj.get("city") or {}).get("name")
            u["location"]["district"] = (addr_obj.get("district") or {}).get("name")
        for item in (ad.get("topInformation") or []):
            if item.get("label") == "number_of_units_in_project":
                vals = item.get("values", [])
                if vals:
                    try:
                        u["specifications"]["units_count"] = int(vals[0])
                    except (ValueError, TypeError):
                        pass
                break

        return u

    @classmethod
    def _from_raw(cls, raw: dict, inv_slug: str, dev_slug: str) -> dict:
        # raw is the ad_data dict saved by scraper_otodom
        ad = raw.get("ad") or raw  # old format had {"ad": {...}}
        cfg = PORTAL_MAPPING.get("oto", {}).get("investment", {})
        get = resolve_path

        images = [img.get("large") for img in (ad.get("images") or []) if img.get("large")]
        if not images:
            images = ad.get("image_urls", [])

        loc = (ad.get("location") or {}).get("coordinates") or {}
        lat = loc.get("latitude")
        lng = loc.get("longitude")

        agency_name = get(ad, cfg.get("developer_name")) or (ad.get("owner") or {}).get("name")
        url = ad.get("url")

        dq = dy = None
        units_count = None
        h_min = h_max = None
        
        # Try config-based units count first
        units_val = get(ad, cfg.get("units_count"))
        if units_val:
            try: units_count = int(units_val)
            except (ValueError, TypeError): pass
            
        for item in (ad.get("topInformation") or []):
            lbl = item.get("label")
            vals = item.get("values", [])
            if not vals:
                continue

            if lbl == "project_finish_date":
                try:
                    parts = vals[0].split("-")
                    dy = int(parts[0])
                    dq = (int(parts[1]) - 1) // 3 + 1
                except Exception:
                    pass
            elif lbl == "number_of_units_in_project" and units_count is None:
                try: units_count = int(vals[0])
                except (ValueError, TypeError): pass
        
        try:
            h_min_cm = get(ad, cfg.get("ceiling_height_min"))
            h_max_cm = get(ad, cfg.get("ceiling_height_max"))
            if h_min_cm: h_min = round(float(h_min_cm) / 100, 2)
            if h_max_cm: h_max = round(float(h_max_cm) / 100, 2)
        except (ValueError, TypeError):
            pass

        if dq is None:
            old_del = ad.get("investmentEstimatedDelivery") or {}
            dq = old_del.get("quarter")
            dy = old_del.get("year")

        title = get(ad, cfg.get("name")) or ad.get("title")
        u = _unified_base(inv_slug, dev_slug, title, developer=agency_name)
        
        oto_src = {"url": url or ""}
        oto_id = get(ad, cfg.get("id"))
        if oto_id:
            oto_src["id"] = str(oto_id)
        
        agency_id = get(ad, cfg.get("developer_id")) or (ad.get("owner") or {}).get("id")
        if agency_id:
            oto_src["agency_id"] = str(agency_id)
            
        u["sources"]["oto"] = oto_src
        u["location"]["coords"] = [lat, lng]
        addr_obj = (ad.get("location") or {}).get("address") or {}
        if isinstance(addr_obj, dict) and addr_obj:
            street = (addr_obj.get("street") or {}).get("name") or ""
            street_num = (addr_obj.get("street") or {}).get("number") or ""
            street = re.sub(r'^ul\.\s*', '', street, flags=re.IGNORECASE).strip()
            street_full = f"ul. {street} {street_num}".strip() if street else None
            u["location"]["address"] = street_full or None
            u["location"]["city"] = (addr_obj.get("city") or {}).get("name")
            u["location"]["district"] = (addr_obj.get("district") or {}).get("name")

        price_min = get(ad, cfg.get("price_min"))
        u["financials"].update({
            "price_min": float(price_min) if price_min else None
        })

        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": f"{dy}-Q{dq}" if dy and dq else None,
            "units_count": units_count,
            "ceiling_height_min": h_min,
            "ceiling_height_max": h_max,
        })
        u["image_urls"] = images
        u["images_count"] = len(images)
        return u


class TOAdapter:
    """
    Transforms TabelaOfert data to the unified Merger schema.
    Accepts either a full scraper result (source="tabelaofert.pl")
    or raw TO product dict (from raw_to_*.json on disk).
    """

    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("source") == "tabelaofert.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)

    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        u = _unified_base(inv_slug, dev_slug,
                          res.get("name"), developer=res.get("developer_name"))
        
        city = res.get("city")
        address = res.get("address")
        lat, lng = res.get("latitude"), res.get("longitude")

        # Fallback for location from description
        desc = res.get("raw_details", {}).get("description") or ""
        if (not city or not address) and desc:
            # Matches: ✔️ Łódź, Śródmieście, ul. Telefoniczna 21 ✔️
            # and variants like: Łódź, Śródmieście, ul. Telefoniczna 21
            m = re.search(r'(?:✔️|✅|📍)?\s*([^,]+),\s*([^,]+),\s*(ul\.[^✔️✅📍\n]+)', desc)
            if m:
                if not city: city = m.group(1).strip()
                if not address: address = m.group(3).strip()

        u["sources"]["to"] = {"url": res.get("to_url") or ""}
        u["location"].update({
            "coords": [lat, lng],
            "address": address,
            "city": city,
        })
        u["specifications"]["delivery_date"] = res.get("construction_date_upper")
        u["specifications"]["units_count"] = res.get("properties_count")
        u["financials"].update({
            "price_min": res.get("price_min"),
            "price_max": res.get("price_max"),
        })
        amenity_labels = [a["name"] for a in (res.get("amenities") or []) if isinstance(a, dict) and a.get("name")]
        u["amenities"]["labels"] = amenity_labels
        urls = res.get("image_urls", [])
        u["image_urls"] = urls
        u["images_count"] = len(urls)
        return u

    @classmethod
    def _from_raw(cls, raw: dict, inv_slug: str, dev_slug: str) -> dict:
        cfg = PORTAL_MAPPING.get("to", {}).get("investment", {})
        get = resolve_path

        developer_name = get(raw, cfg.get("developer_name"))
        price_min = get(raw, cfg.get("price_min"))
        price_max = get(raw, cfg.get("price_max"))
        
        # Fallback for multi-offer lists if JsonPathExtractor didn't handle it
        # (though it should if the path matches)
        if isinstance(raw.get("offers"), list) and raw.get("offers") and price_min is None:
            off = raw["offers"][0]
            if isinstance(off, dict):
                price_min = off.get("lowPrice")
                price_max = off.get("highPrice")

        try:
            price_min = float(price_min or 0) or None
            price_max = float(price_max or 0) or None
        except (TypeError, ValueError):
            price_min = price_max = None

        urls = raw.get("_raw_gallery_urls") or raw.get("image_urls", [])

        ext_loc = raw.get("_extracted_location") or {}
        lat = ext_loc.get("latitude")
        lng = ext_loc.get("longitude")
        city = ext_loc.get("city")
        address = ext_loc.get("address")

        desc = raw.get("description") or ""
        if (not city or not address) and desc:
            m = re.search(r'(?:✔️|✅|📍)?\s*([^,]+),\s*([^,]+),\s*(ul\.[^✔️✅📍\n]+)', desc)
            if m:
                if not city: city = m.group(1).strip()
                if not address: address = m.group(3).strip()

        amenity_labels = []
        for prop in (raw.get("additionalProperty") or []):
            if isinstance(prop, dict) and prop.get("name"):
                amenity_labels.append(prop["name"])

        h_min = h_max = None
        height_val = get(raw, cfg.get("ceiling_height_min"))
        if height_val and isinstance(height_val, str):
            # Extract number from string like "270 cm"
            h_match = re.search(r'(\d+)', height_val)
            if h_match:
                try: h_min = h_max = round(float(h_match.group(1)) / 100, 2)
                except: pass

        title = get(raw, cfg.get("name")) or raw.get("name")
        u = _unified_base(inv_slug, dev_slug, title, developer=developer_name)
        
        to_src = {"url": raw.get("url") or raw.get("to_url") or ""}
        to_id = get(raw, cfg.get("id"))
        if to_id:
            to_src["id"] = str(to_id)
            
        dev_id = get(raw, cfg.get("developer_id"))
        if dev_id:
            to_src["developer_id"] = str(dev_id)
            
        u["sources"]["to"] = to_src
        u["location"].update({"coords": [lat, lng], "address": address, "city": city})
        u["financials"].update({"price_min": price_min, "price_max": price_max})
        u["amenities"]["labels"] = amenity_labels
        u["specifications"].update({
            "units_count": get(raw, cfg.get("units_count")),
            "ceiling_height_min": h_min,
            "ceiling_height_max": h_max,
        })
        u["image_urls"] = urls
        u["images_count"] = len(urls)
        return u


class AdapterFactory:
    _adapters = {
        "rp": RPAdapter,
        "otodom": OtodomAdapter,
        "oto": OtodomAdapter,
        "tabelaofert": TOAdapter,
        "to": TOAdapter,
    }

    @classmethod
    def get_adapter(cls, portal_name):
        portal_name = portal_name.lower()
        adapter_cls = cls._adapters.get(portal_name)
        if not adapter_cls:
            raise ValueError(f"No adapter registered for portal: {portal_name}")
        return adapter_cls


__all__ = ["AdapterFactory", "Merger", "RPAdapter", "OtodomAdapter", "TOAdapter"]
