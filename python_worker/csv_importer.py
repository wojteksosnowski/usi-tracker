import csv
import json
import logging
import re
import shutil
import unicodedata
from pathlib import Path
from .stage_detector import extract_groups_id, extract_stages
from .logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)


_SLUG_REPLACE = str.maketrans("łŁ", "lL")

def slugify(text: str) -> str:
    # Handle characters that NFKD can't decompose (e.g. ł → l)
    text = text.translate(_SLUG_REPLACE)
    nfkd = unicodedata.normalize("NFKD", text)
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_str.lower()).strip("-")


def get_rp_val(data, key, default=None):
    if not data or key not in data:
        return default
    val = data[key]
    if isinstance(val, dict) and "value" in val:
        return val["value"]
    return val


def parse_imglist(imglist_str: str) -> list:
    if not imglist_str or not imglist_str.strip():
        return []
    # Try comma+space separator first, fall back to space-only
    if ", " in imglist_str:
        parts = imglist_str.split(", ")
    else:
        parts = imglist_str.split(" ")
    return [p.strip() for p in parts if p.strip().startswith("/Public/")]


def load_developer_mapping(konkurenci_path: Path) -> dict:
    """Loads mappings from portal IDs and names to canonical usiFolder slugs."""
    id_mapping = {
        "rp": {},
        "oto": {}
    }
    name_mapping = {} # Name -> List[slug]

    if not konkurenci_path.exists():
        return {"id": id_mapping, "name": name_mapping}

    with open(konkurenci_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Deweloper", "").strip()
            slug = row.get("usiFolder", "").strip()
            rp_id = row.get("rpID", "").strip()
            oto_id = row.get("otoID", "").strip()
            
            if not slug:
                continue

            if rp_id:
                id_mapping["rp"][rp_id] = slug
            if oto_id:
                # Handle both "ID123" and "123" formats
                clean_oto = re.sub(r"^ID", "", oto_id)
                if clean_oto:
                    id_mapping["oto"][clean_oto] = slug
            
            if name:
                name_mapping.setdefault(name, []).append(slug)

    return {"id": id_mapping, "name": name_mapping}


def extract_developer_slug(row: dict, dev_mapping: dict = None) -> str | None:
    """Return the canonical usiFolder slug from Konkurenci.csv.

    Returns None (never slugifies) when the developer has no entry in Konkurenci —
    the caller must skip the row in that case.
    """
    # PRIORYTET 1: Rozpoznawanie po ID portalowym (najpewniejsze)
    if dev_mapping and "id" in dev_mapping:
        row_rp_id = row.get("rpID", "").strip()
        if row_rp_id and row_rp_id in dev_mapping["id"]["rp"]:
            return dev_mapping["id"]["rp"][row_rp_id]

        row_oto_id = row.get("otoID", "").strip()
        if row_oto_id:
            clean_row_oto = re.sub(r"^ID", "", row_oto_id)
            if clean_row_oto in dev_mapping["id"]["oto"]:
                return dev_mapping["id"]["oto"][clean_row_oto]

    # PRIORYTET 2: Dopasowanie po nazwie dewelopera
    dev_name = row.get("Deweloper", "").strip()
    if dev_mapping and "name" in dev_mapping and dev_name in dev_mapping["name"]:
        candidates = dev_mapping["name"][dev_name]
        return candidates[0]

    # Brak dopasowania — zwróć None, nie slugifikuj
    inv_slug = row.get("USIfolder", "").strip()
    logger.warning(
        "Brak wpisu w Konkurenci.csv dla dewelopera %r (inwestycja %r, rpID=%r, otoID=%r) — wiersz pominięty",
        dev_name, inv_slug,
        row.get("rpID", ""), row.get("otoID", ""),
    )
    return None


def extract_native_slugs(row: dict) -> tuple[str | None, str | None]:
    """Wyciąga natywne slugi inwestycji z JSONów RP i OTO."""
    rp_slug = None
    oto_slug = None

    # RP Slug extraction
    rp_raw = row.get("rpJSON", "").strip()
    if rp_raw.startswith("{"):
        try:
            rp = json.loads(rp_raw)
            # RP v2 API zazwyczaj ma slug w głównym obiekcie lub vendorze
            rp_slug = rp.get("slug")
        except: pass

    # OTO Slug extraction (z URL lub JSONa)
    oto_url = row.get("strona_oto", "").strip()
    if "/inwestycja/" in oto_url:
        oto_slug = oto_url.split("/inwestycja/")[-1].split("?")[0].strip("/")
    
    # Fallback do USIfolder jeśli nie znaleziono natywnych
    fallback = row.get("USIfolder", "").strip()
    return rp_slug or fallback, oto_slug or fallback


def parse_stars(stars_str):
    """Maps ★ symbols to numbers."""
    if not stars_str: return None
    mapping = {
        "★": 1, "★★": 2, "★★★": 3, "★★★★": 4,
        "⓿¾": 0.75, "★¼": 1.25, "★½": 1.5, "★¾": 1.75,
        "★★¼": 2.25, "★★½": 2.5, "★★¾": 2.75,
        "★★★¼": 3.25, "★★★½": 3.5, "★★★¾": 3.75
    }
    return mapping.get(stars_str.strip())


def safe_float(val):
    if not val: return None
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return None


def extract_ratings(row: dict) -> dict:
    """Extracts analytical ratings from CSV row."""
    return {
        "status": row.get("Ocena", "Brak"),
        "Gwiazdki": parse_stars(row.get("Gwiazdki")),
        "Balkony": safe_float(row.get("Balkony")),
        "Fasady": safe_float(row.get("Fasady")),
        "Wnętrza": safe_float(row.get("Wnętrza")),
        "Teren": safe_float(row.get("Teren")),
        "Mieszkania": safe_float(row.get("Mieszkania")),
        "Udogodnienia": safe_float(row.get("Udogodnienia")),
        "komentarz": row.get("komentarz", "").strip()
    }


def build_rp_result(row: dict, investment_slug: str = None, ratings: dict = None, dev_mapping: dict = None) -> dict:
    rp_raw = row.get("rpJSON", "").strip()
    rp = json.loads(rp_raw) if rp_raw.startswith("{") else {}

    developer_slug = extract_developer_slug(row, dev_mapping=dev_mapping)
    if not investment_slug:
        investment_slug = row.get("USIfolder", "").strip()

    # Coordinates: rpJSON geo_point.value.coordinates = [lon, lat]
    geo_point = get_rp_val(rp, "geo_point")
    coords = get_rp_val(geo_point, "coordinates") if geo_point else None
    if isinstance(coords, dict) and "value" in coords:
        coords = coords["value"]
    if coords and len(coords) >= 2:
        longitude = coords[0]
        latitude = coords[1]
    else:
        # Fallback to CSV columns
        try:
            latitude = float(row.get("Latitude", "") or 0) or None
            longitude = float(row.get("Longitude", "") or 0) or None
        except ValueError:
            latitude = longitude = None

    construction_date = get_rp_val(rp, "construction_date_range")
    const_upper = get_rp_val(construction_date, "upper") if construction_date else None

    # IMAGE PATHS: Preserve original folder structure from imgList
    image_paths_raw = parse_imglist(row.get("imgList", ""))
    image_paths = image_paths_raw # KEEP ORIGINAL PATHS FROM CSV
    
    # Extract original usi_folder_path from image_paths if possible
    usi_folder_path = f"/Public/USI/{developer_slug}/{investment_slug}/"
    if image_paths:
        sample = Path(image_paths[0])
        if len(sample.parts) >= 5:
             # parts: ('/', 'Public', 'USI', 'dev', 'inv', 'file.jpg')
             usi_folder_path = f"/Public/USI/{sample.parts[3]}/{sample.parts[4]}/"

    stages = extract_stages(rp)
    groups_id = extract_groups_id(rp)
    groups = rp.get("groups") or {}
    offer_id = row.get("rpID", "").strip()
    sibling_stage_folders = [
        f"{developer_slug}/{s['slug']}"
        for s in stages
        if str(s["offer_id"]) != str(offer_id) and s["slug"]
    ]

    stage_sort = None
    stage_is_current = None
    for s in stages:
        if str(s["offer_id"]) == str(offer_id):
            stage_sort = s["sort"]
            stage_is_current = s["current"]
            break

    result = {
        "source": "rynekpierwotny.pl",
        "id": offer_id,
        "url": row.get("strona_rynek", "").strip(),
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": usi_folder_path,
        "name": rp.get("name"),
        "address": rp.get("address"),
        "geo_point": coords,
        "latitude": latitude,
        "longitude": longitude,
        "construction_date_upper": const_upper,
        "website": rp.get("website"),
        "properties_count": rp.get("properties"),
        "images_count": len(image_paths),
        "image_paths": image_paths,
        "groups_id": groups_id,
        "groups_name": groups.get("name"),
        "stage_sort": stage_sort,
        "stage_is_current": stage_is_current,
        "sibling_stages": stages,
        "sibling_stage_folders": sibling_stage_folders,
    }
    if ratings:
        result["ratings"] = ratings
    return result


def build_oto_result(row: dict, investment_slug: str = None, ratings: dict = None, dev_mapping: dict = None) -> dict:
    oto_raw = row.get("otoJSON", "").strip()
    page_props = json.loads(oto_raw) if oto_raw.startswith("{") else {}
    ad_data = page_props.get("ad", {})

    developer_slug = extract_developer_slug(row, dev_mapping=dev_mapping)
    if not investment_slug:
        investment_slug = row.get("USIfolder", "").strip()

    # Coordinates from ad_data
    location = ad_data.get("location", {}).get("mapDetails", {})
    lat = location.get("lat")
    lng = location.get("lon")
    if lat is None or lng is None:
        try:
            lat = float(row.get("Latitude", "") or 0) or None
            lng = float(row.get("Longitude", "") or 0) or None
        except ValueError:
            lat = lng = None

    agency = ad_data.get("agency", {}) or {}
    delivery = ad_data.get("investmentEstimatedDelivery", {}) or {}
    
    # IMAGE PATHS: Preserve original folder structure from imgList
    image_paths_raw = parse_imglist(row.get("imgList", ""))
    image_paths = image_paths_raw # KEEP ORIGINAL PATHS FROM CSV
    
    # Extract original usi_folder_path from image_paths if possible
    usi_folder_path = f"/Public/USI/{developer_slug}/{investment_slug}/"
    if image_paths:
        sample = Path(image_paths[0])
        if len(sample.parts) >= 5:
             usi_folder_path = f"/Public/USI/{sample.parts[3]}/{sample.parts[4]}/"

    result = {
        "source": "otodom.pl",
        "url": row.get("strona_otodom", "").strip(),
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": usi_folder_path,
        "title": ad_data.get("title"),
        "agency_name": agency.get("name"),
        "agency_id": agency.get("id"),
        "latitude": lat,
        "longitude": lng,
        "delivery_quarter": delivery.get("quarter"),
        "delivery_year": delivery.get("year"),
        "images_count": len(image_paths),
        "image_paths": image_paths,
    }
    if ratings:
        result["ratings"] = ratings
    return result


def import_csv(
    csv_path,
    output_dir,
    limit=None,
    folder_filter=None,
    dry_run=False,
    split_dual=False,
) -> list:
    """Import investments from USImaster.csv into the USIdata directory tree.

    When split_dual=True, rows with both rpJSON and otoJSON produce two separate
    investment folders. Ratings from the CSV are preserved in BOTH resulting records.
    """
    from .adapters import RPAdapter, OtodomAdapter, Merger
    
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)

    # Try to load developer mapping from Konkurenci.csv (expected in same dir)
    konkurenci_path = csv_path.parent / "Konkurenci.csv"
    dev_mapping = load_developer_mapping(konkurenci_path)
    if dev_mapping:
        n_id = sum(len(v) for v in dev_mapping["id"].values())
        n_name = len(dev_mapping["name"])
        logger.info(f"Loaded {n_id} portal-ID mappings and {n_name} name mappings from {konkurenci_path}")

    if not csv_path.exists():
        logger.error(f"CSV not found: {csv_path}")
        return []

    results = []
    seen_folders: dict = {}
    rows_processed = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit is not None and rows_processed >= limit:
                break

            inv_slug = row.get("USIfolder", "").strip()
            if not inv_slug:
                continue
            if folder_filter and inv_slug != folder_filter:
                continue
            
            has_rp = row.get("rpJSON", "").strip().startswith("{")
            has_oto = row.get("otoJSON", "").strip().startswith("{")

            if not has_rp and not has_oto:
                continue

            try:
                ratings = extract_ratings(row)
                is_dual = split_dual and has_rp and has_oto
                
                if is_dual:
                    rp_slug, oto_slug = extract_native_slugs(row)
                    rp_result = build_rp_result(row, investment_slug=rp_slug, ratings=ratings, dev_mapping=dev_mapping)
                    oto_result = build_oto_result(row, investment_slug=oto_slug, ratings=ratings, dev_mapping=dev_mapping)
                elif has_rp:
                    rp_result = build_rp_result(row, ratings=ratings, dev_mapping=dev_mapping)
                    oto_result = None
                else:
                    rp_result = None
                    oto_result = build_oto_result(row, ratings=ratings, dev_mapping=dev_mapping)
            except Exception as e:
                logger.warning(f"Skipping {inv_slug}: {e}")
                continue

            _any_result = rp_result or oto_result
            dev_slug = _any_result["developer_slug"] if _any_result else ""
            if not dev_slug:
                continue

            if not dry_run:
                # ── RP Processing ─────────────────────────────────────────────
                if rp_result:
                    dev_slug = rp_result["developer_slug"]
                    inv_slug_rp = rp_result["investment_slug"]
                    inv_dir_rp = output_dir / dev_slug / inv_slug_rp
                    inv_dir_rp.mkdir(parents=True, exist_ok=True)
                    
                    # Save raw details
                    rp_raw = row.get("rpJSON", "").strip()
                    with open(inv_dir_rp / f"raw_rp_{inv_slug_rp}.json", "w", encoding="utf-8") as out:
                        out.write(rp_raw)
                    
                    # Save ratings
                    with open(inv_dir_rp / f"meta_{inv_slug_rp}_ratings.json", "w", encoding="utf-8") as out:
                        json.dump(ratings, out, indent=2, ensure_ascii=False)
                    
                    # Save app_result
                    with open(inv_dir_rp / f"app_result_rp.json", "w", encoding="utf-8") as out:
                        json.dump(rp_result, out, indent=4, ensure_ascii=False)
                    
                    # Unified JSON
                    rp_unified = RPAdapter.transform(json.loads(rp_raw), inv_slug_rp, dev_slug)
                    rp_unified["image_paths"] = rp_result["image_paths"]
                    rp_unified["images_count"] = rp_result["images_count"]
                    
                    final_rp = Merger.merge(rp_data=rp_unified, meta_ratings=ratings)
                    with open(inv_dir_rp / f"usi_rp_{inv_slug_rp}.json", "w", encoding="utf-8") as out:
                        json.dump(final_rp, out, indent=2, ensure_ascii=False)
                        
                    log_to_processing_log(dev_slug, inv_slug_rp, "Imported from CSV (RP)")

                # ── OTO Processing ────────────────────────────────────────────
                if oto_result:
                    dev_slug = oto_result["developer_slug"]
                    inv_slug_oto = oto_result["investment_slug"]
                    inv_dir_oto = output_dir / dev_slug / inv_slug_oto
                    inv_dir_oto.mkdir(parents=True, exist_ok=True)
                    
                    # Save raw details
                    oto_raw = row.get("otoJSON", "").strip()
                    with open(inv_dir_oto / f"raw_oto_{inv_slug_oto}.json", "w", encoding="utf-8") as out:
                        out.write(oto_raw)
                    
                    # Save ratings
                    with open(inv_dir_oto / f"meta_{inv_slug_oto}_ratings.json", "w", encoding="utf-8") as out:
                        json.dump(ratings, out, indent=2, ensure_ascii=False)
                    
                    # Save app_result
                    with open(inv_dir_oto / f"app_result_oto.json", "w", encoding="utf-8") as out:
                        json.dump(oto_result, out, indent=4, ensure_ascii=False)
                    
                    # Unified JSON
                    oto_unified = OtodomAdapter.transform(json.loads(oto_raw), inv_slug_oto, dev_slug)
                    oto_unified["image_paths"] = oto_result["image_paths"]
                    oto_unified["images_count"] = oto_result["images_count"]
                    
                    final_oto = Merger.merge(oto_data=oto_unified, meta_ratings=ratings)
                    with open(inv_dir_oto / f"usi_oto_{inv_slug_oto}.json", "w", encoding="utf-8") as out:
                        json.dump(final_oto, out, indent=2, ensure_ascii=False)
                        
                    log_to_processing_log(dev_slug, inv_slug_oto, "Imported from CSV (OTO)")

            if is_dual:
                results.append({"developer_slug": dev_slug, "investment_slug": rp_slug, "result": rp_result})
                results.append({"developer_slug": dev_slug, "investment_slug": oto_slug, "result": oto_result})
            else:
                single = rp_result or oto_result
                results.append({"developer_slug": dev_slug, "investment_slug": inv_slug, "result": single})

            rows_processed += 1

    logger.info(f"import_csv: processed {rows_processed} rows, {len(results)} results (dry_run={dry_run})")
    return results



def audit_dual(csv_path) -> dict:
    """Scan USImaster.csv and report dual-portal records (read-only).

    Returns a dict with counts and breakdowns useful before a split_dual rollout.
    """
    csv_path = Path(csv_path)
    if not csv_path.exists():
        return {}

    total_rows = 0
    dual_url = 0
    dual_importable = 0
    by_developer: dict = {}
    no_oto_id: list = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_rows += 1
            has_rynek = bool(row.get("strona_rynek", "").strip())
            has_otodom_url = bool(row.get("strona_otodom", "").strip())
            if not (has_rynek and has_otodom_url):
                continue
            dual_url += 1
            has_rp_json = row.get("rpJSON", "").strip().startswith("{")
            has_oto_json = row.get("otoJSON", "").strip().startswith("{")
            if has_rp_json and has_oto_json:
                dual_importable += 1
                dev = row.get("Deweloper", "").strip()
                by_developer[dev] = by_developer.get(dev, 0) + 1
                if not row.get("otoID", "").strip():
                    no_oto_id.append(row.get("USIfolder", ""))

    top10 = sorted(by_developer.items(), key=lambda x: x[1], reverse=True)[:10]

    return {
        "total_rows": total_rows,
        "dual_url": dual_url,
        "dual_importable": dual_importable,
        "by_developer_top10": top10,
        "no_oto_id": no_oto_id,
    }


def migrate_dual(usi_data_dir, dry_run=True) -> list:
    """Rename app_result_imported.json → app_result_imported_rp.json in investment
    folders that have both rp_details.json and oto_details.json (i.e. dual-portal
    records imported before split_dual existed).

    Returns list of action dicts. When dry_run=True, no files are modified.
    Run with dry_run=False only after verifying the dry-run report.
    """
    from datetime import datetime
    usi_data_dir = Path(usi_data_dir)
    actions = []

    for result_file in sorted(usi_data_dir.rglob("app_result_imported.json")):
        inv_dir = result_file.parent
        if not (inv_dir / "rp_details.json").exists():
            continue
        if not (inv_dir / "oto_details.json").exists():
            continue

        try:
            with open(result_file, encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, OSError):
            logger.warning(f"Could not read {result_file}, skipping")
            continue

        source = existing.get("source", "")
        if source == "rynekpierwotny.pl":
            new_name = "app_result_imported_rp.json"
        elif source == "otodom.pl":
            new_name = "app_result_imported_oto.json"
        else:
            logger.warning(f"Unknown source '{source}' in {result_file}, skipping")
            continue

        action = {
            "folder": str(inv_dir),
            "old_file": "app_result_imported.json",
            "new_file": new_name,
            "source": source,
        }

        if not dry_run:
            result_file.rename(inv_dir / new_name)
            log_path = inv_dir / f"processing_log_{inv_dir.name}.txt"
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(
                    f"[{datetime.now().isoformat()}] {inv_dir.parent.name}/{inv_dir.name} - migrate_dual: "
                    f"renamed app_result_imported.json → {new_name}\n"
                )
            logger.info(f"Renamed {result_file} → {inv_dir / new_name}")

        actions.append(action)

    logger.info(f"migrate_dual: {'(dry-run) would rename' if dry_run else 'renamed'} {len(actions)} files")
    return actions
