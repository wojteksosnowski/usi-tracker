import re
from .merger import Merger


def _get_val(data, key, default=None):
    """Unwrap RP API wrapper dicts: {"type": ..., "value": ...}."""
    if not data or key not in data:
        return default
    val = data[key]
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def _unified_base(inv_slug, dev_slug, name, developer=None):
    return {
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "name": name,
        "developer": developer,
        "website": None,
        "sources": {},
        "location": {"coords": [None, None], "address": None, "city": None, "district": None},
        "specifications": {"delivery_date": None, "delivery_quarter": None, "delivery_year": None, "units_count": None, "ceiling_height": None},
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
        u = _unified_base(inv_slug, dev_slug,
                          _get_val(raw, "name") or raw.get("name"))

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

        offer_id = str(raw.get("id", ""))
        url = raw.get("url")
        website = raw.get("website")
        vendor = _get_val(raw, "vendor")
        if isinstance(vendor, dict):
            vendor_name = _get_val(vendor, "name")
            if vendor_name:
                u["developer"] = vendor_name
            if not url:
                vendor_slug = _get_val(vendor, "slug")
                offer_slug = raw.get("slug", "")
                if vendor_slug and offer_slug:
                    url = f"https://rynekpierwotny.pl/oferty/{vendor_slug}/{offer_slug}-{offer_id}/"

        rp_src = {"id": offer_id, "url": url}
        if isinstance(vendor, dict):
            vid = _get_val(vendor, "id")
            if vid:
                rp_src["vendor_id"] = str(vid)
        u["sources"]["rp"] = rp_src
        u["website"] = website
        u["location"].update({
            "coords": [lat, lng],
            "address": _get_val(raw, "address") or raw.get("address"),
        })

        # Extract height and prices from stats if available
        stats = _get_val(raw, "stats")
        height = None
        if isinstance(stats, dict):
            h_cm = stats.get("ranges_height_max")
            if h_cm:
                try:
                    height = round(float(h_cm) / 100, 2)
                except (ValueError, TypeError):
                    pass
            
            p_min = stats.get("ranges_price_min")
            p_max = stats.get("ranges_price_max")
            pm2_min = stats.get("ranges_price_m2_min")
            pm2_max = stats.get("ranges_price_m2_max")
            if p_min is not None or p_max is not None:
                try:
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
            "units_count": _get_val(raw, "properties") or raw.get("properties"),
            "ceiling_height": height,
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

        images = [img.get("large") for img in (ad.get("images") or []) if img.get("large")]
        if not images:
            images = ad.get("image_urls", [])

        loc = (ad.get("location") or {}).get("coordinates") or {}
        lat = loc.get("latitude")
        lng = loc.get("longitude")

        agency = ad.get("agency") or {}
        agency_name = agency.get("name") or (ad.get("owner") or {}).get("name")
        url = ad.get("url")

        dq = dy = None
        for item in (ad.get("topInformation") or []):
            if item.get("label") == "project_finish_date":
                vals = item.get("values", [])
                if vals:
                    try:
                        parts = vals[0].split("-")
                        dy = int(parts[0])
                        dq = (int(parts[1]) - 1) // 3 + 1
                    except Exception:
                        pass
                break
        if dq is None:
            old_del = ad.get("investmentEstimatedDelivery") or {}
            dq = old_del.get("quarter")
            dy = old_del.get("year")

        u = _unified_base(inv_slug, dev_slug,
                          ad.get("title"), developer=agency_name)
        oto_src = {"url": url or ""}
        agency_id = agency.get("id") or (ad.get("owner") or {}).get("id")
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
        u["specifications"].update({
            "delivery_quarter": dq,
            "delivery_year": dy,
            "delivery_date": f"{dy}-Q{dq}" if dy and dq else None,
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
        lat, lng = res.get("latitude"), res.get("longitude")
        u["sources"]["to"] = {"url": res.get("to_url") or ""}
        u["location"].update({
            "coords": [lat, lng],
            "address": res.get("address"),
            "city": res.get("city"),
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
        brand = raw.get("brand") or {}
        developer_name = brand.get("name") if isinstance(brand, dict) else None

        offers = raw.get("offers") or {}
        try:
            price_min = float(offers.get("lowPrice") or 0) or None
            price_max = float(offers.get("highPrice") or 0) or None
        except (TypeError, ValueError):
            price_min = price_max = None

        urls = raw.get("_raw_gallery_urls") or raw.get("image_urls", [])

        ext_loc = raw.get("_extracted_location") or {}
        lat = ext_loc.get("latitude")
        lng = ext_loc.get("longitude")

        amenity_labels = []
        for prop in (raw.get("additionalProperty") or []):
            if isinstance(prop, dict) and prop.get("name"):
                amenity_labels.append(prop["name"])

        u = _unified_base(inv_slug, dev_slug,
                          raw.get("name"), developer=developer_name)
        u["sources"]["to"] = {"url": raw.get("url") or raw.get("to_url") or ""}
        u["location"].update({"coords": [lat, lng], "address": ext_loc.get("address"), "city": ext_loc.get("city")})
        u["financials"].update({"price_min": price_min, "price_max": price_max})
        u["amenities"]["labels"] = amenity_labels
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
