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
from python_worker.main import update_investment, download_raw_json
from python_worker.scraper_rp import discover_rp_investments
from python_worker.scraper_otodom import discover_otodom_investments
from python_worker.scraper_to import discover_to_investments
from python_worker.url_parser import parse_url
from python_worker.logger_utils import log_to_processing_log

class JobManager:
    def __init__(self):
        self.jobs = {}
        self.lock = threading.Lock()

    def start_job(self, name, target_func, *args, **kwargs):
        job_id = f"job_{int(time.time())}_{len(self.jobs)}"
        self.jobs[job_id] = {
            "id": job_id,
            "name": name,
            "status": "running",
            "progress": 0,
            "total": 100,
            "message": "Initializing...",
            "started_at": datetime.now().isoformat(),
            "finished_at": None,
            "error": None
        }
        
        def wrapper():
            try:
                target_func(job_id, *args, **kwargs)
                with self.lock:
                    self.jobs[job_id]["status"] = "completed"
                    self.jobs[job_id]["progress"] = self.jobs[job_id]["total"]
                    self.jobs[job_id]["message"] = "Finished successfully."
                    self.jobs[job_id]["finished_at"] = datetime.now().isoformat()
            except Exception as e:
                logger.error(f"Job {job_id} failed: {e}")
                with self.lock:
                    self.jobs[job_id]["status"] = "failed"
                    self.jobs[job_id]["error"] = str(e)
                    self.jobs[job_id]["finished_at"] = datetime.now().isoformat()

        threading.Thread(target=wrapper, daemon=True).start()
        return job_id

    def update_progress(self, job_id, progress, message=None, total=None):
        with self.lock:
            if job_id in self.jobs:
                if progress is not None: self.jobs[job_id]["progress"] = progress
                if message is not None: self.jobs[job_id]["message"] = message
                if total is not None: self.jobs[job_id]["total"] = total

    def get_job(self, job_id):
        return self.jobs.get(job_id)

    def list_active_jobs(self):
        return [j for j in self.jobs.values() if j["status"] == "running"]

job_manager = JobManager()
import time

logger = logging.getLogger(__name__)

UI_DIR = Path(__file__).parent / "ui"
UI_PORT = int(os.environ.get("USI_PORT", 5000))
VISIBLE_METADATA_FILE = Path(__file__).parent / "data" / "visible_metadata.json"
REPORTS_DIR = Path(USI_DATA_DIR) / "reports"

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


@app.route("/api/ui-error", methods=["POST"])
def log_ui_error():
    payload = request.get_json(silent=True) or {}
    msg = payload.get("message", "Unknown error")
    stack = payload.get("stack", "No stack trace")
    url = payload.get("url", "Unknown URL")
    
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "ui_errors.log"
    
    ts = datetime.now().isoformat()
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"--- UI ERROR at {ts} ---\n")
        f.write(f"URL: {url}\n")
        f.write(f"Message: {msg}\n")
        f.write(f"Stack:\n{stack}\n")
        f.write("-" * 40 + "\n")
        
    logger.error(f"UI Error captured: {msg}")
    return jsonify({"ok": True})


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

@app.route("/api/download-raw/<dev_slug>/<inv_slug>", methods=["POST"])
def download_raw_route(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    usi_file = inv_dir / f"usi_{inv_slug}.json"
    if not usi_file.exists():
        abort(404)
        
    try:
        with open(usi_file, "r") as f:
            data = json.load(f)
            sources = data.get("sources", {})
            
        success = False
        portals_to_try = ["rp", "oto", "to"]
        for p in portals_to_try:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier:
                    if download_raw_json(p, identifier, dev_slug, inv_slug):
                        success = True
        
        if success:
            return jsonify({"ok": True})
        else:
            return jsonify({"ok": False, "error": "No valid sources for raw download"}), 400
    except Exception as e:
        logger.error(f"UI Download-raw error: {e}")
        return jsonify({"ok": False, "error": str(e)}), 500

@app.route("/api/developers")
def list_developers():
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    
    developers = dm.list_developers()
    # Sort by name
    developers.sort(key=lambda x: x.get("name", "").lower())
    
    # Optional: enrichment with investment counts if needed by UI
    for dev in developers:
        dev_slug = dev["developer_slug"]
        dev_dir = Path(USI_DATA_DIR) / dev_slug
        if dev_dir.exists():
            dev["investments_count"] = sum(1 for d in dev_dir.iterdir() if d.is_dir())
        else:
            dev["investments_count"] = 0
            
    return jsonify(developers)


@app.route("/api/developer/<dev_slug>")
def get_developer_detail(dev_slug):
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    
    dev = dm.get_developer(dev_slug)
    if not dev:
        abort(404)
        
    # Enrich with investments
    investments = []
    dev_dir = Path(USI_DATA_DIR) / dev_slug
    if dev_dir.exists():
        for inv_dir in dev_dir.iterdir():
            if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                inv = _load_investment(dev_slug, inv_dir.name)
                if inv:
                    investments.append(inv)
    
    dev["investments"] = investments
    return jsonify(dev)


@app.route("/api/developer/<dev_slug>/merge", methods=["POST"])
def merge_developer(dev_slug):
    payload = request.get_json() or {}
    source_slug = payload.get("source_slug")
    if not source_slug:
        abort(400, "Missing source_slug")
        
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    
    if dm.merge_developers(dev_slug, source_slug):
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False, "error": "Merge failed"}), 500


@app.route("/api/developer/<dev_slug>/dismiss-suggestion", methods=["POST"])
def dismiss_suggestion(dev_slug):
    payload = request.get_json() or {}
    suggested_id = payload.get("usi_dev_id")
    if not suggested_id:
        abort(400, "Missing usi_dev_id")
        
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    
    if dm.dismiss_suggestion(dev_slug, suggested_id):
        return jsonify({"ok": True})
    else:
        return jsonify({"ok": False}), 500


def run_discovery_job(job_id, dev_slug):
    from python_worker.developer_manager import DeveloperManager
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    dev = dm.get_developer(dev_slug)
    if not dev: return
    
    mapping = dev.get("portal_mapping", {})
    job_manager.update_progress(job_id, 10, "Starting discovery...")
    
    found_total = 0
    
    # 1. RP
    rp_map = mapping.get("rp") or {}
    rp_id = rp_map.get("id") or rp_map.get("slug")
    if rp_id:
        job_manager.update_progress(job_id, 20, f"Scanning RynekPierwotny ({rp_id})...")
        try:
            res = discover_rp_investments(rp_id)
            found_total += len(res)
        except Exception as e:
            logger.error(f"RP discovery failed: {e}")

    # 2. Otodom
    oto_map = mapping.get("oto") or {}
    oto_url = oto_map.get("url")
    if oto_url:
        job_manager.update_progress(job_id, 50, f"Scanning Otodom...")
        try:
            from python_worker.scraper_otodom import discover_otodom_investments
            parsed = parse_url(oto_url)
            if parsed.get("agency_id"):
                res = discover_otodom_investments(parsed["agency_id"])
                found_total += len(res)
        except Exception as e:
            logger.error(f"Otodom discovery failed: {e}")

    # 3. TO
    to_map = mapping.get("to") or {}
    to_slug = to_map.get("slug")
    if to_slug:
        job_manager.update_progress(job_id, 80, f"Scanning TabelaOfert...")
        try:
            res = discover_to_investments(to_slug)
            found_total += len(res)
        except Exception as e:
            logger.error(f"TO discovery failed: {e}")

    job_manager.update_progress(job_id, 100, f"Finished. Found {found_total} potential investments.")


@app.route("/api/developer/<dev_slug>/discover", methods=["POST"])
def discover_dev_new(dev_slug):
    job_id = job_manager.start_job(f"Discovery: {dev_slug}", run_discovery_job, dev_slug)
    return jsonify({"ok": True, "job_id": job_id})


@app.route("/api/discovery/<portal>")
def discovery(portal):
        identifier = request.args.get("id", "").strip()
        
        # RP, Otodom and TabelaOfert support global discovery without ID
        if not identifier and portal not in ("rp", "oto", "to"):
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
                results = discover_rp_investments(identifier if identifier else None)
                from .portal_matcher import filter_new_investments
                results = filter_new_investments(results, "rp")
            elif portal == "oto":
                from .scraper_otodom import discover_otodom_investments, discover_otodom_listing
                from .config import OTODOM_DISCOVERY_URLS

                if identifier:
                    results = discover_otodom_investments(identifier)
                else:
                    # Global discovery for Otodom - scan all configured URLs
                    results = []
                    seen_slugs = set()
                    for url in OTODOM_DISCOVERY_URLS:
                        try:
                            batch = discover_otodom_listing(url)
                            for item in batch:
                                if item["slug"] not in seen_slugs:
                                    results.append(item)
                                    seen_slugs.add(item["slug"])
                        except Exception as e:
                            logger.warning(f"Failed global discovery for {url}: {e}")
                
                from .portal_matcher import filter_new_investments
                results = filter_new_investments(results, "otodom")
            elif portal == "to":
                from .scraper_to import discover_to_investments
                results = discover_to_investments(identifier if identifier else None)
                from .portal_matcher import filter_new_investments
                results = filter_new_investments(results, "to")
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


@app.route("/api/reports")
def list_reports():
    reports = []
    if not REPORTS_DIR.exists():
        return jsonify([])
    for f in sorted(REPORTS_DIR.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            reports.append({
                "id": data.get("id", f.stem),
                "title": data.get("title", f.stem),
                "description": data.get("description", "")
            })
        except Exception as e:
            logger.error(f"Error reading report {f}: {e}")
    return jsonify(reports)


@app.route("/api/report/<report_id>/data")
def get_report_data(report_id):
    report_file = REPORTS_DIR / f"{report_id}.json"
    if not report_file.exists():
        abort(404)
    
    try:
        report_def = json.loads(report_file.read_text(encoding="utf-8"))
        filters = report_def.get("filters", {})
        
        investments = []
        data_root = Path(USI_DATA_DIR)
        for dev_dir in data_root.iterdir():
            if not dev_dir.is_dir() or dev_dir.name == "reports": continue
            for inv_dir in dev_dir.iterdir():
                if not inv_dir.is_dir(): continue
                inv = _load_investment(dev_dir.name, inv_dir.name)
                if inv:
                    match = True
                    if "city" in filters:
                        city = filters["city"].lower()
                        addr = (inv.get("address") or "").lower()
                        # Proste sprawdzenie czy miasto jest w adresie lub dystrykcie
                        distr = (inv.get("district") or "").lower()
                        if city not in addr and city not in distr: 
                            match = False
                    
                    if match and "developer_slug" in filters:
                        if inv.get("developer_slug") != filters["developer_slug"]: 
                            match = False
                        
                    if match and "min_rating" in filters:
                        score = _calculate_ocena_log(inv.get("ratings", {}))
                        if score is None or score < filters["min_rating"]: 
                            match = False
                    
                    # Filtry geograficzne (odległość od punktu)
                    if match and "near" in filters:
                        center = filters["near"].get("coords") # [lat, lng]
                        radius = filters["near"].get("radius", 5) # km
                        if center and inv.get("coords"):
                            # Korzystamy z uproszczonej formuly Pitagorasa dla malych odleglosci lub Haversine
                            # Tutaj dla prostoty uzyjemy tej samej co w UI (Haversine)
                            dist = _calculate_distance(center[0], center[1], inv["coords"][0], inv["coords"][1])
                            if dist > radius:
                                match = False

                    if match:
                        investments.append(inv)
        
        return jsonify({
            "definition": report_def,
            "data": investments
        })
    except Exception as e:
        logger.error(f"Error processing report {report_id}: {e}")
        return jsonify({"error": str(e)}), 500


def _calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@app.route("/api/fetch-status")
def fetch_status():
    """Zwraca ile inwestycji jest już w bazie (na podstawie nowych folderów)."""
    data_root = Path(USI_DATA_DIR)
    count = sum(
        1 for dev in data_root.iterdir() if dev.is_dir()
        for inv in dev.iterdir() if inv.is_dir() and list(inv.glob("usi_*.json"))
    ) if data_root.exists() else 0
    return jsonify({"count": count})


@app.route("/api/jobs")
def list_jobs():
    return jsonify(job_manager.list_active_jobs())


@app.route("/api/jobs/<job_id>")
def get_job_status(job_id):
    job = job_manager.get_job(job_id)
    if not job:
        abort(404)
    return jsonify(job)


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
