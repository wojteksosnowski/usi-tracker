import re
import json
import logging
from pathlib import Path
from .merger import Merger
from usi_scrapers import resolve_path, get_mapping
from python_worker.config import SEGMENTS_CONFIG_PATH

logger = logging.getLogger(__name__)

# Build portal mapping config from library
try:
    PORTAL_MAPPING = {
        p: {
            "investment": get_mapping(p, "investment"),
            "developer": get_mapping(p, "developer")
        } for p in ("rp", "oto", "to")
    }
except Exception as e:
    logger.error(f"Failed to load portal mapping from library: {e}")
    PORTAL_MAPPING = {}

# Load segments config (used for UI list and legacy fallbacks)
try:
    with open(SEGMENTS_CONFIG_PATH, "r", encoding="utf-8") as f:
        SEGMENTS_CONFIG = json.load(f)
except Exception as e:
    logger.error(f"Failed to load segments config: {e}")
    SEGMENTS_CONFIG = {"segments": [], "mapping": {}}

def _unwrap(val):
    """Unwraps RP-style {value, type} structures."""
    if isinstance(val, dict) and "value" in val and "type" in val:
        return val["value"]
    return val

def _get_val(data, key, default=None):
    """Delegates to usi-scrapers resolve_path and handles RP {value, type} unwrapping."""
    val = _unwrap(resolve_path(data, key))
    return val if val is not None else default

def _unified_base(inv_slug, dev_slug, name, developer=None):
    return {
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "name": _unwrap(name),
        "developer": _unwrap(developer),
        "website": None,
        "sources": {},
        "location": {"coords": [None, None], "address": None, "city": None, "district": None},
        "specifications": {
            "delivery_date": None,
            "delivery_quarter": None,
            "delivery_year": None,
            "units_count": None,
            "ceiling_height_min": None,
            "ceiling_height_max": None,
            "segment": None
        },
        "financials": {"price_min": None, "price_max": None, "price_avg": None, "price_m2_min": None, "price_m2_max": None, "rent_price_min": None, "rent_price_max": None},
        "amenities": {"labels": [], "raw_codes": []},
        "image_urls": [],
        "images_count": 0,
        "image_paths": [],
    }

class RPAdapter:
    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("raw_details"):
            return cls._from_raw(data["raw_details"], inv_slug, dev_slug)
        if data.get("source") == "rynekpierwotny.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)

    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        cfg = PORTAL_MAPPING.get("rp", {}).get("investment", {})
        u = _unified_base(inv_slug, dev_slug, res.get("name"), developer=res.get("developer_name"))
        lat, lng = res.get("latitude"), res.get("longitude")
        u["sources"]["rp"] = {"id": res.get("id"), "url": res.get("url")}
        u["location"].update({"coords": [lat, lng], "address": res.get("address")})
        u["specifications"].update({
            "delivery_date": res.get("construction_date_upper"),
            "units_count": res.get("properties_count"),
            "ceiling_height_min": _get_val(res, cfg.get("ceiling_height_min")),
            "ceiling_height_max": _get_val(res, cfg.get("ceiling_height_max")),
            "segment": _get_val(res, cfg.get("segment"))
        })
        is_rental = _get_val(res, cfg.get("transaction_type")) == "rent"
        p_min = res.get("ranges_price_min")
        if is_rental:
            u["financials"].update({"rent_price_min": p_min})
        else:
            u["financials"].update({
                "price_min": p_min,
                "price_max": res.get("ranges_price_max"),
                "price_m2_min": res.get("ranges_price_m2_min"),
                "price_m2_max": res.get("ranges_price_m2_max")
            })
        urls = res.get("image_urls", [])
        u["image_urls"] = urls
        u["images_count"] = len(urls)
        return u

    @classmethod
    def _from_raw(cls, raw: dict, inv_slug: str, dev_slug: str) -> dict:
        from usi_scrapers.mapping import transform_to_unified
        m = transform_to_unified("rp", raw)
        m = {k: _unwrap(v) for k, v in m.items()}
        
        u = _unified_base(inv_slug, dev_slug, m.get("name") or raw.get("name"), developer=m.get("developer_name"))
        
        rp_src = {}
        if m.get("id"): rp_src["id"] = str(m.get("id"))
        if m.get("url"): rp_src["url"] = m.get("url")
        if m.get("developer_id"): rp_src["vendor_id"] = str(m.get("developer_id"))
        
        if not rp_src.get("url") and m.get("developer_slug") and raw.get("slug") and m.get("id"):
            rp_src["url"] = f"https://rynekpierwotny.pl/oferty/{m.get('developer_slug')}/{raw.get('slug')}-{m.get('id')}/"
            
        u["sources"]["rp"] = rp_src
        u["website"] = raw.get("website")
        
        u["location"].update({
            "coords": [m.get("latitude"), m.get("longitude")],
            "address": m.get("address"),
            "city": m.get("city"),
            "district": m.get("region")
        })

        is_rental = m.get("transaction_type") == "rent"
        p_min = m.get("price_min")
        if is_rental:
            u["financials"].update({"rent_price_min": p_min})
        else:
            u["financials"].update({
                "price_min": p_min, 
                "price_max": m.get("price_max"), 
                "price_m2_min": m.get("price_m2_min"), 
                "price_m2_max": m.get("price_m2_max")
            })

        u["specifications"].update({
            "delivery_date": m.get("delivery_date"),
            "units_count": m.get("units_count") or raw.get("properties"),
            "ceiling_height_min": m.get("ceiling_height_min"),
            "ceiling_height_max": m.get("ceiling_height_max"),
            "segment": m.get("segment")
        })
        
        amenities = m.get("amenities") or []
        u["amenities"]["raw_codes"] = [int(x) for x in amenities if str(x).isdigit()]
        
        gallery = m.get("gallery") or raw.get("image_urls") or []
        u["image_urls"] = gallery
        u["images_count"] = len(gallery)
        
        return u
class OtodomAdapter:
    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("raw_details"):
            return cls._from_raw(data["raw_details"], inv_slug, dev_slug)
        if data.get("source") == "otodom.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)

    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        cfg = PORTAL_MAPPING.get("oto", {}).get("investment", {})
        u = _unified_base(inv_slug, dev_slug,
                          res.get("title"), developer=res.get("agency_name"))
        lat, lng = res.get("latitude"), res.get("longitude")
        
        oto_src = {"url": res.get("url")}
        if res.get("id"):
            oto_src["id"] = str(res.get("id"))
        u["sources"]["oto"] = oto_src
        
        u["location"]["coords"] = [lat, lng]
        dq, dy = res.get("delivery_quarter"), res.get("delivery_year")
        ad = res.get("raw_details") or res
        
        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": f"{dy}-Q{dq}" if dy and dq else None,
            "segment": _get_val(ad, cfg.get("segment"))
        })
        urls = res.get("image_urls", [])
        u["image_urls"] = urls
        u["images_count"] = len(urls)

        price = res.get("price")
        price_m2 = res.get("price_per_m")
        is_rental = _get_val(ad, cfg.get("transaction_type")) == "rent"
        
        if is_rental:
            u["financials"].update({
                "rent_price_min": float(price) if price else None,
            })
        else:
            u["financials"].update({
                "price_min": float(price) if price else None,
                "price_m2_min": float(price_m2) if price_m2 else None
            })

        u["location"]["address"] = _get_val(ad, cfg.get("street"))
        u["location"]["city"] = _get_val(ad, cfg.get("city"))
        u["location"]["district"] = _get_val(ad, cfg.get("region"))
        
        u["specifications"]["units_count"] = _get_val(ad, cfg.get("units_count"))

        return u

    @classmethod
    def _from_raw(cls, raw: dict, inv_slug: str, dev_slug: str) -> dict:
        from usi_scrapers.mapping import transform_to_unified
        m = transform_to_unified("oto", raw)
        m = {k: _unwrap(v) for k, v in m.items()}
        
        u = _unified_base(inv_slug, dev_slug, m.get("name"), developer=m.get("developer_name"))
        
        oto_src = {"url": m.get("url") or (raw.get("ad") or raw).get("url") or ""}
        if m.get("id"): oto_src["id"] = str(m.get("id"))
        if m.get("developer_id"): oto_src["agency_id"] = str(m.get("developer_id"))
        u["sources"]["oto"] = oto_src
        
        u["location"].update({
            "coords": [m.get("latitude"), m.get("longitude")],
            "address": m.get("address"),
            "city": m.get("city"),
            "district": m.get("region")
        })

        is_rental = m.get("transaction_type") == "rent"
        p_min = m.get("price_min")
        if is_rental:
            u["financials"].update({"rent_price_min": p_min})
        else:
            u["financials"].update({
                "price_min": p_min, 
                "price_m2_min": m.get("price_m2_min")
            })

        u["specifications"].update({
            "units_count": m.get("units_count"),
            "ceiling_height_min": m.get("ceiling_height_min"),
            "ceiling_height_max": m.get("ceiling_height_max"),
            "segment": m.get("segment")
        })
        
        del_date_str = m.get("delivery_date")
        dq = m.get("delivery_fallback_quarter")
        dy = m.get("delivery_fallback_year")
        
        if del_date_str and isinstance(del_date_str, str) and "-Q" in del_date_str:
            parts = del_date_str.split("-Q")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                dy = int(parts[0])
                dq = int(parts[1])
            
        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": del_date_str or (f"{dy}-Q{dq}" if dy and dq else None),
        })
        
        gallery = m.get("images") or (raw.get("ad") or raw).get("image_urls") or []
        u["image_urls"] = gallery
        u["images_count"] = len(gallery)
        
        return u
class TOAdapter:
    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if data.get("raw_details"):
            return cls._from_raw(data["raw_details"], inv_slug, dev_slug)
        if data.get("source") == "tabelaofert.pl":
            return cls._from_result(data, inv_slug, dev_slug)
        return cls._from_raw(data, inv_slug, dev_slug)


    @classmethod
    def _from_result(cls, res: dict, inv_slug: str, dev_slug: str) -> dict:
        cfg = PORTAL_MAPPING.get("to", {}).get("investment", {})
        u = _unified_base(inv_slug, dev_slug,
                          res.get("name"), developer=res.get("developer_name"))
        
        raw_details = res.get("raw_details", {})
        city = _get_val(raw_details, cfg.get("city")) or res.get("city")
        address = _get_val(raw_details, cfg.get("street")) or res.get("address")
        lat, lng = res.get("latitude"), res.get("longitude")

        to_src = {"url": res.get("to_url") or ""}
        
        if res.get("to_id"):
            to_src["id"] = str(res.get("to_id"))
            
        dev_id = _get_val(raw_details, cfg.get("developer_id"))
        if dev_id:
            to_src["developer_id"] = str(dev_id)
            
        u["sources"]["to"] = to_src
        u["location"].update({
            "coords": [lat, lng],
            "address": address,
            "city": city,
            "district": _get_val(raw_details, cfg.get("region"))
        })
        u["specifications"]["delivery_date"] = res.get("construction_date_upper")
        u["specifications"]["units_count"] = res.get("properties_count")
        u["specifications"]["segment"] = _get_val(raw_details, cfg.get("segment"))
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
        from usi_scrapers.mapping import transform_to_unified
        m = transform_to_unified("to", raw)
        m = {k: _unwrap(v) for k, v in m.items()}
        
        u = _unified_base(inv_slug, dev_slug, m.get("name") or raw.get("name"), developer=m.get("developer_name"))
        
        to_src = {"url": m.get("url") or raw.get("to_url") or ""}
        if m.get("id"): to_src["id"] = str(m.get("id"))
        if m.get("developer_id"): to_src["developer_id"] = str(m.get("developer_id"))
        u["sources"]["to"] = to_src
        
        u["location"].update({
            "coords": [m.get("latitude"), m.get("longitude")],
            "address": m.get("address"),
            "city": m.get("city"),
            "district": m.get("region")
        })

        price_min = m.get("price_min")
        price_max = m.get("price_max")
        price_m2_min = m.get("price_m2_min")
        price_m2_max = m.get("price_m2_max")
        
        if isinstance(raw.get("offers"), list) and raw.get("offers") and price_min is None:
            off = raw["offers"][0]
            if isinstance(off, dict):
                price_min = off.get("lowPrice")
                price_max = off.get("highPrice")
                if price_m2_min is None:
                    price_m2_min = off.get("pricePerSqm")

        p_min = m.get("price_min") if price_min is None else price_min
        p_max = m.get("price_max") if price_max is None else price_max
        pm2_min = m.get("price_m2_min") if price_m2_min is None else price_m2_min
        pm2_max = m.get("price_m2_max") if price_m2_max is None else price_m2_max
        
        is_rental = m.get("transaction_type") == "rent"
        if is_rental:
            u["financials"].update({"rent_price_min": p_min})
        else:
            u["financials"].update({
                "price_min": p_min, 
                "price_max": p_max,
                "price_m2_min": pm2_min,
                "price_m2_max": pm2_max
            })
            
        u["amenities"]["labels"] = m.get("amenities") or []
        u["specifications"].update({
            "units_count": m.get("units_count"),
            "ceiling_height_min": m.get("ceiling_height_min"),
            "ceiling_height_max": m.get("ceiling_height_max"),
            "segment": m.get("segment"),
            "delivery_date": m.get("delivery_date")
        })
        
        gallery = raw.get("_raw_gallery_urls") or raw.get("image_urls") or []
        u["image_urls"] = gallery
        u["images_count"] = len(gallery)
        
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
