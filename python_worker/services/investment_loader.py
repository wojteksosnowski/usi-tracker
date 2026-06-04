import json
import logging
import math
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

from python_worker.services.amenity_scorer import compute_amenity_score, suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images

logger = logging.getLogger(__name__)

def find_inv_file(inv_dir: Path, inv_slug: str, system_id: str = None) -> Path | None:
    """Find the canonical investment JSON in inv_dir (by system_id first, then new format, then legacy)."""
    if system_id:
        if system_id.startswith("MASTER-"):
            pass
        elif "_" in system_id and not system_id.startswith("legacy_"):
            portal, portal_id = system_id.split("_", 1)
            f = inv_dir / f"usi_{portal}_{portal_id}.json"
            if f.exists():
                return f
        else:
            for f in inv_dir.glob("usi_*.json"):
                if f.name == f"{system_id.replace('legacy_', '')}.json":
                    return f

    for p in ("rp", "oto", "to"):
        candidates = sorted(inv_dir.glob(f"usi_{p}_*.json"))
        if candidates:
            return candidates[0]

    for legacy in (
        inv_dir / f"usi_{inv_slug}.json",
        inv_dir / f"usi_rp_{inv_slug}.json",
        inv_dir / f"usi_oto_{inv_slug}.json",
        inv_dir / f"usi_to_{inv_slug}.json",
    ):
        if legacy.exists():
            return legacy
    return None

def load_investment(system_id: str | None = None, usi_file: Path | None = None, data_dir: Path | None = None, public_usi_dir: Path | None = None, fast_index: bool = False, **kwargs) -> dict | None:

    """
    Unified loader for investment data from disk.
    Combines usi_*.json with photos scan and ratings.
    Resolves resources exclusively by system_id or direct usi_file.
    """
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
        from python_worker.services.investment_service import InvestmentService
        svc = InvestmentService(data_dir=data_dir, public_usi_dir=public_usi_dir)
        resources = svc.get_investment_resources(system_id)
        if resources:
            usi_file = resources["files"].get("anchor")
            slug_parts = resources["metadata"]["slug"].split("/")
            if len(slug_parts) >= 2:
                dev_slug = slug_parts[0]
                inv_slug = slug_parts[1]
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
    except Exception:
        return None

    deletion_file = inv_dir / "deletion_list.json"
    photos_to_delete = 0
    if not fast_index and deletion_file.exists():
        try:
            dl = json.loads(deletion_file.read_text())
            photos_to_delete = len(dl.get("paths", []))
        except Exception: pass

    images = resolve_images(usi, inv_dir, public_usi_dir, resources, fast_index)

    am_data = usi.get("amenities", {})
    labels = am_data.get("labels", [])
    raw_codes = am_data.get("raw_codes", [])
    
    score_data = compute_amenity_score(labels, raw_codes)
    display_amenities = labels
    if not display_amenities and score_data["matched"]:
        display_amenities = [m["label"] for m in score_data["matched"]]

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
        master_file = inv_dir / f"inv_master_{master_id}.json"
        if not master_file.exists() and data_dir:
            found = list(data_dir.rglob(f"inv_master_{master_id}.json"))
            if found: master_file = found[0]
        
        if master_file.exists():
            try:
                master_data = json.loads(master_file.read_text())
                merged_from = master_data.get("merged_from", [])
                master_usi_inv_id = master_data.get("master_usi_inv_id")
            except Exception: pass

    ratings_data = usi.get("ratings", {})
    if inv_dir:
        ratings_file = inv_dir / "ratings.json"
        if ratings_file.exists():
            try:
                ratings_data = json.loads(ratings_file.read_text())
            except Exception: pass
            
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
        "amenities_score": score_data["score"],
        "amenities_matched": score_data["matched"],
        "suggested_udogodnienia": suggest_udogodnienia(score_data["score"]),
        "coords": [lat, lng],
        "photos": images,
        "image_urls": usi.get("image_urls", []),
        "images_count": usi.get("images_count", len(images)),
        "id": system_id or usi.get("master_id") or (f"{usi.get('portal')}_{usi.get('portal_id')}" if usi.get("portal") and usi.get("portal_id") else f"legacy_{dev_slug}/{inv_slug}"),
        "usi_inv_id": usi.get("usi_inv_id"),
        "usi_dev_id": usi.get("usi_dev_id"),
        "ratings": ratings_data,
        "comment": ratings_data.get("komentarz", ""),
        "photos_to_delete": photos_to_delete,
        "folder_path": str(inv_dir),
        "last_updated_ts": usi_file.stat().st_mtime if usi_file else None,
        "website": "",
        "sources": sources,
        "master_id": master_id,
        "master_usi_inv_id": master_usi_inv_id,
        "suggestions": usi.get("suggestions", []),
        "merged_from": merged_from,
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
