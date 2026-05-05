import json
import logging
import math
import re
import csv as _csv
from pathlib import Path
from datetime import datetime
from functools import lru_cache
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.here_maps import build_here_url

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

def _load_investment(dev_slug: str, inv_slug: str, data_dir: Path = None, public_usi_dir: Path = None) -> dict | None:
    if data_dir is None: data_dir = Path(USI_DATA_DIR)
    if public_usi_dir is None: public_usi_dir = Path(PUBLIC_USI_DIR)
    
    inv_dir = data_dir / dev_slug / inv_slug
    usi_file = inv_dir / f"usi_{inv_slug}.json"
    
    if not usi_file.exists():
        return None
        
    try:
        usi = json.loads(usi_file.read_text())
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

    img_dir = public_usi_dir / dev_slug / inv_slug
    images = []
    if img_dir.is_dir():
        images = sorted(
            f"/api/image/{dev_slug}/{inv_slug}/{p.name}"
            for p in img_dir.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and not p.name.startswith('.')
        )

    am_data = usi.get("amenities", {})
    labels = am_data.get("labels", [])
    raw_codes = am_data.get("raw_codes", [])
    
    score_data = _compute_amenity_score(labels, raw_codes)
    
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
    lat = loc.get("coords", [0, 0])[0] or 0
    lng = loc.get("coords", [0, 0])[1] or 0
    
    here_map_url = here_map_url_dark = ""
    if lat != 0 or lng != 0:
        try:
            here_map_url = build_here_url(lat, lng, style="explore.day", zoom=14, width=560, height=140)
            here_map_url_dark = build_here_url(lat, lng, style="explore.night", zoom=14, width=560, height=140)
        except Exception:
            pass
            
    address = loc.get("address") or ""
    district = loc.get("district")
    if not district:
        parts = [p.strip() for p in address.split(",")]
        district = parts[-1] if len(parts) >= 2 else inv_slug.split("-")[0].title()

    return {
        "slug": f"{dev_slug}/{inv_slug}",
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "name": usi.get("name", inv_slug.title()),
        "developer": usi.get("developer", dev_slug.title()),
        "address": address,
        "city": loc.get("city"),
        "district": district,
        "source": source,
        "source_url": source_url,
        "source_links": source_links,
        "price_avg": usi.get("financials", {}).get("price_avg", 0),
        "units": usi.get("specifications", {}).get("units_count", 0),
        "delivery": usi.get("specifications", {}).get("delivery_date", "—"),
        "status": usi.get("status", "Brak"),
        "amenities": labels,
        "amenities_score": score_data["score"],
        "amenities_matched": score_data["matched"],
        "suggested_udogodnienia": _suggest_udogodnienia(score_data["score"]),
        "coords": [lat, lng],
        "photos": images,
        "ratings": usi.get("ratings", {}),
        "comment": usi.get("ratings", {}).get("komentarz", ""),
        "photos_to_delete": photos_to_delete,
        "folder_path": str(inv_dir),
        "website": "",
        "here_map_url": here_map_url,
        "here_map_url_dark": here_map_url_dark,
    }
