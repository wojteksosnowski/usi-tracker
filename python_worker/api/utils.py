import json
import logging
import math
import re
import csv as _csv
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

logger = logging.getLogger(__name__)

_CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia']
USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona']
_WYROZNIKI_CSV = Path(__file__).parent.parent / "data" / "wyrozniki.csv"
_STANDARD_TIERS = [(16, 4), (8, 3), (4, 2), (1, 1), (0, 0)]

@lru_cache(maxsize=1)
def _load_wyrozniki():
    w_lok, w_udo = [], []
    if not _WYROZNIKI_CSV.exists():
        return w_lok, w_udo
    try:
        with open(_WYROZNIKI_CSV, "r", encoding="utf-8") as f:
            reader = _csv.DictReader(f)
            for row in reader:
                lbl = row["Label"]
                rpno = int(row["RPno"]) if row["RPno"] else None
                try:
                    score = int(row["USIudo"])
                except:
                    score = 0
                w_udo.append((lbl, rpno, score))
    except Exception as e:
        logger.error(f"Failed to load wyrozniki: {e}")
    return w_lok, w_udo

def _compute_amenity_score(amenity_labels: list, rp_codes: list) -> dict:
    _, wyrozniki_udo = _load_wyrozniki()
    matched_lc = {}
    matched_display = {}
    rp_set = set(rp_codes)
    
    for lbl, rpno, hm_udo in wyrozniki_udo:
        lbl_lc = lbl.lower()
        if rpno is not None and rpno in rp_set and lbl_lc not in matched_lc:
            matched_lc[lbl_lc] = hm_udo
            matched_display[lbl_lc] = lbl
            
    for amenity in amenity_labels:
        al = amenity.lower()
        for lbl, _, hm_udo in wyrozniki_udo:
            lbl_lc = lbl.lower()
            if lbl_lc in al and lbl_lc not in matched_lc:
                matched_lc[lbl_lc] = hm_udo
                matched_display[lbl_lc] = lbl
                
    total = sum(matched_lc.values())
    return {
        "score": total,
        "matched": [{"label": matched_display[k], "hm_udo": v} for k, v in matched_lc.items()],
    }

def _suggest_udogodnienia(score: int):
    if score <= 0: return None
    for tier, ocena in _STANDARD_TIERS:
        if score > tier: return ocena
    return None

def _valid_slug(s: str) -> bool:
    return bool(s) and bool(re.match(r"^[a-zA-Z0-9_-]+$", s))

def _valid_filename(s: str) -> bool:
    if ".." in s: return False
    return bool(s) and bool(re.match(r"^[^/\\]+\.(jpg|jpeg|png|webp|svg)$", s, re.IGNORECASE))

def _calculate_ocena_log(ratings: dict) -> float | None:
    vals = [ratings.get(cat) for cat in _CATS if ratings.get(cat) is not None]
    if not vals:
        return None
    try:
        sum_exp = sum(math.exp(v) for v in vals)
        return math.log(sum_exp) - math.log(len(vals))
    except (ValueError, OverflowError):
        return None

def _calculate_distance(lat1, lon1, lat2, lon2):
    """Oblicza odległość między dwoma punktami (Haversine)."""
    R = 6371  # Promień Ziemi w km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _find_inv_file(inv_dir: Path, inv_slug: str, system_id: str = None) -> Path | None:
    """Find the canonical investment JSON in inv_dir (by system_id first, then new format, then legacy)."""
    if system_id:
        if system_id.startswith("MASTER-"):
            # It's a master ID, but _find_inv_file usually looks for an anchor file
            pass
        elif "_" in system_id and not system_id.startswith("legacy_"):
            portal, portal_id = system_id.split("_", 1)
            f = inv_dir / f"usi_{portal}_{portal_id}.json"
            if f.exists():
                return f
        else:
            # legacy or fallback
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

def _load_investment(dev_slug: str, inv_slug: str, data_dir: Path | None = None, public_usi_dir: Path | None = None, portal: str | None = None, system_id: str | None = None, skip_merge: bool = False) -> dict | None:
    if data_dir is None: data_dir = Path(USI_DATA_DIR)
    if public_usi_dir is None: public_usi_dir = Path(PUBLIC_USI_DIR)
    
    usi_file = None
    resources = None
    
    # PRIORITY 1: Resolve via Identity Service if ID provided
    if system_id and not system_id.startswith("legacy_"):
        from python_worker.services.investment_service import InvestmentService
        svc = InvestmentService(data_dir=data_dir, public_usi_dir=public_usi_dir)
        resources = svc.get_investment_resources(system_id)
        if resources:
            usi_file = resources["files"].get("anchor")
            # Update slugs from resources to ensure we are in the right folder
            dev_slug = resources["metadata"]["slug"].split("/")[0]
            inv_slug = resources["metadata"]["slug"].split("/")[1]

    inv_dir = data_dir / dev_slug / inv_slug

    if not usi_file:
        if system_id:
            usi_file = _find_inv_file(inv_dir, inv_slug, system_id=system_id)
        elif portal:
            # Known portal: prefer new format usi_{portal}_{id}.json, fallback to slug-based
            candidates = sorted(inv_dir.glob(f"usi_{portal}_*.json"))
            usi_file = candidates[0] if candidates else (inv_dir / f"usi_{portal}_{inv_slug}.json")
        else:
            # Autodetect: new format (rp > oto > to) then legacy slug-based variants
            for p in ("rp", "oto", "to"):
                candidates = sorted(inv_dir.glob(f"usi_{p}_*.json"))
                if candidates:
                    usi_file = candidates[0]
                    break
            if not usi_file:
                for legacy in (
                    inv_dir / f"usi_{inv_slug}.json",
                    inv_dir / f"usi_rp_{inv_slug}.json",
                    inv_dir / f"usi_oto_{inv_slug}.json",
                    inv_dir / f"usi_to_{inv_slug}.json",
                ):
                    if legacy.exists():
                        usi_file = legacy
                        break

    if not usi_file or not usi_file.exists():
        return None
        
    try:
        usi = json.loads(usi_file.read_text())
        # Robust ID injection: if the file lacks ID, but Identity Service found it, use it.
        if resources and not usi.get("usi_inv_id"):
            usi["usi_inv_id"] = resources["id"]
    except Exception:
        return None

    deletion_file = inv_dir / "deletion_list.json"
    photos_to_delete = 0
    if deletion_file.exists():
        try:
            dl = json.loads(deletion_file.read_text())
            photos_to_delete = len(dl.get("paths", []))
        except Exception:
            pass

    images = []
    # 1. Priority: Recorded paths (imgList from ratings or image_paths)
    image_paths_raw = usi.get("image_paths") or []
    img_list_str = usi.get("ratings", {}).get("imgList")
    
    # If imgList is present, it often reflects the authoritative manually verified selection
    if img_list_str and isinstance(img_list_str, str):
        image_paths_raw = [p.strip() for p in img_list_str.split(",") if p.strip()]
        
    if image_paths_raw:
        from python_worker.config import DROPBOX_PATH
        for p in image_paths_raw:
            p_clean = p.lstrip("/")
            if not (DROPBOX_PATH / p_clean).exists():
                continue
            
            # /Public/USI/{dev}/{inv}/{file} → /api/image/{dev}/{inv}/{file}
            # Or /Public/USI/{inv}/{file} → /api/image/{inv}/{file}
            if p_clean.startswith("Public/USI/"):
                suffix = p_clean[len("Public/USI/"):]
                images.append("/api/image/" + suffix)
        images = sorted(list(set(images)))

    # 2. Fallback: Direct directory scan if no valid recorded paths found
    if not images:
        if resources and resources.get("images_dir"):
            img_dir = resources["images_dir"]
        else:
            img_dir = public_usi_dir / dev_slug / inv_slug
            
        _IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}

        def _scan(d: Path) -> list:
            return sorted(
                f"/api/image/{d.parent.name}/{d.name}/{p.name}"
                for p in d.iterdir()
                if p.suffix.lower() in _IMG_EXT and not p.name.startswith('.')
            ) if d.is_dir() else []

        # 1. Exact paths (current dev_slug and USIdata parent name)
        for candidate in {
            img_dir,
            public_usi_dir / Path(inv_dir).parent.name / inv_slug,
        }:
            images = _scan(candidate)
            if images:
                break

        # 2. Locate by CDN filename from image_urls (unambiguous — matches actual content)
        if not images and public_usi_dir.is_dir():
            for url in usi.get("image_urls", []):
                stem = url.split("/files/")[-1].split("/image")[0]
                if not stem or "/" in stem:
                    continue
                hits = list(public_usi_dir.glob(f"*/*/{stem}.*"))
                if hits:
                    images = _scan(hits[0].parent)
                    break

        # 3. Prefix match within same dev dir (fallback for custom-named files)
        if not images:
            for dev_candidate in {public_usi_dir / dev_slug, public_usi_dir / Path(inv_dir).parent.name}:
                if not dev_candidate.is_dir():
                    continue
                for d in dev_candidate.iterdir():
                    if d.is_dir() and d.name.startswith(inv_slug):
                        found = _scan(d)
                        if len(found) > len(images):
                            images = found

    am_data = usi.get("amenities", {})
    labels = am_data.get("labels", [])
    raw_codes = am_data.get("raw_codes", [])
    
    score_data = _compute_amenity_score(labels, raw_codes)
    
    # Use matched labels for display if manual ones are missing
    display_amenities = labels
    if not display_amenities and score_data["matched"]:
        display_amenities = [m["label"] for m in score_data["matched"]]

    source = "RP"
    sources = usi.get("sources", {})
    if "rp" in sources: source = "RP"
    elif "oto" in sources: source = "OTO"
    elif "to" in sources: source = "TO"
    
    source_links = []
    if "rp" in sources and sources["rp"].get("url"):
        source_links.append({"source": "RP", "url": sources["rp"]["url"]})
    if "oto" in sources and sources["oto"].get("url"):
        source_links.append({"source": "OTO", "url": sources["oto"]["url"]})
    if "to" in sources and sources["to"].get("url"):
        source_links.append({"source": "TO", "url": sources["to"]["url"]})

    if not source_links:
        source_links.append({"source": "RP", "url": "https://rynekpierwotny.pl/"})
    
    source_url = source_links[0]["url"]

    loc = usi.get("location", {})
    coords = loc.get("coords")
    lat = coords[0] if coords and len(coords) > 0 else None
    lng = coords[1] if coords and len(coords) > 1 else None
    
    address = loc.get("address") or ""
    city = loc.get("city")
    # RP addresses start with city: "Warszawa, District, Street" — extract when city not set
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
            # If not in this dir, try to find it globally
            found = list(data_dir.rglob(f"inv_master_{master_id}.json"))
            if found:
                master_file = found[0]
        
        if master_file.exists():
            try:
                master_data = json.loads(master_file.read_text())
                merged_from = master_data.get("merged_from", [])
                master_usi_inv_id = master_data.get("master_usi_inv_id")
            except Exception:
                pass

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
        "suggested_udogodnienia": _suggest_udogodnienia(score_data["score"]),
        "coords": [lat, lng],
        "photos": images,
        "id": system_id or usi.get("master_id") or (f"{usi.get('portal')}_{usi.get('portal_id')}" if usi.get("portal") and usi.get("portal_id") else f"legacy_{dev_slug}/{inv_slug}"),
        "usi_inv_id": usi.get("usi_inv_id"),
        "usi_dev_id": usi.get("usi_dev_id"),
        "ratings": usi.get("ratings", {}),
        "comment": usi.get("ratings", {}).get("komentarz", ""),
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

    # 1 minikarta = 1 portal. Skip merging data from children/siblings.
    return base_data
