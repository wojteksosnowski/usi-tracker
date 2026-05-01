import csv
import json
import logging
import re
import shutil
import unicodedata
from pathlib import Path
from .stage_detector import extract_groups_id, extract_stages

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


def extract_developer_slug(row: dict) -> str:
    # PRIORYTET 1: Zawsze bierzemy nazwę od użytkownika (Coda) z kolumny "Deweloper"
    dev_name = row.get("Deweloper", "").strip()
    if dev_name:
        return slugify(dev_name)

    # PRIORYTET 2: Z imgList (tylko jako ostateczność, gdy brakuje w CSV)
    imglist = row.get("imgList", "").strip()
    if imglist:
        paths = parse_imglist(imglist)
        if paths:
            parts = paths[0].split("/")
            if len(parts) >= 4 and parts[1] == "Public" and parts[2] == "USI":
                return parts[3]

    # PRIORYTET 3: Ze zrzutu JSON portalu (najmniej wiarygodne np. "Platforma Mieszkaniowa")
    rp_raw = row.get("rpJSON", "").strip()
    if rp_raw.startswith("{"):
        try:
            rp = json.loads(rp_raw)
            vendor = rp.get("vendor", {})
            if isinstance(vendor, dict) and "value" in vendor:
                vendor = vendor["value"]
            slug = vendor.get("slug", "") if isinstance(vendor, dict) else ""
            if slug:
                return slug
        except (json.JSONDecodeError, AttributeError):
            pass

    return "unknown"


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


def build_rp_result(row: dict, investment_slug: str = None) -> dict:
    rp_raw = row.get("rpJSON", "").strip()
    rp = json.loads(rp_raw) if rp_raw.startswith("{") else {}

    developer_slug = extract_developer_slug(row)
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

    image_paths_raw = parse_imglist(row.get("imgList", ""))
    image_paths = [f"/Public/USI/{developer_slug}/{investment_slug}/{Path(p).name}" for p in image_paths_raw]

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

    return {
        "source": "rynekpierwotny.pl",
        "id": offer_id,
        "url": row.get("strona_rynek", "").strip(),
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": f"/Public/USI/{developer_slug}/{investment_slug}/",
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


def build_oto_result(row: dict, investment_slug: str = None) -> dict:
    oto_raw = row.get("otoJSON", "").strip()
    page_props = json.loads(oto_raw) if oto_raw.startswith("{") else {}
    ad_data = page_props.get("ad", {})

    developer_slug = extract_developer_slug(row)
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
    image_paths_raw = parse_imglist(row.get("imgList", ""))
    image_paths = [f"/Public/USI/{developer_slug}/{investment_slug}/{Path(p).name}" for p in image_paths_raw]

    return {
        "source": "otodom.pl",
        "url": row.get("strona_otodom", "").strip(),
        "developer_slug": developer_slug,
        "investment_slug": investment_slug,
        "usi_folder_path": f"/Public/USI/{developer_slug}/{investment_slug}/",
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
    app_result files: app_result_imported_rp.json and app_result_imported_oto.json.
    Single-portal rows always produce app_result_imported.json (unchanged behaviour).
    """
    csv_path = Path(csv_path)
    output_dir = Path(output_dir)

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
            if inv_slug in seen_folders:
                oto_id = row.get("otoID", "").strip()
                logger.warning(
                    f"Duplicate USIfolder '{inv_slug}' (otoID={oto_id!r} → Otodom zmienił ID). "
                    f"Poprzedni rekord zostanie nadpisany."
                )
            seen_folders[inv_slug] = True

            has_rp = row.get("rpJSON", "").strip().startswith("{")
            has_oto = row.get("otoJSON", "").strip().startswith("{")

            if not has_rp and not has_oto:
                continue

            try:
                is_dual = split_dual and has_rp and has_oto
                if is_dual:
                    # Wyciągamy natywne slugi zamiast doklejać -oto
                    rp_slug, oto_slug = extract_native_slugs(row)
                    
                    # Jeśli slugi są identyczne (kolizja), musimy je rozróżnić, 
                    # ale zgodnie z planem zakładamy, że natywne slugi portalowe zazwyczaj się różnią.
                    if rp_slug == oto_slug:
                        oto_slug = f"{oto_slug}-oto" # Jedyny przypadek kolizji
                    
                    rp_result = build_rp_result(row, investment_slug=rp_slug)
                    oto_result = build_oto_result(row, investment_slug=oto_slug)
                elif has_rp:
                    rp_result = build_rp_result(row)
                    oto_result = None
                else:
                    rp_result = None
                    oto_result = build_oto_result(row)
            except Exception as e:
                logger.warning(f"Skipping {inv_slug}: {e}")
                continue

            dev_slug = (rp_result or oto_result)["developer_slug"]

            if not dry_run:
                if is_dual:
                    # Create two separate directories (DATA)
                    inv_dir_rp = output_dir / dev_slug / rp_slug
                    inv_dir_oto = output_dir / dev_slug / oto_slug
                    inv_dir_rp.mkdir(parents=True, exist_ok=True)
                    inv_dir_oto.mkdir(parents=True, exist_ok=True)

                    # Create two separate directories (IMAGES - SYMMETRY)
                    # Zakładamy, że Public/USI jest w tej samej strukturze co Public/USIdata
                    # (wyjście poziom wyżej z Public/USIdata do Public/ i potem do USI/)
                    usi_base = output_dir.parent / "USI"
                    usi_dir_rp = usi_base / dev_slug / rp_slug
                    usi_dir_oto = usi_base / dev_slug / oto_slug
                    usi_dir_rp.mkdir(parents=True, exist_ok=True)
                    usi_dir_oto.mkdir(parents=True, exist_ok=True)

                    # Kopiowanie/Synchronizacja zdjęć ze starego USIfolder (jeśli wskazany w CSV)
                    # aby oba nowe foldery miały dostęp do pobranych wcześniej zasobów.
                    usi_folder_raw = row.get("USIfolder", "")
                    if usi_folder_raw:
                        old_usi_folder = usi_base / usi_folder_raw
                        if old_usi_folder.exists() and old_usi_folder.is_dir():
                            for img_file in old_usi_folder.glob("*"):
                                if img_file.is_file():
                                    # Kopiujemy tylko jeśli ścieżka docelowa jest inna niż źródłowa
                                    dst_rp = usi_dir_rp / img_file.name
                                    if old_usi_folder != usi_dir_rp:
                                        shutil.copy2(img_file, dst_rp)
                                    
                                    dst_oto = usi_dir_oto / img_file.name
                                    if old_usi_folder != usi_dir_oto:
                                        shutil.copy2(img_file, dst_oto)
                        else:
                            # Fallback do obecnej logiki (jeśli USIfolder nie podano lub nie istnieje)
                            fallback_old = usi_base / dev_slug / inv_slug
                            if fallback_old.exists() and fallback_old.is_dir():
                                for img_file in fallback_old.glob("*"):
                                    if img_file.is_file():
                                        if fallback_old != usi_dir_rp:
                                            shutil.copy2(img_file, usi_dir_rp / img_file.name)
                                        if fallback_old != usi_dir_oto:
                                            shutil.copy2(img_file, usi_dir_oto / img_file.name)

                    rp_raw = row.get("rpJSON", "").strip()
                    with open(inv_dir_rp / "rp_details.json", "w", encoding="utf-8") as out:
                        out.write(rp_raw)
                    
                    oto_raw = row.get("otoJSON", "").strip()
                    with open(inv_dir_oto / "oto_details.json", "w", encoding="utf-8") as out:
                        out.write(oto_raw)

                    with open(inv_dir_rp / "app_result_imported.json", "w", encoding="utf-8") as out:
                        json.dump(rp_result, out, indent=4, ensure_ascii=False)
                    
                    with open(inv_dir_oto / "app_result_imported.json", "w", encoding="utf-8") as out:
                        json.dump(oto_result, out, indent=4, ensure_ascii=False)
                else:
                    inv_dir = output_dir / dev_slug / inv_slug
                    inv_dir.mkdir(parents=True, exist_ok=True)

                    rp_raw = row.get("rpJSON", "").strip()
                    if rp_raw.startswith("{"):
                        rp_path = inv_dir / "rp_details.json"
                        with open(rp_path, "w", encoding="utf-8") as out:
                            out.write(rp_raw)
                        logger.info(f"Wrote {rp_path}")

                    oto_raw = row.get("otoJSON", "").strip()
                    if oto_raw.startswith("{"):
                        oto_path = inv_dir / "oto_details.json"
                        with open(oto_path, "w", encoding="utf-8") as out:
                            out.write(oto_raw)
                        logger.info(f"Wrote {oto_path}")

                    single = rp_result or oto_result
                    result_path = inv_dir / "app_result_imported.json"
                    with open(result_path, "w", encoding="utf-8") as out:
                        json.dump(single, out, indent=4, ensure_ascii=False)
                    logger.info(f"Wrote {result_path}")

            if is_dual:
                results.append({"developer_slug": dev_slug, "investment_slug": inv_slug, "result": rp_result})
                results.append({"developer_slug": dev_slug, "investment_slug": inv_slug, "result": oto_result})
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
            log_path = inv_dir / "processing_log.txt"
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(
                    f"[{datetime.now().isoformat()}] migrate_dual: "
                    f"renamed app_result_imported.json → {new_name}\n"
                )
            logger.info(f"Renamed {result_file} → {inv_dir / new_name}")

        actions.append(action)

    logger.info(f"migrate_dual: {'(dry-run) would rename' if dry_run else 'renamed'} {len(actions)} files")
    return actions
