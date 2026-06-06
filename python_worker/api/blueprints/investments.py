import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort, request, send_file, redirect
from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename
import python_worker.investment_index as inv_index
import threading

logger = logging.getLogger(__name__)
_fallback_lock = threading.Lock()



PORTAL_MATCHERS = {
    "rp": lambda pm_p, src_p: bool(str(pm_p.get("id", "")) and str(src_p.get("vendor_id", "")) and str(pm_p.get("id", "")) == str(src_p.get("vendor_id", ""))),
    "oto": lambda pm_p, src_p: str(src_p.get("agency_id", "")) in {str(a) for a in (pm_p.get("agency_ids") or [pm_p.get("agency_id", "")]) if a},
    "to": lambda pm_p, src_p: (
        (pm_id := str(pm_p.get("id") or pm_p.get("slug", "") or pm_p.get("agency_id", ""))) == 
        (src_id := str(src_p.get("developer_id") or ""))
    ) or (not pm_id and not src_id)
}


def _inv_matches_dev(inv: dict, pm: dict) -> bool:
    """Return True only when a portal developer ID from sources exactly matches portal_mapping.
    No fallback guessing — missing ID means no match."""
    src = inv.get("sources") or {}
    for portal, matcher in PORTAL_MATCHERS.items():
        if not pm.get(portal) or not src.get(portal):
            continue
        pm_p = pm[portal]
        src_p = src[portal]
        
        if pm_p.get("_inferred"):
            return True
            
        if matcher(pm_p, src_p):
            return True
    return False


investments_bp = Blueprint('investments', __name__)
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
investment_service = InvestmentService()
developer_manager = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")

from functools import lru_cache
_missing_images_cache = set()
_cdn_redirect_cache = {}
_list_inv_cache = {} # Map full_path -> {"data": result, "timestamp": ts}
_list_inv_lock = threading.Lock()

def invalidate_list_cache():
    """Clears the server-side cache for investment lists."""
    with _list_inv_lock:
        count = len(_list_inv_cache)
        _list_inv_cache.clear()
        if count > 0:
            logger.info(f"Investment list cache invalidated ({count} entries cleared)")

# Register callback for index changes
inv_index.on_change(invalidate_list_cache)

@investments_bp.route("/image/<path:filepath>")
def serve_image(filepath):
    from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR
    from pathlib import Path
    from urllib.parse import unquote
    import time

    start_t = time.time()
    if filepath in _missing_images_cache:
        return abort(404)
    
    # 0. Check redirect cache
    if filepath in _cdn_redirect_cache:
        return redirect(_cdn_redirect_cache[filepath], code=302)

    # 1. Decode path
    decoded_path = unquote(filepath)
    img_path = Path(PUBLIC_USI_DIR) / decoded_path

    if img_path.exists() and img_path.is_file():
        return send_file(img_path)

    # 2. Try raw if decoded failed
    raw_path = Path(PUBLIC_USI_DIR) / filepath
    if raw_path.exists() and raw_path.is_file():
        return send_file(raw_path)

    # 3. Fallback — Use index to find original URL via JSON mapping
    parts = Path(decoded_path).parts
    if len(parts) >= 2:
        dev_slug, inv_slug = parts[0], parts[1]
        
        lock_start = time.time()
        logger.debug(f"Image {filepath} requires fallback path. Waiting for _fallback_lock...")
        
        with _fallback_lock:
            lock_waited = (time.time() - lock_start) * 1000
            if lock_waited > 50:
                logger.warning(f"High lock contention: Waited {lock_waited:.1f}ms to acquire _fallback_lock for {filepath}")
                
            # Check cache again inside lock
            if filepath in _cdn_redirect_cache:
                return redirect(_cdn_redirect_cache[filepath], code=302)
            if filepath in _missing_images_cache:
                return abort(404)

            try:
                # Fast path: Use hot index to find the ID and canonical directory
                entry = inv_index.get_entry_by_slug(dev_slug, inv_slug)
                
                if not entry:
                    logger.warning(f"Slug match missing in hot index for {dev_slug}/{inv_slug}. Forcing full index check.")
                    # Fallback if hot index is not yet populated
                    inv_index.load(USI_DATA_DIR)
                    entry = inv_index.get_entry_by_slug(dev_slug, inv_slug)
                
                if entry:
                    inv_id = entry.get("usi_inv_id")
                    resources = investment_service.get_investment_resources(inv_id)
                    if resources and resources["files"].get("anchor"):
                        json_file = resources["files"]["anchor"]
                        try:
                            data = json.loads(json_file.read_text(encoding="utf-8"))
                            image_paths = data.get("image_paths", [])
                            photos = data.get("photos", [])
                            
                            # ← UŻYWAJ DICT LOOKUP zamiast substring search
                            path_to_photo = {img_path: photo for img_path, photo in zip(image_paths, photos)}
                            
                            if decoded_path in path_to_photo:
                                photo_url = path_to_photo[decoded_path]
                                if str(photo_url).startswith("http"):
                                    _cdn_redirect_cache[filepath] = photo_url
                                    duration = (time.time() - start_t) * 1000
                                    logger.info(f"Image redirect found in {duration:.1f}ms")
                                    return redirect(photo_url, code=302)
                            
                            # Fallback: partial match only if direct lookup failed
                            for img_path, photo_url in path_to_photo.items():
                                if decoded_path.endswith(Path(img_path).name):
                                    if str(photo_url).startswith("http"):
                                        _cdn_redirect_cache[filepath] = photo_url
                                        return redirect(photo_url, code=302)
                        except Exception as e:
                            logger.warning(f"Error parsing {json_file.name}: {e}")
            except Exception as e:
                logger.error(f"Fallback error for {filepath}: {e}")

    duration = (time.time() - start_t) * 1000
    logger.warning(f"Image not found: {filepath} - took {duration:.1f}ms")
    
    # Okresowe czyszczenie - rozdzielone i niezależne warunki
    _missing_images_cache.add(filepath)
    
    # Cache brakujących zdjęć czyścimy, gdy osiągnie 5 000 pozycji
    if len(_missing_images_cache) > 5000:
        _missing_images_cache.clear()
        logger.info("Missing images cache cleared (reached 5000)")
        
    # Prawidłowe przekierowania CDN czyścimy bardzo rzadko (np. dopiero przy 100 000 wpisów)
    # Zapobiegnie to pętli destrukcji cache (cache thrashing)
    if len(_cdn_redirect_cache) > 100000:
        _cdn_redirect_cache.clear()
        logger.info("CDN redirect cache cleared (reached 100000)")
    
    abort(404)

@investments_bp.route("/developer/<usi_dev_id>/logo")
def serve_dev_logo(usi_dev_id):
    from python_worker.config import USI_DEV_DIR
    from pathlib import Path
    
    res = developer_manager.get_developer_resources(usi_dev_id)
    if not res or not res.get("directory"):
        abort(404)
        
    dev_dir = res["directory"]
    
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
    import time
    cache_key = request.full_path
    
    # Check if cache is still valid
    with _list_inv_lock:
        if cache_key in _list_inv_cache:
            entry = _list_inv_cache[cache_key]
            if (time.time() - entry["timestamp"]) < 30:
                logger.info(f"Returning cached investments list for {cache_key}")
                return jsonify(entry["data"])

    start_t = time.time()
    data_root = investment_service.data_dir
    if not data_root.exists():
        return jsonify([])

    entries = inv_index.load(data_root)
    investments = entries

    if investments is None:
        # Index missing — build it in background
        logger.info("Investment index not found; checking rebuild status")

        from python_worker.investment_index import _is_rebuilding
        if not _is_rebuilding:
            logger.info("Triggering background index rebuild (no rebuild currently in progress)")
            public_usi_dir = investment_service.public_usi_dir

            def _rebuild():
                try:
                    logger.info("Background rebuild thread starting...")
                    inv_index.rebuild(data_root, public_usi_dir)
                    logger.info("Background rebuild thread finished successfully.")
                except Exception as e:
                    logger.error(f"Background index rebuild failed: {e}")

            import threading
            threading.Thread(target=_rebuild, daemon=True).start()
        else:
            logger.warning("Index rebuild already in progress. Multiple concurrent rebuilds prevented.")
        investments = []
    if investments is None:
        investments = []

    # Server-side filtering
    filters = []

    if request.args.get("onlyUnreviewed") == "true":
        filters.append(lambda inv: inv.get("reviewed") is False)
    if request.args.get("onlyNoPhotos") == "true":
        filters.append(lambda inv: not inv.get("photos"))
    if search := request.args.get("search", "").lower():
        filters.append(lambda inv: any(search in (inv.get(k) or "").lower() for k in ["name", "developer", "district", "address"]))
    if dev := request.args.get("dev"):
        filters.append(lambda inv: dev in (inv.get("developer_slug"), inv.get("developer")))
    if status := request.args.get("status"):
        filters.append(lambda inv: inv.get("status") == status)
    if sources_arg := request.args.get("sources"):
        sources = set(sources_arg.upper().split(","))
        filters.append(lambda inv: inv.get("source", "").upper() in sources)
    if segments_arg := request.args.get("segments"):
        segments = set(segments_arg.split(","))
        filters.append(lambda inv: (inv.get("segment") or inv.get("specifications", {}).get("segment")) in segments)
    if cities_arg := request.args.get("cities"):
        cities = set(cities_arg.lower().split(","))
        main_cities = ['warszawa', 'kraków', 'wrocław', 'łódź', 'poznań', 'gdańsk', 'szczecin', 'bydgoszcz', 'lublin', 'białystok']
        def city_filter(inv):
            addr = (inv.get("address") or "").lower()
            found_city = next((c for c in main_cities if c in addr), None)
            return found_city in cities
        filters.append(city_filter)

    unreviewed_count = sum(1 for inv in investments if inv.get("reviewed") is False)

    filter_start = time.time()
    filtered = [inv for inv in investments if all(f(inv) for f in filters)]

    duration = (time.time() - start_t) * 1000
    filter_duration = (time.time() - filter_start) * 1000
    logger.info(f"list_investments: Found {len(filtered)}/{len(investments)} entries in {duration:.1f}ms (filtering: {filter_duration:.1f}ms)")

    result = {"data": filtered, "unreviewedCount": unreviewed_count}
    with _list_inv_lock:
        _list_inv_cache[cache_key] = {"data": result, "timestamp": time.time()}
        # Simple cleanup if cache grows too large
        if len(_list_inv_cache) > 100:
            _list_inv_cache.clear()

    return jsonify(result)

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

@investments_bp.route("/investment/<system_id>/data")
def investment_data(system_id):
    inv = investment_service.get_investment(system_id)
    if inv is None:
        abort(404)
    return jsonify(inv)

@investments_bp.route("/investment/<system_id>/ratings", methods=["POST"])
def save_ratings(system_id):
    payload = request.get_json(silent=True) or {}
    try:
        if investment_service.save_ratings(system_id, payload):
            return jsonify({"ok": True})
        else:
            return jsonify({"error": f"Nie znaleziono inwestycji (ID: {system_id})"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@investments_bp.route("/investment/<system_id>/mark-delete", methods=["POST"])
def save_deletion_list(system_id):
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        abort(400, "paths must be a list")
    if investment_service.mark_deleted_photos(system_id, paths):
        return jsonify({"ok": True, "count": len(paths)})
    else:
        abort(404)

@investments_bp.route("/investment/<system_id>/reload", methods=["POST"])
def reload_investment(system_id):
    success = investment_service.update_investment(system_id)
    if not success:
        return jsonify({"ok": False, "error": "Failed to update"}), 500
    
    # --- POPRAWKA: Czyszczenie cache listy inwestycji ---
    with _list_inv_lock:
        _list_inv_cache.clear()
        logger.info("Cleared investments list cache due to manual reload.")
        
    updated_inv = investment_service.get_investment(system_id)
    return jsonify({"ok": True, "investment": updated_inv})

@investments_bp.route("/investment/<system_id>/refresh", methods=["POST"])
def refresh_investment_route(system_id):
    inv = investment_service.get_investment(system_id)
    if not inv:
        abort(404)
    
    def run_refresh_job(job_id, i_name, system_id):
        job_manager.update_progress(job_id, 10, f"Rozpoczęto odświeżanie: {i_name}")
        try:
            if investment_service.update_investment(system_id):
                # --- POPRAWKA: Czyszczenie cache listy inwestycji po zakończeniu wątku ---
                with _list_inv_lock:
                    _list_inv_cache.clear()
                logger.info(f"Cleared investments list cache after background refresh for {i_name}.")
                job_manager.update_progress(job_id, 100, f"Ukończono odświeżanie: {i_name}")
            else:
                job_manager.update_progress(job_id, 100, f"Brak danych do odświeżenia: {i_name}", status="failed")
        except RuntimeError as e:
            logger.error(f"Refresh job failed for {system_id}: {e}")
            job_manager.update_progress(job_id, 100, str(e), status="failed")
        except Exception as e:
            logger.exception(f"Exception during refresh job for {system_id}: {e}")
            job_manager.update_progress(job_id, 100, f"Wyjątek: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Refresh: {inv['name']}", run_refresh_job, inv['name'], system_id)
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/investment/<system_id>/download-raw", methods=["POST"])
def download_raw_route(system_id):
    try:
        data = investment_service.get_investment(system_id)
        if not data:
            abort(404)
            
        sources = data.get("sources", {})
        success = False
        for p in ["rp", "oto", "to"]:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier and investment_service.download_raw_json(p, identifier, system_id):
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
    dm = developer_manager
    t1 = time.time()
    logger.info(f"[TIMING] /developers - DM Init: {t1-t0:.3f}s")
    
    only_merged = request.args.get("only_merged") == "true"
    devs = dm.list_developers(only_merged=only_merged)
    t2 = time.time()
    logger.info(f"[TIMING] /developers - list_developers call: {t2-t1:.3f}s")
    
    # Sort alphabetically
    devs.sort(key=lambda d: d.get("name", d.get("usi_dev_id", "")).lower())
    
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

@investments_bp.route("/developer/<usi_dev_id>")
def get_developer_detail(usi_dev_id):
    import time
    t0 = time.time()
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    dev = dm.get_developer_by_id(usi_dev_id)
    
    if not dev: abort(404)

    target_id = dev.get("usi_dev_id")

    # PRELOAD INDEX ONCE
    import python_worker.investment_index as inv_index
    import python_worker.developer_index as dev_index
    all_invs = inv_index.load(USI_DATA_DIR) or []
    
    # Group investments by their assigned usi_dev_id (ID-only rule)
    invs_by_dev_id = {}
    for i in all_invs:
        did = i.get("usi_dev_id")
        if did:
            invs_by_dev_id.setdefault(did, []).append(i)
    
    from python_worker.developer_manager import DeveloperManager
    # 1. Collect all valid members and original portal mappings
    base_pm = (dev.get("original_portal_mapping") or dev.get("portal_mapping") or {}).copy()
    valid_members = []
    
    for member in dev.get("merged_from", []):
        child_id = member.get("usi_dev_id")
        child_dev = dm.get_developer_by_id(child_id) if child_id else None
        
        if not child_dev or child_dev.get("usi_dev_id") == dev.get("usi_dev_id"):
            continue
            
        member["slug"] = child_dev.get("developer_slug")
        member["_pm"] = (child_dev.get("original_portal_mapping") or child_dev.get("portal_mapping") or {}).copy()
        member["_dev"] = child_dev
        member["_invs"] = invs_by_dev_id.get(child_id, [])
        valid_members.append(member)

    # 2. Collect base investments
    base_invs = invs_by_dev_id.get(target_id, [])
    base_portals = {p for p in ("rp", "oto", "to") if base_pm.get(p)}

    # 4. Finalize Base Record UI response
    if not base_portals and not base_invs:
        dev["base_record"] = None
    else:
        dev["base_record"] = {
            "name": dev.get("name"),
            "developer_slug": dev.get("developer_slug"),
            "usi_dev_id": dev.get("usi_dev_id"),
            "portal_mapping": base_pm,
            "investments_count": len(base_invs),
            "inv_list": [
                {"name": inv.get("name", inv.get("usi_inv_id", "")), "id": inv.get("usi_inv_id", "")}
                for inv in base_invs[:10]
            ]
        }

    # 5. Finalize Members UI response
    final_members = []
    investments = list(base_invs)
    existing_inv_ids = {i.get("usi_inv_id") for i in base_invs if i.get("usi_inv_id")}
    
    aggregated_pm = base_pm.copy()
    
    for m in valid_members:
        m["investments_count"] = len(m["_invs"])
        m["inv_list"] = [
            {"name": inv.get("name", inv.get("usi_inv_id", "")), "id": inv.get("usi_inv_id", "")}
            for inv in m["_invs"][:10]
        ]
        m["portal_mapping"] = m["_pm"]
        m["original_portal_mapping"] = m["_pm"] 
        
        # Aggregate portal mappings for the main record
        for p, pdata in m["_pm"].items():
            if not aggregated_pm.get(p) and pdata:
                aggregated_pm[p] = pdata
        
        # Collect for global investments list (deduplicated)
        for inv in m["_invs"]:
            iid = inv.get("usi_inv_id")
            if iid and iid not in existing_inv_ids:
                investments.append(inv)
                existing_inv_ids.add(iid)
        
        # Clean up temp keys
        m.pop("_pm", None); m.pop("_dev", None); m.pop("_invs", None)
        final_members.append(m)

    dev["merged_from"] = final_members
    merged_ids = {m.get("usi_dev_id") for m in final_members if m.get("usi_dev_id")}

    dev["portal_mapping"] = aggregated_pm
    dev["investments_count"] = len(investments)
    dev["investments"] = investments 

    # Suggestions logic follows...
    valid_suggestions = []

    for s in dev.get("suggestions", []):
        s_id = s.get("usi_dev_id")
        if s_id in merged_ids:
            continue

        s_dev = dm.get_developer_by_id(s_id)
        if s_dev:
            s["name"] = s_dev.get("name", s_id)
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
    
    return jsonify(dev)

@investments_bp.route("/developer/<usi_dev_id>/merge", methods=["POST"])
def merge_developer(usi_dev_id):
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    if not source_id:
        abort(400)
    try:
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        if dm.merge_by_id(usi_dev_id, source_id):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Merge failed — check server logs"}), 422
    except Exception as e:
        logger.exception("merge_developer error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@investments_bp.route("/developer/<usi_dev_id>/unmerge", methods=["POST"])
def unmerge_developer(usi_dev_id):
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    if not source_id:
        abort(400)
    try:
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        if dm.unmerge_by_id(usi_dev_id, source_id):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Unmerge failed"}), 422
    except Exception as e:
        logger.exception("unmerge_developer error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@investments_bp.route("/developer/<usi_dev_id>/dismiss-suggestion", methods=["POST"])
def dismiss_suggestion(usi_dev_id):
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    suggested_id = payload.get("usi_dev_id")
    if not suggested_id: abort(400)
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    if dm.dismiss_suggestion_by_id(usi_dev_id, suggested_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/developer/<usi_dev_id>/discover", methods=["POST"])
def discover_developer_investments(usi_dev_id):
    """Triggers discovery for a developer's investments."""
    from python_worker.services.discovery_service import DiscoveryService
    from python_worker.jobs import job_manager
    
    dev = developer_manager.get_developer_by_id(usi_dev_id)
    if not dev:
        abort(404)
        
    def run_discovery(job_id, d_id, d_name):
        discovery_service = DiscoveryService()
        job_manager.update_progress(job_id, 10, f"Szukanie nowych inwestycji dla: {d_name}")
        try:
            results = discovery_service.discover_for_developer(d_id)
            count = len(results)
            job_manager.update_progress(job_id, 100, f"Znaleziono {count} nowych ofert.")
        except Exception as e:
            logger.exception(f"Discovery failed for {d_id}")
            job_manager.update_progress(job_id, 100, f"Błąd: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Discovery: {dev['name']}", run_discovery, usi_dev_id, dev['name'])
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/investment/<system_id>/merge", methods=["POST"])
def merge_investment(system_id):
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    if not source_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    
    im = InvestmentMerger()
    dm = DeveloperManager(Path(USI_DATA_DIR))
    
    # Pre-fetch entries to check developers before merge updates files
    target_entry = im._find_index_entry(system_id)
    source_entry = im._find_index_entry(source_id)

    if im.merge_by_id(system_id, source_id):
        # Auto-suggest developers if they differ
        if target_entry and source_entry:
            t_dev_id = target_entry.get("usi_dev_id")
            s_dev_id = source_entry.get("usi_dev_id")
            if t_dev_id and s_dev_id and t_dev_id != s_dev_id:
                t_dev = dm.get_developer_by_id(t_dev_id)
                s_dev = dm.get_developer_by_id(s_dev_id)
                if t_dev and s_dev:
                    t_master = t_dev.get("master_id") or t_dev_id
                    s_master = s_dev.get("master_id") or s_dev_id
                    
                    if t_master != s_master:
                        dm.add_suggestion(t_dev_id, s_dev_id, "Połączono ich inwestycje")
        
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Merge failed"}), 422

@investments_bp.route("/investment/<system_id>/unmerge", methods=["POST"])
def unmerge_investment(system_id):
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    if not source_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if im.unmerge_by_id(system_id, source_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Unmerge failed"}), 422

@investments_bp.route("/investment/<system_id>/dismiss-suggestion", methods=["POST"])
def dismiss_investment_suggestion(system_id):
    payload = request.get_json() or {}
    suggested_id = payload.get("id") or payload.get("usi_inv_id")
    if not suggested_id: abort(400)
    
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if im.dismiss_suggestion_by_id(system_id, suggested_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False, "error": "Dismiss failed"}), 422

@investments_bp.route("/investment/<system_id>/suggest", methods=["POST"])
def suggest_similar_investments(system_id):
    inv = investment_service.get_investment(system_id)
    if not inv:
        abort(404)
        
    from python_worker.jobs import job_manager
    def run_suggest(job_id, t_id, i_name):
        from python_worker.detect_similar_invs import detect_similar_invs
        from python_worker.config import USI_DATA_DIR
        from pathlib import Path
        job_manager.update_progress(job_id, 10, message=f"Skanowanie w poszukiwaniu podobnych dla {i_name}...")
        detect_similar_invs(Path(USI_DATA_DIR), target_inv_id=t_id)
        job_manager.update_progress(job_id, 100, message="Skanowanie zakończone.")
        
    job_manager.start_job(f"Skanuj Podobne: {inv['name']}", run_suggest, system_id, inv['name'])
    return jsonify({"ok": True, "message": "Rozpoczęto skanowanie podobnych inwestycji."})

@investments_bp.route("/investment/<system_id>/review", methods=["POST"])
def mark_reviewed(system_id):
    if investment_service.mark_as_reviewed(system_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/investment/<system_id>/add-report", methods=["POST"])
def add_report(system_id):
    payload = request.get_json() or {}
    note = payload.get("note")
    if not note:
        abort(400, "note is required")
        
    if investment_service.add_report(system_id, note):
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

        dev_name = payload.get("developer_name")
        # Ensure we don't pass dummy values that mask identification
        if dev_name and dev_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper", ""):
            dev_name = None

        result = investment_service.register_investment(
            portal=portal,
            developer_name=dev_name,
            name=payload.get("name"),
            item_id=payload.get("id"),
            url=payload.get("url"),
            vendor_id=payload.get("vendor_id")
        )

        if result == (None, None):
            return jsonify({"ok": True, "skipped": True, "message": "Investment already exists by ID"})

        dev_slug, inv_slug, system_id = result

        def run_register_job(job_id, sys_id, inv_name):
            job_manager.update_progress(job_id, 10, f"Rozpoczęto pobieranie: {inv_name}")
            if investment_service.update_investment(sys_id):
                job_manager.update_progress(job_id, 100, f"Ukończono: {inv_name}")
            else:
                job_manager.update_progress(job_id, 100, f"Błąd pobierania: {inv_name}", status="failed")

        job_id = job_manager.start_job(f"Register: {payload.get('name')}", run_register_job, system_id, payload.get('name'))
        return jsonify({"ok": True, "job_id": job_id})
    except Exception as e:
        logger.error(f"API Error in {request.path}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500
