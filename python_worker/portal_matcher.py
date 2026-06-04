import json
import logging
import math
import re
import unicodedata
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

logger = logging.getLogger(__name__)

_SLUG_REPLACE = str.maketrans("łŁ", "lL")

# Stage suffixes to strip: "etap 3", "etap III", "etap ix", "III", "faza 2"
_STAGE_RE = re.compile(
    r'\s+(etap|faza|stage|phase)\s+[\divxlIVXL]+\b'
    r'|\s+[IVX]{1,5}\b(?!\w)',
    re.IGNORECASE,
)


@dataclass
class MatchSuggestion:
    rp_folder: str
    other_portal: str
    other_folder: str
    confidence: str
    signals: list = field(default_factory=list)
    rp_name: str = ""
    other_name: str = ""
    distance_m: float = None


def normalize_name(name: str) -> str:
    if not name:
        return ""
    cleaned = _STAGE_RE.sub("", name).strip()
    text = cleaned.translate(_SLUG_REPLACE)
    nfkd = unicodedata.normalize("NFKD", text)
    return nfkd.encode("ascii", "ignore").decode("ascii").lower().strip()


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(dλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _sim(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _parse_rp_delivery(result: dict):
    """Returns (year, quarter) int tuple or None."""
    upper = result.get("construction_date_upper")
    if not upper:
        return None
    try:
        parts = upper.split("-")
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 12
        quarter = (month - 1) // 3 + 1
        return (year, quarter)
    except (ValueError, IndexError):
        return None


def _parse_oto_delivery(result: dict):
    """Returns (year, quarter) int tuple or None."""
    q = result.get("delivery_quarter")
    y = result.get("delivery_year")
    if q and y:
        try:
            return (int(y), int(q))
        except (ValueError, TypeError):
            return None
    return None


def _quarters_apart(a, b) -> int:
    """Distance in quarters between two (year, quarter) tuples."""
    return abs((a[0] - b[0]) * 4 + (a[1] - b[1]))


def load_all_app_results(data_dir: Path) -> list:
    data_dir = Path(data_dir)
    results = []
    for path in data_dir.rglob("app_result_*.json"):
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            data["_path"] = str(path)
            parts = path.relative_to(data_dir).parts
            if len(parts) >= 2:
                data["_folder"] = f"{parts[0]}/{parts[1]}"
            results.append(data)
        except Exception as e:
            logger.debug(f"Skipping {path}: {e}")
    # Also include stubs for otodom (they have coordinates from CSV import)
    for path in data_dir.rglob("usi_stage_stub.json"):
        pass  # stubs are RP-only, skip for matching
    return results


def find_matches(results: list) -> list:
    rp = [r for r in results if r.get("source") == "rynekpierwotny.pl"]
    others = [r for r in results if r.get("source") in ("otodom.pl", "tabelaofert.pl")]

    suggestions = []

    for r in rp:
        r_lat = r.get("latitude")
        r_lon = r.get("longitude")
        r_dev = r.get("developer_slug", "")
        r_name_norm = normalize_name(r.get("name") or "")
        r_units = r.get("properties_count")
        r_delivery = _parse_rp_delivery(r)
        r_folder = r.get("_folder", "")

        for o in others:
            o_lat = o.get("latitude")
            o_lon = o.get("longitude")
            o_dev = o.get("developer_slug", "")
            o_name_norm = normalize_name(o.get("title") or o.get("name") or "")
            o_folder = o.get("_folder", "")

            # Skip if same folder (shouldn't happen but guard against self-match)
            if r_folder == o_folder:
                continue

            signals = []
            dist_m = None

            # --- Coordinates ---
            coords_ok = False
            if r_lat and r_lon and o_lat and o_lon:
                dist_m = haversine_m(r_lat, r_lon, o_lat, o_lon)
                if dist_m <= 150:
                    coords_ok = True
                    signals.append(f"coords_{int(dist_m)}m")

            # --- Developer ---
            dev_ok = False
            if r_dev and o_dev:
                if r_dev == o_dev:
                    dev_ok = True
                    signals.append("same_dev")
                else:
                    dev_sim = _sim(r_dev, o_dev)
                    if dev_sim >= 0.9:
                        dev_ok = True
                        signals.append(f"dev_{dev_sim:.2f}")

            # --- Name similarity ---
            name_ok = False
            if r_name_norm and o_name_norm:
                name_sim = _sim(r_name_norm, o_name_norm)
                if name_sim >= 0.82:
                    name_ok = True
                    signals.append(f"name_{name_sim:.2f}")

            # --- Delivery date ---
            delivery_ok = False
            o_delivery = _parse_oto_delivery(o)
            if r_delivery and o_delivery:
                gap = _quarters_apart(r_delivery, o_delivery)
                if gap <= 2:
                    delivery_ok = True
                    signals.append(f"delivery_q{r_delivery[1]}_{r_delivery[0]}")

            # --- Units count ---
            o_units = None
            raw_oto = o.get("raw_details") or {}
            unit_groups = raw_oto.get("unitGroups", {}).get("items", [])
            if unit_groups:
                try:
                    o_units = sum(int(ug.get("count", 0)) for ug in unit_groups)
                except (TypeError, ValueError):
                    pass

            units_ok = False
            if r_units and o_units and r_units > 0:
                ratio = abs(int(r_units) - o_units) / int(r_units)
                if ratio <= 0.30:
                    units_ok = True
                    signals.append(f"units_rp{r_units}_oto{o_units}")

            # If both have coords but they disagree (>150m), reject even low-confidence matches
            both_have_coords = (r_lat and r_lon and o_lat and o_lon)
            coords_contradict = both_have_coords and (not coords_ok)

            # --- Determine confidence ---
            if not signals:
                continue

            if coords_ok and dist_m is not None and dist_m <= 50 and dev_ok:
                confidence = "exact"
            elif coords_ok and dev_ok and name_ok:
                confidence = "high"
            elif coords_ok and dev_ok:
                confidence = "medium"
            elif dev_ok and name_ok and not coords_contradict:
                confidence = "low"
            else:
                continue

            # Delivery date mismatch can downgrade confidence
            if r_delivery and o_delivery and _quarters_apart(r_delivery, o_delivery) > 2:
                if confidence == "exact":
                    confidence = "high"
                elif confidence == "high":
                    confidence = "medium"

            portal = o.get("source", "").replace(".pl", "")

            suggestions.append(MatchSuggestion(
                rp_folder=r_folder,
                other_portal=portal,
                other_folder=o_folder,
                confidence=confidence,
                signals=signals,
                rp_name=r.get("name") or "",
                other_name=o.get("title") or o.get("name") or "",
                distance_m=round(dist_m, 1) if dist_m is not None else None,
            ))

    # Sort: exact first, then high, medium, low
    order = {"exact": 0, "high": 1, "medium": 2, "low": 3}
    suggestions.sort(key=lambda s: order.get(s.confidence, 9))
    return suggestions


def save_suggestions(suggestions: list, output_path: Path):
    output_path = Path(output_path)
    data = [
        {
            "rp_folder": s.rp_folder,
            "other_portal": s.other_portal,
            "other_folder": s.other_folder,
            "confidence": s.confidence,
            "signals": s.signals,
            "rp_name": s.rp_name,
            "other_name": s.other_name,
            "distance_m": s.distance_m,
        }
        for s in suggestions
    ]
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(data)} match suggestions to {output_path}")


def run_matcher(data_dir: Path, output_path: Path, min_confidence: str = "low") -> int:
    order = {"exact": 0, "high": 1, "medium": 2, "low": 3}
    min_level = order.get(min_confidence, 3)

    results = load_all_app_results(data_dir)
    suggestions = find_matches(results)
    filtered = [s for s in suggestions if order.get(s.confidence, 9) <= min_level]
    save_suggestions(filtered, output_path)
    return len(filtered)


def filter_new_investments(discovered_items: list[dict], portal: str) -> list[dict]:
    """
    Adds 'is_new' and 'registered' flags to discovered items by comparing with existing USIdata.
    portal: 'rp' or 'otodom'
    """
    from .developer_manager import DeveloperManager
    from .config import USI_DATA_DIR

    dm = DeveloperManager(USI_DATA_DIR)
    identifiers = dm.get_existing_identifiers()

    rp_ids = identifiers["rp_ids"]
    oto_ids = identifiers["oto_ids"]
    oto_slugs = identifiers["oto_slugs"]
    to_ids = identifiers.get("to_ids", set())

    for item in discovered_items:
        is_new = True
        if portal == "rp":
            item_id = str(item.get("id"))
            if item_id and item_id != "None" and item_id in rp_ids:
                is_new = False
        elif portal == "otodom" or portal == "oto":
            item_id = str(item.get("id"))
            item_hash = item.get("hash_id")
            item_slug = item.get("slug")
            
            # 1. Check numeric ID
            id_match = item_id and item_id != "None" and item_id in oto_ids
            
            # 2. Check hash ID from discovery result
            hash_match_field = item_hash and item_hash in oto_ids
            
            # 3. Check full slug
            slug_match = item_slug and item_slug in oto_slugs
            
            # 4. Extract Hash ID from slug as per Coda spec and check (fallback)
            hash_match_regex = False
            if item_slug and not hash_match_field:
                h_match = re.search(r"ID([a-zA-Z0-9]+)$", item_slug)
                if h_match:
                    if h_match.group(1) in oto_ids:
                        hash_match_regex = True

            if id_match or hash_match_field or slug_match or hash_match_regex:
                is_new = False
            else:
                logger.info(f"Otodom item NEW: id={item_id}, hash={item_hash}. (Tried matching against {len(oto_ids)} oto_ids)")
        elif portal in ("to", "tabelaofert"):
            item_id = str(item.get("id"))
            if item_id and item_id != "None" and item_id in to_ids:
                is_new = False

        item["is_new"] = is_new
        item["registered"] = not is_new
        item["portal"] = portal

    return discovered_items
