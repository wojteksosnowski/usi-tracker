import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort, request, send_file
from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename
import python_worker.investment_index as inv_index

logger = logging.getLogger(__name__)



def _inv_matches_dev(inv: dict, pm: dict) -> bool:
    """Return True only when a portal developer ID from sources exactly matches portal_mapping.
    No fallback guessing — missing ID means no match."""
    src = inv.get("sources") or {}
    for portal in ("rp", "oto", "to"):
        if not pm.get(portal) or not src.get(portal):
            continue
        pm_p = pm[portal]
        src_p = src[portal]
        
        if pm_p.get("_inferred"):
            return True
            
        if portal == "rp":
            pm_id = str(pm_p.get("id", ""))
            src_vid = str(src_p.get("vendor_id", ""))
            if pm_id and src_vid and pm_id == src_vid:
                return True
        elif portal == "oto":
            pm_aids = {str(a) for a in (pm_p.get("agency_ids") or [pm_p.get("agency_id", "")]) if a}
            src_aid = str(src_p.get("agency_id", ""))
            if pm_aids and src_aid and src_aid in pm_aids:
                return True
        elif portal == "to":
            pm_id = str(pm_p.get("id") or pm_p.get("slug", "") or pm_p.get("agency_id", ""))
            src_id = str(src_p.get("developer_id") or "")
            if (pm_id and src_id and pm_id == src_id) or (not pm_id and not src_id):
                return True
    return False


investments_bp = Blueprint('investments', __name__)
investment_service = InvestmentService()

@investments_bp.route("/image/<dev_slug>/<inv_slug>/<filename>")
def serve_image(dev_slug, inv_slug, filename):
    from python_worker.config import PUBLIC_USI_DIR
    from pathlib import Path
    from urllib.parse import quote
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug) or not _valid_filename(filename):
        abort(400)
    
    # 1. Try exact match (decoded by Flask)
    img_path = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug / filename
    if img_path.exists():
        return send_file(img_path)
        
    # 2. Try re-encoding (for files literally named with % on disk)
    encoded_filename = quote(filename)
    # quote() uses uppercase %XX, but some scrapers might use lowercase
    alt_path_upper = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug / encoded_filename
    if alt_path_upper.exists():
        return send_file(alt_path_upper)
        
    alt_path_lower = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug / encoded_filename.lower()
    if alt_path_lower.exists():
        return send_file(alt_path_lower)

    abort(404)

@investments_bp.route("/developer/<dev_slug>/logo")
def serve_dev_logo(dev_slug):
    from python_worker.config import USI_DEV_DIR
    from pathlib import Path
    if not _valid_slug(dev_slug):
        abort(400)
    
    dev_dir = Path(USI_DEV_DIR) / dev_slug
    if not dev_dir.exists():
        abort(404)
        
    # Search for logo.*
    for ext in ['png', 'jpg', 'jpeg', 'webp', 'svg']:
        logo_path = dev_dir / f"logo.{ext}"
        if logo_path.exists():
            return send_file(logo_path)
            
    abort(404)

@investments_bp.route("/investments")
def list_investments():
    data_root = investment_service.data_dir
    if not data_root.exists():
        return jsonify([])

    entries = inv_index.load(data_root)
    investments = entries

    if investments is None:
        # Index missing — build it in background and fall back to full scan this time
        logger.info("Investment index not found; triggering rebuild in background")
        public_usi_dir = investment_service.public_usi_dir
    
        def _rebuild():
            try:
                inv_index.rebuild(data_root, public_usi_dir)
            except Exception as e:
                logger.error(f"Background index rebuild failed: {e}")
    
        import threading
        threading.Thread(target=_rebuild, daemon=True).start()
    
        investments = []
        for dev_dir in sorted(data_root.iterdir()):
            if not dev_dir.is_dir(): continue
            for inv_dir in sorted(dev_dir.iterdir()):
                if not inv_dir.is_dir(): continue
                usi_files = list(inv_dir.glob("usi_*.json"))
                for usi_file in usi_files:
                    parts = usi_file.name.split("_")
                    if len(parts) == 3:
                        portal = parts[1]
                        inv = investment_service.get_investment(dev_dir.name, inv_dir.name, portal=portal)
                    else:
                        inv = investment_service.get_investment(dev_dir.name, inv_dir.name)
                    if inv:
                        investments.append(inv)

    # Server-side filtering
    search = request.args.get("search", "").lower()
    dev = request.args.get("dev", "")
    status = request.args.get("status", "")
    only_unreviewed = request.args.get("onlyUnreviewed") == "true"
    only_no_photos = request.args.get("onlyNoPhotos") == "true"
    sources_arg = request.args.get("sources", "")
    sources = set(sources_arg.upper().split(",")) if sources_arg else set()
    cities_arg = request.args.get("cities", "")
    cities = set(cities_arg.lower().split(",")) if cities_arg else set()

    filtered = []
    unreviewed_count = 0
    main_cities = ['warszawa', 'kraków', 'wrocław', 'łódź', 'poznań', 'gdańsk', 'szczecin', 'bydgoszcz', 'lublin', 'białystok']

    for inv in investments:
        if inv.get("reviewed") is False:
            unreviewed_count += 1
            
        # Hide merged children
        if inv.get("master_id") and inv.get("master_usi_inv_id") and inv.get("usi_inv_id") != inv.get("master_usi_inv_id"):
            continue
            
        if only_unreviewed and inv.get("reviewed") is not False:
            continue
            
        if only_no_photos and inv.get("photos"):
            continue
            
        if search:
            inv_name = (inv.get("name") or "").lower()
            inv_dev = (inv.get("developer") or "").lower()
            inv_dist = (inv.get("district") or "").lower()
            inv_addr = (inv.get("address") or "").lower()
            if search not in inv_name and search not in inv_dev and search not in inv_dist and search not in inv_addr:
                continue
                
        if dev and inv.get("developer_slug") != dev and inv.get("developer") != dev:
            continue
            
        if status and inv.get("status") != status:
            continue
            
        if sources and inv.get("source") and inv.get("source", "").upper() not in sources:
            continue
            
        if cities:
            addr = (inv.get("address") or "").lower()
            found_city = next((c for c in main_cities if c in addr), None)
            if not found_city or found_city not in cities:
                continue
                
        filtered.append(inv)
        
    return jsonify({"data": filtered, "unreviewedCount": unreviewed_count})


@investments_bp.route("/investments/rebuild-index", methods=["POST"])
def rebuild_index():
    data_root = investment_service.data_dir
    public_usi_dir = investment_service.public_usi_dir

    def _run(job_id):
        try:
            job_manager.update_job(job_id, status="running", message="Budowanie indeksu inwestycji...")
            count = inv_index.rebuild(data_root, public_usi_dir)
            job_manager.update_job(job_id, status="done", message=f"Indeks gotowy: {count} inwestycji")
        except Exception as e:
            job_manager.update_job(job_id, status="error", message=str(e))

    job_id = job_manager.create_job("rebuild-index", "Rebuild investment index")
    import threading
    threading.Thread(target=_run, args=(job_id,), daemon=True).start()
    return jsonify({"job_id": job_id})

@investments_bp.route("/data/<dev_slug>/<inv_slug>")
def investment_data(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    inv = investment_service.get_investment(dev_slug, inv_slug)
    if inv is None:
        abort(404)
    return jsonify(inv)

@investments_bp.route("/ratings/<dev_slug>/<inv_slug>", methods=["POST"])
def save_ratings(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    payload = request.get_json(silent=True) or {}
    try:
        if investment_service.save_ratings(dev_slug, inv_slug, payload):
            return jsonify({"ok": True})
        else:
            abort(404)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@investments_bp.route("/mark-delete/<dev_slug>/<inv_slug>", methods=["POST"])
def save_deletion_list(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        abort(400, "paths must be a list")
    if investment_service.mark_deleted_photos(dev_slug, inv_slug, paths):
        return jsonify({"ok": True, "count": len(paths)})
    else:
        abort(404)

@investments_bp.route("/reload-investment/<dev_slug>/<inv_slug>", methods=["POST"])
def reload_investment(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    success = investment_service.update_investment(dev_slug, inv_slug)
    if not success:
        return jsonify({"ok": False, "error": "Failed to update"}), 500
    updated_inv = investment_service.get_investment(dev_slug, inv_slug)
    return jsonify({"ok": True, "investment": updated_inv})

@investments_bp.route("/refresh/<dev_slug>/<inv_slug>", methods=["POST"])
def refresh_investment_route(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    inv = investment_service.get_investment(dev_slug, inv_slug)
    if not inv:
        abort(404)
    
    def run_refresh_job(job_id, d_slug, i_slug, inv_name):
        job_manager.update_progress(job_id, 10, f"Rozpoczęto odświeżanie: {inv_name}")
        try:
            if investment_service.update_investment(d_slug, i_slug):
                job_manager.update_progress(job_id, 100, f"Ukończono odświeżanie: {inv_name}")
            else:
                job_manager.update_progress(job_id, 100, f"Brak danych do odświeżenia: {inv_name}", status="failed")
        except RuntimeError as e:
            logger.error(f"Refresh job failed for {i_slug}: {e}")
            job_manager.update_progress(job_id, 100, str(e), status="failed")
        except Exception as e:
            logger.exception(f"Exception during refresh job for {i_slug}: {e}")
            job_manager.update_progress(job_id, 100, f"Wyjątek: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Refresh: {inv['name']}", run_refresh_job, dev_slug, inv_slug, inv['name'])
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/download-raw/<dev_slug>/<inv_slug>", methods=["POST"])
def download_raw_route(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    from python_worker.config import USI_DATA_DIR
    from python_worker.main import download_raw_json
    from python_worker.api.utils import _find_inv_file
    from pathlib import Path
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    usi_file = _find_inv_file(inv_dir, inv_slug)
    if not usi_file or not usi_file.exists():
        abort(404)
    try:
        with open(usi_file, "r") as f:
            data = json.load(f)
            sources = data.get("sources", {})
        success = False
        for p in ["rp", "oto", "to"]:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier and download_raw_json(p, identifier, dev_slug, inv_slug):
                    success = True
        return jsonify({"ok": success})
    except Exception as e:
        logger.error(f"API Error in {request.path}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@investments_bp.route("/fetch-status")
def fetch_status():
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    data_root = Path(USI_DATA_DIR)
    count = sum(1 for dev in data_root.iterdir() if dev.is_dir()
                for inv in dev.iterdir() if inv.is_dir() and list(inv.glob("usi_*.json"))) if data_root.exists() else 0
    return jsonify({"count": count})

@investments_bp.route("/system/verify-library")
def verify_library():
    """Checks the health of the usi-scrapers library connection (v0.3.0)."""
    try:
        from usi_scrapers import api as scraper_api
        from python_worker.config import get_scraper_config
        from usi_scrapers.fetcher import Fetcher

        config = get_scraper_config()
        if not config:
            return jsonify({"ok": False, "error": "Scraper config not available"})

        fetcher = Fetcher(config)
        # In usi-scrapers v0.3.0 health_check returns standardized {ok: bool, ...}
        result = scraper_api.health_check(config, fetcher)

        # Ensure 'status' key exists for frontend compatibility if result is True
        if result.get("ok"):
            result["status"] = "ok"

        return jsonify(result)
    except (AttributeError, ImportError) as e:
        logger.warning(f"Library health check failed: {e}")
        return jsonify({"ok": False, "error": f"Scraper API mismatch: {e}"}), 501
    except Exception as e:
        logger.exception("verify_library failed")
        return jsonify({"ok": False, "error": str(e)}), 500
# ── Developer API ──────────────────────────────────────────────────────────────

@investments_bp.route("/developers")
def list_developers():
    import time
    t0 = time.time()
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    t1 = time.time()
    logger.info(f"[TIMING] /developers - DM Init: {t1-t0:.3f}s")
    
    only_merged = request.args.get("only_merged") == "true"
    devs = dm.list_developers(only_merged=only_merged)
    t2 = time.time()
    logger.info(f"[TIMING] /developers - list_developers call: {t2-t1:.3f}s")
    
    # Sort alphabetically
    devs.sort(key=lambda d: d.get("name", d.get("developer_slug", "")).lower())
    
    t3 = time.time()
    logger.info(f"[TIMING] /developers - total: {t3-t0:.3f}s")
    
    return jsonify(devs)

@investments_bp.route("/developer/suggest", methods=["POST"])
def trigger_suggestions():
    """Triggers the developer similarity algorithm globally (via Doktor)."""
    from python_worker.daemons import get_doktor
    doktor = get_doktor()
    if doktor:
        import threading
        # Run it in a separate thread so it doesn't block the UI response
        threading.Thread(target=doktor._refresh_index, name="manual-doktor-refresh", daemon=True).start()
        return jsonify({"ok": True, "message": "Doktor is refreshing the index and investigating."})
    
    return jsonify({"ok": False, "message": "usi_crawlers not available."}), 500

@investments_bp.route("/developer/<dev_slug>")
def get_developer_detail(dev_slug):
    import time
    t0 = time.time()
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from python_worker.api.utils import _load_investment
    from pathlib import Path
    
    t1 = time.time()
    logger.info(f"[TIMING] Imports: {t1-t0:.3f}s")
    
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    t2 = time.time()
    logger.info(f"[TIMING] DM Init: {t2-t1:.3f}s")
    
    usi_dev_id = request.args.get("id")
    if usi_dev_id:
        dev = dm.get_developer_by_id(usi_dev_id)
    else:
        dev = dm.get_developer(dev_slug)
    
    t3 = time.time()
    logger.info(f"[TIMING] DM get_developer: {t3-t2:.3f}s")
    
    if not dev: abort(404)

    target_id = dev.get("usi_dev_id")

    # PRELOAD INDEX ONCE
    import python_worker.investment_index as inv_index
    import python_worker.developer_index as dev_index
    all_invs = inv_index.load(USI_DATA_DIR) or []
    
    # Preload dev index for fast fallback lookups
    all_devs = dev_index.load(dm.dev_dir) or []
    dev_slug_to_id = {d.get("developer_slug"): d.get("usi_dev_id") for d in all_devs if d.get("usi_dev_id")}
    
    t4 = time.time()
    logger.info(f"[TIMING] inv_index.load: {t4-t3:.3f}s")
    
    # Group investments by their assigned usi_dev_id (ID-only rule)
    invs_by_dev_id = {}
    for i in all_invs:
        did = i.get("usi_dev_id")
        if not did:
            # Fallback mapping if usi_dev_id is mysteriously missing in index
            did = dev_slug_to_id.get(i.get("developer_slug"))
        if did:
            invs_by_dev_id.setdefault(did, []).append(i)
    
    t5 = time.time()
    logger.info(f"[TIMING] group by id: {t5-t4:.3f}s")

    # PRESERVE BASE RECORD: before aggregation, capture the state of the "host" record
    base_invs_raw = invs_by_dev_id.get(target_id, [])
    base_pm = (dev.get("original_portal_mapping") or dev.get("portal_mapping") or {}).copy()
    base_portals = {p for p in ("rp", "oto", "to") if base_pm.get(p)}
    base_invs = [i for i in base_invs_raw if not base_portals or _inv_matches_dev(i, base_pm)]
    
    dev["base_record"] = {
        "name": dev.get("name"),
        "developer_slug": dev.get("developer_slug"),
        "usi_dev_id": dev.get("usi_dev_id"),
        "portal_mapping": base_pm,
        "investments_count": len(base_invs),
        "inv_list": [
            {"name": inv.get("name", inv.get("investment_slug", "")), "slug": inv.get("investment_slug", "")}
            for inv in base_invs[:10]
        ]
    }

    aggregated_pm = base_pm.copy()

    # Collect investments from this dev and all children (merged_from)
    investments = list(base_invs)
    
    # Store original merged IDs to prevent them from showing up as suggestions
    merged_ids = {m.get("usi_dev_id") for m in dev.get("merged_from", []) if m.get("usi_dev_id")}

    existing_inv_ids = {i.get("usi_inv_id") for i in investments if i.get("usi_inv_id")}

    # Enrich merged_from entries — resolve child by usi_dev_id
    valid_members = []
    for member in dev.get("merged_from", []):
        child_id = member.get("usi_dev_id")
        child_slug = member.get("slug")
        child_dev = (dm.get_developer_by_id(child_id) if child_id else (dm.get_developer(child_slug) if child_slug else None))
        
        if not child_dev or child_dev.get("usi_dev_id") == dev.get("usi_dev_id"):
            continue
            
        c_slug = child_dev.get("developer_slug", child_slug)
        member["slug"] = c_slug
        
        child_pm = (child_dev.get("portal_mapping") or {}).copy()
        child_portals = {p for p in ("rp", "oto", "to") if child_pm.get(p)}
        
        child_invs_raw = invs_by_dev_id.get(child_dev.get("usi_dev_id"), [])
        child_invs = [i for i in child_invs_raw if not child_portals or _inv_matches_dev(i, child_pm)]

        for p in ("rp", "oto", "to"):
            if not aggregated_pm.get(p) and child_pm.get(p):
                aggregated_pm[p] = child_pm[p]

        for ci in child_invs:
            ci_id = ci.get("usi_inv_id")
            if ci_id and ci_id not in existing_inv_ids:
                investments.append(ci)
                existing_inv_ids.add(ci_id)
            elif not ci_id:
                investments.append(ci)
                
        member["portal_mapping"] = child_pm
        member["website"] = child_dev.get("website")
        member["investments_count"] = len(child_invs)
        member["inv_list"] = [
            {"name": inv.get("name", inv.get("investment_slug", "")), "slug": inv.get("investment_slug", "")}
            for inv in child_invs[:10]
        ]
        valid_members.append(member)

    dev["merged_from"] = valid_members

    # Enrich suggestions — resolve suggested dev by usi_dev_id (not slug)
    valid_suggestions = []

    for s in dev.get("suggestions", []):
        s_id = s.get("usi_dev_id")
        if s_id in merged_ids:
            continue

        s_slug = s.get("developer_slug")
        s_dev = (dm.get_developer_by_id(s_id) if s_id
                 else (dm.get_developer(s_slug) if s_slug else None))
        if s_dev:
            s["developer_slug"] = s_dev.get("developer_slug", s_slug)  # refresh slug
            s["name"] = s_dev.get("name", s_slug)
            s["portal_mapping"] = s_dev.get("portal_mapping", {})
            s["website"] = s_dev.get("website")
            
            s_portals = {p for p in ("rp", "oto", "to") if (s_dev.get("portal_mapping") or {}).get(p)}
            s_invs_raw = invs_by_dev_id.get(s_dev.get("usi_dev_id"), [])
            s_invs = [i for i in s_invs_raw if not s_portals or _inv_matches_dev(i, s_dev.get("portal_mapping") or {})]
            
            s["investments_count"] = len(s_invs)
            valid_suggestions.append(s)

    dev["suggestions"] = valid_suggestions
    dev["investments"] = investments
    dev["investments_count"] = len(investments)
    dev["portal_mapping"] = aggregated_pm
    
    t6 = time.time()
    logger.info(f"[TIMING] suggestions and final processing: {t6-t5:.3f}s")
    logger.info(f"[TIMING] TOTAL endpoint time: {t6-t0:.3f}s")
    
    return jsonify(dev)

@investments_bp.route("/developer/<dev_slug>/merge", methods=["POST"])
def merge_developer(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    target_id_param = payload.get("target_id")
    if not source_id or not target_id_param:
        abort(400)
    try:
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        target_dev = dm.get_developer_by_id(target_id_param)
        if not target_dev:
            abort(404)
        target_id = target_dev.get("usi_dev_id")
        if dm.merge_by_id(target_id, source_id):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Merge failed — check server logs"}), 422
    except Exception as e:
        logger.exception("merge_developer error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@investments_bp.route("/developer/<dev_slug>/unmerge", methods=["POST"])
def unmerge_developer(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    target_id_param = payload.get("target_id")
    if not source_id or not target_id_param:
        abort(400)
    try:
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        target_dev = dm.get_developer_by_id(target_id_param)
        if not target_dev:
            abort(404)
        target_id = target_dev.get("usi_dev_id")
        if dm.unmerge_by_id(target_id, source_id):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Unmerge failed"}), 422
    except Exception as e:
        logger.exception("unmerge_developer error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@investments_bp.route("/developer/<dev_slug>/dismiss-suggestion", methods=["POST"])
def dismiss_suggestion(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    suggested_id = payload.get("usi_dev_id")
    target_id_param = payload.get("target_id")
    if not suggested_id or not target_id_param: abort(400)
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    if dm.dismiss_suggestion_by_id(target_id_param, suggested_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/report", methods=["POST"])
def report_issue(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    payload = request.get_json()
    note = payload.get("note")
    usi_inv_id = request.args.get("id")
    if not note:
        return jsonify({"error": "Note is required"}), 400

    if investment_service.add_report(dev_slug, inv_slug, note, usi_inv_id=usi_inv_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/merge", methods=["POST"])
def merge_investment(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug): abort(400)
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    target_id = payload.get("target_id")
    if not source_id or not target_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if im.merge_by_id(target_id, source_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Merge failed"}), 422

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/unmerge", methods=["POST"])
def unmerge_investment(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug): abort(400)
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    master_id = payload.get("target_id") # We receive target_id which is actually the master_id
    if not source_id or not master_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if im.unmerge_by_id(master_id, source_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Unmerge failed"}), 422

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/dismiss-suggestion", methods=["POST"])
def dismiss_investment_suggestion(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug): abort(400)
    payload = request.get_json() or {}
    suggested_id = payload.get("usi_inv_id")
    target_id = payload.get("target_id")
    if not suggested_id or not target_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if im.dismiss_suggestion_by_id(target_id, suggested_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Dismiss failed"}), 422

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/suggest", methods=["POST"])
def suggest_similar_investments(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug): abort(400)
    payload = request.get_json() or {}
    target_id = payload.get("target_id") # Can be empty for legacy investments
    
    from python_worker.jobs import job_manager
    def run_suggest(job_id, t_dev, t_inv, t_id):
        from python_worker.detect_similar_invs import detect_similar_invs
        from python_worker.config import USI_DATA_DIR
        from pathlib import Path
        job_manager.update_progress(job_id, 10, message="Skanowanie w poszukiwaniu podobnych...")
        detect_similar_invs(Path(USI_DATA_DIR), target_dev_slug=t_dev, target_inv_id=t_id, target_inv_slug=t_inv)
        job_manager.update_progress(job_id, 100, message="Skanowanie zakończone.")
        
    job_manager.start_job("Skanuj Podobne Inwestycje", run_suggest, dev_slug, inv_slug, target_id)
    return jsonify({"ok": True, "message": "Rozpoczęto skanowanie podobnych inwestycji."})

@investments_bp.route("/investment/<dev_slug>/<inv_slug>/review", methods=["POST"])
def mark_reviewed(dev_slug, inv_slug):
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug):
        abort(400)
    usi_inv_id = request.args.get("id")
    if investment_service.mark_as_reviewed(dev_slug, inv_slug, usi_inv_id=usi_inv_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/register-bulk", methods=["POST"])
def register_bulk():
    payload = request.get_json()
    portal = payload.get("portal")
    investments = payload.get("investments", [])
    
    if not portal or not investments:
        return jsonify({"error": "Missing portal or investments list"}), 400

    def run_bulk_job(job_id, p, invs):
        def progress_wrapper(report):
            msg = report.get("message", "Przetwarzanie danych...")
            percent = report.get("progress_percent", 0)
            job_manager.update_progress(job_id, percent, msg)
            
        try:
            investment_service.process_batch(p, invs, on_progress_callback=progress_wrapper)
            job_manager.update_progress(job_id, 100, f"Zakończono pobieranie zbiorcze ({len(invs)} pozycji)")
        except Exception as e:
            logger.error(f"Bulk job error: {e}")
            job_manager.update_progress(job_id, 100, f"Błąd zadania zbiorczego: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Bulk Register: {portal.upper()} ({len(investments)})", run_bulk_job, portal, investments)
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json()
    try:
        portal = payload.get("portal", "")
        if "rynekpierwotny" in portal or portal == "rp": portal = "rp"
        elif "otodom" in portal or portal == "oto": portal = "oto"
        elif "tabelaofert" in portal or portal == "to": portal = "to"

        result = investment_service.register_investment(
            portal=portal,
            developer_name=payload.get("developer_name"),
            inv_slug=payload.get("inv_slug"),
            name=payload.get("name"),
            item_id=payload.get("id"),
            url=payload.get("url"),
            vendor_id=payload.get("vendor_id")
        )

        if result == (None, None):
            return jsonify({"ok": True, "skipped": True, "message": "Investment already exists by ID"})

        dev_slug, inv_slug = result

        def run_register_job(job_id, d_slug, i_slug, inv_name):
            job_manager.update_progress(job_id, 10, f"Rozpoczęto pobieranie: {inv_name}")
            if investment_service.update_investment(d_slug, i_slug):
                job_manager.update_progress(job_id, 100, f"Ukończono: {inv_name}")
            else:
                job_manager.update_progress(job_id, 100, f"Błąd pobierania: {inv_name}", status="failed")

        job_id = job_manager.start_job(f"Register: {payload.get('name')}", run_register_job, dev_slug, inv_slug, payload.get('name'))
        return jsonify({"ok": True, "job_id": job_id})
    except Exception as e:
        logger.error(f"API Error in {request.path}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
