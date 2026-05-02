"""
USI Tracker — lokalny interfejs webowy (Odchudzony).
Uruchomienie:  python3 -m python_worker.main ui
"""
import csv as _csv
import json
import logging
import os
import re
import threading
import math
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import requests as req
from flask import Flask, abort, jsonify, request, send_file, send_from_directory

from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR, HERE_API_KEY
from python_worker.here_maps import build_here_url
from python_worker.main import update_investment
from python_worker.scraper_rp import discover_rp_investments
from python_worker.scraper_otodom import discover_otodom_investments
from python_worker.scraper_to import discover_to_investments
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).parent / "ui"
UI_PORT = int(os.environ.get("USI_PORT", 5000))
VISIBLE_METADATA_FILE = Path(__file__).parent / "data" / "visible_metadata.json"

app = Flask(__name__, static_folder=None)

USI_STATUSES = ['Brak', 'AI', 'Wstępna', 'Poszerzona', 'Pełna', 'Aktualizacja', 'Ukończona']
_WYROZNIKI_CSV = Path(__file__).parent / "data" / "wyrozniki.csv"
_STANDARD_TIERS = [(16, 4), (8, 3), (4, 2), (1, 1), (0, 0)]
_CATS = ['Balkony', 'Fasady', 'Wnętrza', 'Teren', 'Mieszkania', 'Udogodnienia']


@app.route("/api/config")
def get_config():
    return jsonify({
        "hereApiKey": HERE_API_KEY
    })


@app.route("/api/metadata-config")
def get_metadata_config():
    if VISIBLE_METADATA_FILE.exists():
        return send_file(VISIBLE_METADATA_FILE)
    # Default fallback
    return jsonify([
        {"key": "address", "label": "Adres", "path": "address", "type": "string"},
        {"key": "units", "label": "Mieszkania", "path": "units", "type": "number"},
        {"key": "delivery", "label": "Termin", "path": "delivery", "type": "string"},
        {"key": "price_avg", "label": "Cena śr.", "path": "price_avg", "type": "currency"},
        {"key": "photos", "label": "Zdjęcia", "path": "photos.length", "type": "count"}
    ])


def _calculate_ocena_log(ratings: dict) -> float | None:
    vals = [ratings.get(cat) for cat in _CATS if ratings.get(cat) is not None]
    if not vals:
        return None
    try:
        sum_exp = sum(math.exp(v) for v in vals)
        return math.log(sum_exp) - math.log(len(vals))
    except (ValueError, OverflowError):
        return None


@lru_cache(maxsize=1)
def _load_wyrozniki():
    """Load wyrozniki.csv → (rp_facilities dict, wyrozniki_udo list)."""
    rp_fac = {}
    wyrozniki_udo = []
    if not _WYROZNIKI_CSV.exists():
        return rp_fac, wyrozniki_udo
    with open(_WYROZNIKI_CSV, encoding="utf-8") as f:
        for row in _csv.DictReader(f):
            label = row.get("HMLabel", "").strip()
            if not label: continue
            rpno_str = row.get("rpNo", "").strip()
            try:
                hm_udo = int(row.get("HMUdogodnienia", "").strip() or "0")
            except ValueError:
                hm_udo = 0
            rpno = int(rpno_str) if rpno_str else None
            if rpno is not None:
                rp_fac[rpno] = label
            if hm_udo > 0:
                wyrozniki_udo.append((label, rpno, hm_udo))
    return rp_fac, wyrozniki_udo


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

# ── Static files ───────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(UI_DIR, "index.html")

@app.route("/<path:filename>")
def ui_static(filename):
    safe = _safe_path(UI_DIR, filename)
    if safe is None or not safe.exists():
        abort(404)
    return send_file(safe)

# ── Image API ──────────────────────────────────────────────────────────────────

@app.route("/api/image/<dev_slug>/<inv_slug>/<filename>")
def serve_image(dev_slug, inv_slug, filename):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug) or not _valid_filename(filename):
        abort(400)
    img_path = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug / filename
    if not img_path.exists():
        abort(404)
    return send_file(img_path)

# ── Data API ───────────────────────────────────────────────────────────────────

@app.route("/api/investments")
def list_investments():
    investments = []
    data_root = Path(USI_DATA_DIR)
    if not data_root.exists():
        return jsonify([])

    for dev_dir in sorted(data_root.iterdir()):
        if not dev_dir.is_dir(): continue
        for inv_dir in sorted(dev_dir.iterdir()):
            if not inv_dir.is_dir(): continue
            inv = _load_investment(dev_dir.name, inv_dir.name)
            if inv: investments.append(inv)
    return jsonify(investments)


@app.route("/api/data/<dev_slug>/<inv_slug>")
def investment_data(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    inv = _load_investment(dev_slug, inv_slug)
    if inv is None:
        abort(404)
    return jsonify(inv)


@app.route("/api/ratings/<dev_slug>/<inv_slug>", methods=["POST"])
def save_ratings(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    payload = request.get_json(silent=True) or {}
    
    # Zapis ocen uaktualnia teraz bezposrednio meta_{slug}_ratings.json lub usi_{slug}.json
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    if not inv_dir.exists():
        abort(404)
        
    ratings_file = inv_dir / f"meta_{inv_slug}_ratings.json"
    existing_ratings = {}
    if ratings_file.exists():
        try:
            existing_ratings = json.loads(ratings_file.read_text())
        except:
            pass

    changes = []
    for cat in _CATS:
        if cat in payload:
            val = payload[cat]
            if val is not None:
                if not isinstance(val, (int, float)) or not (0 <= val <= 4):
                    abort(400, f"Invalid value for {cat}")
                new_val = float(val)
            else:
                new_val = None
            
            if existing_ratings.get(cat) != new_val:
                changes.append({"field": f"ratings.{cat}", "old": existing_ratings.get(cat), "new": new_val})
                existing_ratings[cat] = new_val

    if "komentarz" in payload:
        new_kom = str(payload["komentarz"])
        if existing_ratings.get("komentarz") != new_kom:
            existing_ratings["komentarz"] = new_kom
            
    if "status" in payload:
        new_status = payload["status"]
        if new_status not in USI_STATUSES:
            abort(400, f"Invalid status: {new_status}")
        if existing_ratings.get("status") != new_status:
            changes.append({"field": "status", "old": existing_ratings.get("status"), "new": new_status})
            existing_ratings["status"] = new_status
        
    # Aktualizuj plik zunifikowany, jeśli istnieje, żeby UI od razu to widziało
    usi_file = inv_dir / f"usi_{inv_slug}.json"
    if usi_file.exists():
        try:
            usi_data = json.loads(usi_file.read_text())
            old_score = _calculate_ocena_log(usi_data.get("ratings", {}))
            
            usi_data["ratings"] = {**usi_data.get("ratings", {}), **existing_ratings}
            usi_data["status"] = existing_ratings.get("status", usi_data.get("status", "Brak"))
            
            new_score = _calculate_ocena_log(usi_data["ratings"])
            if old_score != new_score and new_score is not None:
                changes.append({"field": "ratings_score", "old": old_score, "new": new_score})

            audit = usi_data.setdefault("audit", {})
            if "created_at" not in audit:
                audit["created_at"] = datetime.now().isoformat()
            audit["updated_at"] = datetime.now().isoformat()
            
            if changes:
                history = audit.setdefault("history", [])
                history.append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "Rating Updated",
                    "changes": changes
                })
                log_to_processing_log(dev_slug, inv_slug, f"Ratings updated via UI. Changes: {len(changes)}")
                
            usi_file.write_text(json.dumps(usi_data, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"Failed to update USI unified file: {e}")

    ratings_file.write_text(json.dumps(existing_ratings, ensure_ascii=False, indent=2))
    return jsonify({"ok": True})


@app.route("/api/mark-delete/<dev_slug>/<inv_slug>", methods=["POST"])
def save_deletion_list(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        abort(400, "paths must be a list")
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    if not inv_dir.exists():
        abort(404)
    out = {"paths": paths, "updated_at": datetime.now().isoformat(timespec="seconds")}
    (inv_dir / "deletion_list.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    log_to_processing_log(dev_slug, inv_slug, f"Updated deletion list for photos. Count: {len(paths)}")
    return jsonify({"ok": True, "count": len(paths)})

@app.route("/api/reload-investment/<dev_slug>/<inv_slug>", methods=["POST"])
def reload_investment(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    
    logger.info(f"UI Trigger: Reloading investment {dev_slug}/{inv_slug}")
    success = update_investment(dev_slug, inv_slug)
    
    if not success:
        return jsonify({"ok": False, "error": "Failed to update investment from source"}), 500
        
    updated_inv = _load_investment(dev_slug, inv_slug)
    if not updated_inv:
        return jsonify({"ok": False, "error": "Failed to load updated investment"}), 404
        
    return jsonify({"ok": True, "investment": updated_inv})

@app.route("/api/developers")
def list_developers():
    data_root = Path(USI_DATA_DIR)
    if not data_root.exists():
        return jsonify([])
    devs = sorted([d.name for d in data_root.iterdir() if d.is_dir() and not d.name.startswith(".")])
    return jsonify(devs)


@app.route("/api/discovery/<portal>")
def discovery(portal):
        identifier = request.args.get("id", "").strip()
        if not identifier:
            return jsonify({"error": "Missing 'id' parameter"}), 400

        # Check if identifier is a URL
        parsed = None
        if identifier.startswith("http"):
            parsed = parse_url(identifier)
            if parsed["type"] == "unknown":
                return jsonify({"error": "Unknown or unsupported URL"}), 400

            # Override portal from URL if needed, but usually we respect the selected portal
            # unless it is obvious. For now, let is use the parsed data.
            if parsed["kind"] == "investment":
                # Direct investment registration suggested
                return jsonify([{
                    "id": parsed.get("offer_id") or parsed.get("to_id"),
                    "name": f"Wykryto inwestycję: {parsed.get('investment_slug', 'bez nazwy')}",
                    "slug": parsed.get("investment_slug"),
                    "url": parsed.get("url"),
                    "kind": "single"
                }])

            # For developer profiles, extract the ID/slug
            if parsed["type"] == "rynekpierwotny":
                identifier = parsed["developer_slug"]
            elif parsed["type"] == "otodom":
                identifier = parsed["agency_id"]
            elif parsed["type"] == "tabelaofert":
                identifier = parsed["developer_slug"]

        try:
            if portal == "rp":
                results = discover_rp_investments(identifier)
            elif portal == "oto":
                results = discover_otodom_investments(identifier)
            elif portal == "to":
                results = discover_to_investments(identifier)
            else:
                return jsonify({"error": f"Unsupported portal: {portal}"}), 400

            return jsonify(results)
        except Exception as e:
            logger.error(f"Discovery error for {portal}: {e}")
            return jsonify({"error": str(e)}), 500


@app.route("/api/register", methods=["POST"])
def register():
    payload = request.get_json()
    portal = payload.get("portal")
    dev_slug = payload.get("dev_slug")
    inv_slug = payload.get("inv_slug")
    name = payload.get("name")
    item_id = payload.get("id")
    url = payload.get("url")

    if not all([portal, dev_slug, inv_slug, name]):
        return jsonify({"error": "Missing parameters"}), 400

    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    usi_path = inv_dir / f"usi_{inv_slug}.json"

    if usi_path.exists():
        return jsonify({"error": "Investment already exists"}), 409

    inv_dir.mkdir(parents=True, exist_ok=True)

    sources = {}
    if portal == "rp":
        sources["rp"] = {"id": item_id, "url": url}
    elif portal == "oto":
        sources["oto"] = {"url": url}
    elif portal == "to":
        sources["to"] = {"url": url}

    skeleton = {
        "investment_slug": inv_slug,
        "developer_slug": dev_slug,
        "name": name,
        "sources": sources,
        "status": "Brak",
        "audit": {"created_at": datetime.now().isoformat()}
    }

    try:
        with open(usi_path, "w", encoding="utf-8") as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)
        
        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        
        # Trigger immediate update to fetch all data
        # We pass slugs to ensure scraper knows where to save
        success = update_investment(dev_slug, inv_slug)
        
        return jsonify({"ok": True, "updated": success})
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/fetch-status")
def fetch_status():
    """Zwraca ile inwestycji jest już w bazie (na podstawie nowych folderów)."""
    data_root = Path(USI_DATA_DIR)
    count = sum(
        1 for dev in data_root.iterdir() if dev.is_dir()
        for inv in dev.iterdir() if inv.is_dir() and list(inv.glob("usi_*.json"))
    ) if data_root.exists() else 0
    return jsonify({"count": count})


# ── Data normalization ─────────────────────────────────────────────────────────

def _load_investment(dev_slug: str, inv_slug: str) -> dict | None:
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    usi_file = inv_dir / f"usi_{inv_slug}.json"
    
    if not usi_file.exists():
        return None
        
    try:
        usi = json.loads(usi_file.read_text())
    except Exception:
        return None

    # Load deletion list for photos
    deletion_file = inv_dir / "deletion_list.json"
    photos_to_delete = 0
    if deletion_file.exists():
        try:
            dl = json.loads(deletion_file.read_text())
            photos_to_delete = len(dl.get("paths", []))
        except Exception:
            pass

    # Read photos
    img_dir = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug
    images = []
    if img_dir.is_dir():
        images = sorted(
            f"/api/image/{dev_slug}/{inv_slug}/{p.name}"
            for p in img_dir.iterdir()
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and not p.name.startswith('.')
        )

    # Compute score dynamically for UI based on unified data
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

    # Default if none found
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

    # Map to old UI flat format
    return {
        "slug": f"{dev_slug}/{inv_slug}",
        "developer_slug": dev_slug,
        "investment_slug": inv_slug,
        "name": usi.get("name", inv_slug.title()),
        "developer": usi.get("developer", dev_slug.title()),
        "address": address,
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


# ── Security helpers ───────────────────────────────────────────────────────────

def _safe_path(base: Path, relative: str) -> Path | None:
    try:
        resolved = (base / relative).resolve()
        if not str(resolved).startswith(str(base.resolve())):
            return None
        return resolved
    except Exception:
        return None

def _valid_slug(s: str) -> bool:
    return bool(s) and bool(re.match(r"^[a-zA-Z0-9_\-]+$", s))

def _valid_filename(s: str) -> bool:
    if ".." in s: return False
    return bool(s) and bool(re.match(r"^[^/\\]+\.(jpg|jpeg|png|webp|svg)$", s, re.IGNORECASE))

def run():
    print(f"USI Tracker UI → http://localhost:{UI_PORT}")
    app.run(host="127.0.0.1", port=UI_PORT, debug=False)

if __name__ == "__main__":
    run()
