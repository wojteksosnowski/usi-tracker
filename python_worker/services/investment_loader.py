import json
import logging
import math
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

from python_worker.services.amenity_scorer import suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images

logger = logging.getLogger(__name__)

def load_investment(system_id: str | None = None, usi_file: Path | None = None, data_dir: Path | None = None, public_usi_dir: Path | None = None, fast_index: bool = True, **kwargs) -> dict | None:

    """
    Unified loader for investment data from disk.
    Combines usi_*.json with photos scan and ratings.
    Resolves resources exclusively by system_id or direct usi_file.
    """
    import time
    start_t = time.time()
    if data_dir is None: data_dir = Path(USI_DATA_DIR)
    if public_usi_dir is None: public_usi_dir = Path(PUBLIC_USI_DIR)
    data_dir = Path(data_dir) if isinstance(data_dir, str) else data_dir
    public_usi_dir = Path(public_usi_dir) if public_usi_dir and isinstance(public_usi_dir, str) else public_usi_dir
    resources = None
    inv_dir = None
    dev_slug = None
    inv_slug = None

    if not usi_file and not system_id:
        logger.error("load_investment: Failed to load investment. Neither system_id nor usi_file provided.")
        return None

    if not usi_file and system_id:
        if str(system_id).startswith("legacy_"):
            logger.error(f"load_investment: Cannot load legacy ID {system_id}. Must use direct usi_file.")
            return None
        
        # OPTIMIZATION: Avoid heavy InvestmentService instantiation
        from python_worker.services.investment_identity import InvestmentIdentityResolver
        resolver = InvestmentIdentityResolver(data_dir=data_dir, public_usi_dir=public_usi_dir)
        resources = resolver.get_investment_resources(system_id)
        if resources:
            usi_file = resources["files"].get("anchor")
            m = resources["metadata"]
            dev_slug = m.get("developer_slug") or "unknown"
            inv_slug = m.get("investment_slug") or "unknown"
            inv_dir = resources["base_dir"]
        else:
            logger.error(f"load_investment: Could not resolve resources for ID {system_id}.")
            return None

    if not usi_file or not usi_file.exists():
        logger.error(f"load_investment: Anchor file not found for ID {system_id}.")
        return None

    if not inv_dir:
        inv_dir = usi_file.parent
        inv_slug = inv_dir.name
        dev_slug = inv_dir.parent.name
        
    try:
        usi = json.loads(usi_file.read_text())
        if resources and not usi.get("usi_inv_id"):
            usi["usi_inv_id"] = resources["id"]
            
        # Ensure portal and portal_id are available for the index
        if not usi.get("portal") or not usi.get("portal_id"):
            parts = usi_file.stem.split("_")
            if len(parts) >= 3 and parts[0] == "usi":
                if not usi.get("portal"): usi["portal"] = parts[1]
                if not usi.get("portal_id"): usi["portal_id"] = parts[2]
                
        # MANDAT ID-ONLY: Automatyczne dowiązanie usi_dev_id na podstawie portal_id z źródeł (user hint)
        if not usi.get("usi_dev_id"):
            from python_worker.developer_index import load as load_dev_index
            dev_index = load_dev_index(data_dir.parent / "USIdev")
            if dev_index:
                sources = usi.get("sources", {})
                for portal, pdata in sources.items():
                    pid = pdata.get("vendor_id") or pdata.get("agency_id") or pdata.get("developer_id")
                    if not pid: continue
                    
                    # Szukamy dewelopera z tym portal_id w jego mappingu
                    for d_entry in dev_index:
                        pm = d_entry.get("portal_mapping", {})
                        p_info = pm.get(portal) or {}
                        if portal == "rp" and str(p_info.get("id")) == str(pid):
                            usi["usi_dev_id"] = d_entry["usi_dev_id"]
                            break
                        elif portal == "oto" and str(pid) in [str(a) for a in (p_info.get("agency_ids") or [p_info.get("agency_id")]) if a]:
                            usi["usi_dev_id"] = d_entry["usi_dev_id"]
                            break
                        elif portal == "to" and str(p_info.get("id") or p_info.get("agency_id")) == str(pid):
                            usi["usi_dev_id"] = d_entry["usi_dev_id"]
                            break
                    if usi.get("usi_dev_id"): break
    except Exception:
        return None

    # Authoritative image resolution (06.01.10)
    images = resolve_images(usi, inv_dir=inv_dir, public_usi_dir=public_usi_dir, fast_index=fast_index)

    duration = (time.time() - start_t) * 1000
    if not fast_index:
        logger.info(f"load_investment: Loaded {system_id or usi_file.name} in {duration:.1f}ms")

    photos_to_delete = usi.get("photos_to_delete", 0)

    am_data = usi.get("amenities", {})
    display_amenities = am_data.get("labels", [])
    if not display_amenities and usi.get("amenities_matched"):
        display_amenities = [m["label"] for m in usi.get("amenities_matched")]

    source = "RP"
    sources = usi.get("sources", {})
    if "rp" in sources: source = "RP"
    elif "oto" in sources: source = "OTO"
    elif "to" in sources: source = "TO"
    
    source_links = []
    if "rp" in sources and sources["rp"].get("url"): source_links.append({"source": "RP", "url": sources["rp"]["url"]})
    if "oto" in sources and sources["oto"].get("url"): source_links.append({"source": "OTO", "url": sources["oto"]["url"]})
    if "to" in sources and sources["to"].get("url"): source_links.append({"source": "TO", "url": sources["to"]["url"]})
    if not source_links: source_links.append({"source": "RP", "url": "https://rynekpierwotny.pl/"})
    
    source_url = source_links[0]["url"]

    loc = usi.get("location", {})
    coords = loc.get("coords")
    lat = coords[0] if coords and len(coords) > 0 else None
    lng = coords[1] if coords and len(coords) > 1 else None
    
    address = loc.get("address") or ""
    city = loc.get("city")
    if not city and address:
        first_part = address.split(",")[0].strip()
        if first_part and not first_part.lower().startswith(("ul.", "al.", "os.", "pl.")):
            city = first_part
    district = loc.get("district")
    if not district:
        parts = [p.strip() for p in address.split(",")]
        district = parts[-1] if len(parts) >= 2 else inv_slug.split("-")[0].title()

    master_id = usi.get("master_id")
    merged_from = []
    master_usi_inv_id = None
    if master_id:
        # Master files are stored in the root of USIdata (data_dir)
        master_file = data_dir / f"inv_master_{master_id}.json"
        
        # Fallback for legacy locations (in the investment folder)
        if not master_file.exists():
            master_file = inv_dir / f"inv_master_{master_id}.json"
        
        if master_file.exists():
            try:
                master_data = json.loads(master_file.read_text())
                merged_from = master_data.get("merged_from", [])
                master_usi_inv_id = master_data.get("master_usi_inv_id")
            except Exception: pass

    ratings_data = usi.get("ratings", {})
            
    base_data = {
        "slug": f"{dev_slug}/{inv_slug}",
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "name": usi.get("name", inv_slug.title()),
        "developer": usi.get("developer", dev_slug.title()),
        "address": address,
        "city": city,
        "district": district,
        "source": source,
        "source_url": source_url,
        "source_links": source_links,
        "price_avg": usi.get("financials", {}).get("price_avg") or 0,
        "price_min": usi.get("financials", {}).get("price_min"),
        "price_max": usi.get("financials", {}).get("price_max"),
        "price_m2_min": usi.get("financials", {}).get("price_m2_min"),
        "price_m2_max": usi.get("financials", {}).get("price_m2_max"),
        "rent_price_min": usi.get("financials", {}).get("rent_price_min"),
        "rent_price_max": usi.get("financials", {}).get("rent_price_max"),
        "units": usi.get("specifications", {}).get("units_count") or 0,
        "delivery": usi.get("specifications", {}).get("delivery_date") or "—",
        "segment": usi.get("specifications", {}).get("segment"),
        "ceiling_height_min": usi.get("specifications", {}).get("ceiling_height_min"),
        "ceiling_height_max": usi.get("specifications", {}).get("ceiling_height_max"),
        "specifications": usi.get("specifications", {}),
        "status": usi.get("status", "Brak"),
        "amenities": display_amenities,
        "amenities_score": usi.get("amenities_score", 0),
        "amenities_matched": usi.get("amenities_matched", []),
        "suggested_udogodnienia": usi.get("suggested_udogodnienia", []),
        "coords": [lat, lng],
        "photos": images,
        "image_urls": usi.get("image_urls", []),
        "images_count": usi.get("images_count", len(images)),
        "portal": usi.get("portal"),
        "portal_id": usi.get("portal_id"),
        "id": system_id or usi.get("master_id") or (f"{usi.get('portal')}_{usi.get('portal_id')}" if usi.get("portal") and usi.get("portal_id") else f"legacy_{dev_slug}/{inv_slug}"),
        "usi_inv_id": usi.get("usi_inv_id"),
        "usi_dev_id": usi.get("usi_dev_id"),
        "reviewed": usi.get("reviewed", False),
        "ratings": ratings_data,
        "comment": ratings_data.get("komentarz", ""),
        "photos_to_delete": photos_to_delete,
        "folder_path": f"Public/USIdata/{dev_slug}/{inv_slug}",
        "last_updated_ts": usi_file.stat().st_mtime if usi_file else None,
        "website": "",
        "sources": sources,
        "master_id": master_id,
        "master_usi_inv_id": master_usi_inv_id,
        "suggestions": usi.get("suggestions", []),
        "merged_from": merged_from,
        "nearby_investments": usi.get("nearby_investments", []),
    }

    if resources:
        files_dict = {}
        for key, val in resources.get("files", {}).items():
            if val is None: continue
            if isinstance(val, list): files_dict[key] = [str(p) for p in val]
            else: files_dict[key] = str(val)
        
        base_data["resources"] = {
            "images_dir": str(resources["images_dir"]) if resources.get("images_dir") else None,
            "files": files_dict
        }

    return base_data
