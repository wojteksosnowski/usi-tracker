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

def _get_val(data, key, default=None):
    """Delegates to usi-scrapers resolve_path (which handles RP {value, type} unwrapping since v0.7.0)."""
    val = resolve_path(data, key)
    return val if val is not None else default

def _unified_base(inv_slug, dev_slug, name, developer=None):
    return {
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "name": name,
        "developer": developer,
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
        if "raw_details" in data:
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
        cfg = PORTAL_MAPPING.get("rp", {}).get("investment", {})
        
        name = _get_val(raw, cfg.get("name")) or _get_val(raw, "name")
        u = _unified_base(inv_slug, dev_slug, name)

        lat = _get_val(raw, cfg.get("latitude"))
        lng = _get_val(raw, cfg.get("longitude"))
        delivery = _get_val(raw, cfg.get("construction_date_upper"))

        gallery_urls = _get_val(raw, cfg.get("gallery")) or raw.get("image_urls", [])
        
        amenity_codes = []
        for code in _get_val(raw, cfg.get("amenities")) or []:
            try:
                amenity_codes.append(int(code))
            except ValueError:
                pass

        offer_id = str(_get_val(raw, cfg.get("id")) or raw.get("id", ""))
        url = raw.get("url")
        website = raw.get("website")
        
        vendor_name = _get_val(raw, cfg.get("developer_name"))
        if vendor_name:
            u["developer"] = vendor_name
        
        if not url:
            vendor_slug = _get_val(raw, cfg.get("developer_slug"))
            offer_slug = raw.get("slug", "")
            if vendor_slug and offer_slug:
                url = f"https://rynekpierwotny.pl/oferty/{vendor_slug}/{offer_slug}-{offer_id}/"

        rp_src = {"id": offer_id, "url": url}
        vendor_id = _get_val(raw, cfg.get("developer_id"))
        if vendor_id:
            rp_src["vendor_id"] = str(vendor_id)
            
        u["sources"]["rp"] = rp_src
        u["website"] = website
        
        u["location"].update({
            "coords": [lat, lng],
            "address": _get_val(raw, cfg.get("street")),
            "city": _get_val(raw, cfg.get("city")),
            "district": _get_val(raw, cfg.get("region")),
        })

        try:
            p_min = _get_val(raw, cfg.get("price_min"))
            p_max = _get_val(raw, cfg.get("price_max"))
            pm2_min = _get_val(raw, cfg.get("price_m2_min"))
            pm2_max = _get_val(raw, cfg.get("price_m2_max"))
            
            is_rental = _get_val(raw, cfg.get("transaction_type")) == "rent"
            if is_rental:
                u["financials"].update({"rent_price_min": float(p_min) if p_min is not None else None})
            else:
                u["financials"].update({
                    "price_min": float(p_min) if p_min is not None else None,
                    "price_max": float(p_max) if p_max is not None else None,
                    "price_m2_min": float(pm2_min) if pm2_min is not None else None,
                    "price_m2_max": float(pm2_max) if pm2_max is not None else None,
                })
        except (ValueError, TypeError):
            pass

        u["specifications"].update({
            "delivery_date": delivery,
            "units_count": _get_val(raw, cfg.get("units_count")) or raw.get("properties"),
            "ceiling_height_min": _get_val(raw, cfg.get("ceiling_height_min")),
            "ceiling_height_max": _get_val(raw, cfg.get("ceiling_height_max")),
            "segment": _get_val(raw, cfg.get("segment"))
        })
        u["amenities"]["raw_codes"] = amenity_codes
        u["image_urls"] = gallery_urls
        u["images_count"] = len(gallery_urls)
        return u


class OtodomAdapter:
    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if "raw_details" in data:
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
        ad = raw.get("ad") or raw
        cfg = PORTAL_MAPPING.get("oto", {}).get("investment", {})

        images = _get_val(ad, cfg.get("images"))
        if not images:
            images = ad.get("image_urls", [])

        lat = _get_val(raw, cfg.get("latitude"))
        lng = _get_val(raw, cfg.get("longitude"))

        agency_name = _get_val(ad, cfg.get("developer_name"))
        url = ad.get("url")
        
        title = _get_val(ad, cfg.get("name"))
        u = _unified_base(inv_slug, dev_slug, title, developer=agency_name)
        
        oto_src = {"url": url or ""}
        oto_id = _get_val(raw, cfg.get("id"))
        if oto_id:
            oto_src["id"] = str(oto_id)
        
        agency_id = _get_val(ad, cfg.get("developer_id"))
        if agency_id:
            oto_src["agency_id"] = str(agency_id)
            
        u["sources"]["oto"] = oto_src
        u["location"]["coords"] = [lat, lng]
        u["location"]["address"] = _get_val(ad, cfg.get("street"))
        u["location"]["city"] = _get_val(ad, cfg.get("city"))
        u["location"]["district"] = _get_val(ad, cfg.get("region"))

        price_min = _get_val(raw, cfg.get("price_min"))
        price_m2_min = _get_val(raw, cfg.get("price_m2_min"))
        
        is_rental = _get_val(ad, cfg.get("transaction_type")) == "rent"

        if is_rental:
            u["financials"].update({
                "rent_price_min": float(price_min) if price_min else None,
            })
        else:
            u["financials"].update({
                "price_min": float(price_min) if price_min else None,
                "price_m2_min": float(price_m2_min) if price_m2_min else None
            })

        u["specifications"].update({
            "units_count": _get_val(ad, cfg.get("units_count")),
            "ceiling_height_min": _get_val(ad, cfg.get("ceiling_height_min")),
            "ceiling_height_max": _get_val(ad, cfg.get("ceiling_height_max")),
            "segment": _get_val(ad, cfg.get("segment"))
        })
        
        dq = dy = None
        del_date_str = _get_val(ad, cfg.get("delivery_date"))
        if del_date_str and isinstance(del_date_str, str):
            try:
                parts = del_date_str.split("-")
                dy = int(parts[0])
                dq = (int(parts[1]) - 1) // 3 + 1
            except Exception:
                pass
        
        if dq is None:
            dq = _get_val(ad, cfg.get("delivery_fallback_quarter"))
            dy = _get_val(ad, cfg.get("delivery_fallback_year"))
        
        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": f"{dy}-Q{dq}" if dy and dq else None,
        })
        
        u["image_urls"] = images
        u["images_count"] = len(images)
        return u


class TOAdapter:
    @classmethod
    def transform(cls, data: dict, inv_slug: str, dev_slug: str) -> dict:
        if "raw_details" in data:
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
        cfg = PORTAL_MAPPING.get("to", {}).get("investment", {})

        developer_name = _get_val(raw, cfg.get("developer_name"))
        price_min = _get_val(raw, cfg.get("price_min"))
        price_max = _get_val(raw, cfg.get("price_max"))
        price_m2_min = _get_val(raw, cfg.get("price_m2_min"))
        price_m2_max = _get_val(raw, cfg.get("price_m2_max"))
        
        if isinstance(raw.get("offers"), list) and raw.get("offers") and price_min is None:
            off = raw["offers"][0]
            if isinstance(off, dict):
                price_min = off.get("lowPrice")
                price_max = off.get("highPrice")
                if price_m2_min is None:
                    price_m2_min = off.get("pricePerSqm")

        try:
            price_min = float(price_min or 0) or None
            price_max = float(price_max or 0) or None
            price_m2_min = float(price_m2_min or 0) or None
            price_m2_max = float(price_m2_max or 0) or None
        except (TypeError, ValueError):
            price_min = price_max = price_m2_min = price_m2_max = None

        urls = raw.get("_raw_gallery_urls") or raw.get("image_urls", [])

        lat = _get_val(raw, cfg.get("latitude"))
        lng = _get_val(raw, cfg.get("longitude"))

        amenity_labels = _get_val(raw, cfg.get("amenities")) or []

        title = _get_val(raw, cfg.get("name")) or raw.get("name")
        u = _unified_base(inv_slug, dev_slug, title, developer=developer_name)
        
        to_src = {"url": raw.get("url") or raw.get("to_url") or ""}
        to_id = _get_val(raw, cfg.get("id"))
        if to_id:
            to_src["id"] = str(to_id)
            
        dev_id = _get_val(raw, cfg.get("developer_id"))
        if dev_id:
            to_src["developer_id"] = str(dev_id)
            
        u["sources"]["to"] = to_src
        u["location"].update({
            "coords": [lat, lng],
            "address": _get_val(raw, cfg.get("street")),
            "city": _get_val(raw, cfg.get("city")),
            "district": _get_val(raw, cfg.get("region"))
        })
        
        is_rental = _get_val(raw, cfg.get("transaction_type")) == "rent"
        if is_rental:
            u["financials"].update({"rent_price_min": price_min})
        else:
            u["financials"].update({
                "price_min": price_min, 
                "price_max": price_max,
                "price_m2_min": price_m2_min,
                "price_m2_max": price_m2_max
            })
            
        u["amenities"]["labels"] = amenity_labels
        u["specifications"].update({
            "units_count": _get_val(raw, cfg.get("units_count")),
            "ceiling_height_min": _get_val(raw, cfg.get("ceiling_height_min")),
            "ceiling_height_max": _get_val(raw, cfg.get("ceiling_height_max")),
            "segment": _get_val(raw, cfg.get("segment"))
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
