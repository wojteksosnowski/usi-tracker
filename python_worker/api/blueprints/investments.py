import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote
from flask import Blueprint, jsonify, abort, request, send_file, redirect, send_from_directory
from werkzeug.utils import safe_join

from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename, get_anchor_path, update_anchor_json, filter_investments
import python_worker.developer_index as dev_index
import python_worker.investment_index as inv_index
from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR, USI_DEV_DIR, get_shared_config, get_shared_fetcher, get_shared_tech_manager, get_shared_repository
from usi_scrapers import api as scraper_api

logger = logging.getLogger(__name__)

_PLACEHOLDER_DIR = Path(__file__).parent.parent.parent / "ui" / "assets"
_PLACEHOLDER_FILE = _PLACEHOLDER_DIR / "image-placeholder.svg"

investments_bp = Blueprint('investments', __name__)
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.services.developer_service import DeveloperService

developer_manager = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
developer_service = DeveloperService(Path(USI_DATA_DIR), Path(USI_DATA_DIR).parent / "USIdev")

# Lazy-loaded sync service (tylko do rejestracji, odświeżeń, batch)
def _get_sync():
    from python_worker.services.investment_sync import InvestmentSyncService
    from python_worker.services.investment_identity import InvestmentIdentityResolver
    from python_worker.developer_manager import DeveloperManager
    from python_worker.investment_repository import InvestmentRepository
    identity = InvestmentIdentityResolver(Path(USI_DATA_DIR), Path(PUBLIC_USI_DIR).parent / "USI")
    dm = DeveloperManager(USI_DATA_DIR)
    repo = InvestmentRepository(identity, Path(USI_DATA_DIR))
    return InvestmentSyncService(identity, Path(USI_DATA_DIR), Path(PUBLIC_USI_DIR).parent / "USI", dm, repo)

def _get_editor():
    from python_worker.services.investment_editor import InvestmentEditorService
    from python_worker.services.investment_identity import InvestmentIdentityResolver
    from python_worker.investment_repository import InvestmentRepository
    identity = InvestmentIdentityResolver(Path(USI_DATA_DIR), Path(PUBLIC_USI_DIR).parent / "USI")
    repo = InvestmentRepository(identity, Path(USI_DATA_DIR))
    return InvestmentEditorService(identity, Path(USI_DATA_DIR), Path(PUBLIC_USI_DIR).parent / "USI", repo)

_list_dev_cache = {} # Map full_path -> {"data": result, "timestamp": ts}
_list_dev_lock = threading.Lock()

def invalidate_dev_list_cache():
    """Clears the server-side cache for developer lists."""
    with _list_dev_lock:
        count = len(_list_dev_cache)
        _list_dev_cache.clear()
        if count > 0:
            logger.info(f"Developer list cache invalidated ({count} entries cleared)")

# Register callback for developer index changes
dev_index.on_change(invalidate_dev_list_cache)



@investments_bp.route("/image/<path:filepath>")
def get_image(filepath):
    """Serwuje zdjęcie bezpośrednio z dysku O(1). Bez skanowania i magii."""
    decoded_path = Path(PUBLIC_USI_DIR) / unquote(filepath)
    
    if decoded_path.exists() and decoded_path.is_file():
        response = send_file(decoded_path)
        response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response

    if _PLACEHOLDER_FILE.exists():
        return send_file(_PLACEHOLDER_FILE, mimetype="image/svg+xml")
        
    abort(404)

@investments_bp.route("/developer/<usi_dev_id>/logo")
def serve_dev_logo(usi_dev_id):
    """
    Serwuje plik logo dewelopera z dysku.
    W przypadku braku pliku zwraca standardowy wektorowy placeholder UI,
    eliminując błędy 404 i narzut sieciowy.
    """
    from flask import current_app, send_file
    from pathlib import Path
    
    # Próba pobrania katalogu zasobów dewelopera
    res = developer_manager.get_developer_resources(usi_dev_id)
    if res and res.get("base_dir"):
        dev_dir = Path(res["base_dir"])
            
        if dev_dir.exists():
            # Sprawdzenie obecności fizycznego pliku graficznego
            for ext in ['png', 'jpg', 'jpeg', 'webp', 'svg']:
                logo_path = dev_dir / f"logo.{ext}"
                if logo_path.exists():
                    return send_file(logo_path)
                    
    # Pancerne rozwiązanie: Wbudowany, elegancki placeholder SVG zamiast wywalania 500 lub 404
    fallback_svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">'
        '<rect width="100" height="100" fill="#f1f5f9" rx="12"/>'
        '<path d="M30 75V25H55V35H70V75H30Z" fill="none" stroke="#94a3b8" stroke-width="4" stroke-linejoin="round"/>'
        '<path d="M38 35H47M38 47H47M38 59H47M60 47H64M60 59H64" stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>'
        '</svg>'
    )
    
    # POPRAWKA: Użycie current_app zamiast investments_bp
    response = current_app.response_class(fallback_svg, mimetype='image/svg+xml')
    response.headers["Cache-Control"] = "public, max-age=86400, immutable"
    return response

def _parse_investment_filters(req) -> dict:
    """Parsuje i oczyszcza parametry filtrowania z żądania HTTP."""
    return {
        "onlyUnreviewed": req.args.get("onlyUnreviewed") == "true",
        "onlyNoPhotos": req.args.get("onlyNoPhotos") == "true",
        "dev": req.args.get("dev"),
        "search": req.args.get("search"),
        "portal": req.args.get("portal"),
        "status": req.args.get("status"),
        "cities": req.args.getlist("cities[]") or req.args.getlist("cities"),
        "segments": req.args.getlist("segments[]") or req.args.getlist("segments"),
        "sources": req.args.getlist("sources[]") or req.args.getlist("sources"),
    }

@investments_bp.route("/investments", methods=["GET"])
def list_investments():
    filters = _parse_investment_filters(request)
    print(f"DEBUG FILTERS: {filters}")
    try:
        all_invs = inv_index.load(Path(USI_DATA_DIR)) or []
        results = filter_investments(all_invs, filters) if any(filters.values()) else all_invs

        unreviewed_count = sum(1 for inv in all_invs if inv.get("reviewed") is False)
        ratings_map = {
            i.get("usi_inv_id"): i.get("ratings")
            for i in all_invs
            if i.get("ratings") and i.get("usi_inv_id")
        }
        return jsonify({"data": results, "unreviewedCount": unreviewed_count, "ratingsMap": ratings_map, "totalCount": len(all_invs)}), 200
    except Exception as e:
        logger.error(f"Failed to list investments: {e}")
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route("/investments/nearby", methods=["GET"])
def get_nearby_investments_api():
    lat_raw = request.args.get("lat")
    lon_raw = request.args.get("lon")
    exclude_id = request.args.get("exclude_id") or request.args.get("current_id")

    if not lat_raw or not lon_raw:
        return jsonify({"error": "Missing required float parameters: 'lat' and 'lon'"}), 400
    try:
        lat = float(lat_raw)
        lon = float(lon_raw)
    except ValueError:
        return jsonify({"error": "Coordinates 'lat' and 'lon' must be valid float numbers"}), 400
    try:
        radius = float(request.args.get("radius", 8.0))
        limit = int(request.args.get("limit", 24))
    except ValueError:
        return jsonify({"error": "Parameter 'radius' must be a float, and 'limit' must be an integer"}), 400
    if radius <= 0 or limit <= 0:
        return jsonify({"error": "Parameters 'radius' and 'limit' must be strictly positive values"}), 400
    try:
        raw_results = inv_index.get_investment_index().get_near_coordinates(lat, lon, radius, limit + 1)
        results = [inv for inv in raw_results if inv.get("usi_inv_id") != exclude_id][:limit]
        response = jsonify({"status": "ok", "count": len(results), "data": results})
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response, 200
    except Exception as e:
        logger.error(f"Spatial query failed for lat={lat}, lon={lon}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during spatial processing"}), 500


@investments_bp.route("/investments/rebuild-index", methods=["POST"])
def rebuild_index():
    def _run_rebuild(job_id):
        try:
            job_manager.update_job(job_id, status="running", message="Budowanie indeksu inwestycji...")
            count = inv_index.get_investment_index().rebuild()
            job_manager.update_job(job_id, status="done", message=f"Indeks gotowy: {count} inwestycji")
        except Exception as e:
            job_manager.update_job(job_id, status="error", message=str(e))
    job_id = job_manager.start_job("rebuild-index", _run_rebuild)
    return jsonify({"job_id": job_id})

@investments_bp.route("/investment/<system_id>/data")
def get_investment_data(system_id):
    """Pobiera dane inwestycji. O(1) — bezpośredni odczyt pliku JSON z indeksu."""
    if not system_id:
        abort(400)
    entry = get_shared_repository().get_investment_json(system_id)
    if entry:
        response = jsonify(entry)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        return response
    abort(404)

@investments_bp.route("/investment/<system_id>/ratings", methods=["POST"])
def save_ratings(system_id):
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "Missing payload"}), 400
    success = _get_editor().save_ratings(system_id, payload)
    if not success:
        return jsonify({"error": f"Investment {system_id} not found or save failed"}), 404
    return jsonify({"ok": True, "status": "success"}), 200

@investments_bp.route("/investment/<system_id>/mark-delete", methods=["POST"])
def save_deletion_list(system_id):
    """Usuwa zdjęcia z tablicy photos bezpośrednio w pliku JSON."""
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        abort(400, "paths must be a list")

    data = get_shared_repository().get_investment_json(system_id)
    if not data:
        abort(404, "Investment not found")

    paths_set = set(paths)
    original_count = len(data.get("photos", []))
    data["photos"] = [p for p in data.get("photos", []) if p not in paths_set]
    data.pop("photos_to_delete", None)  # usuń legacy pole

    try:
        get_shared_repository().save_investment_json(system_id, data)
    except Exception as e:
        logger.error(f"Failed to save investment {system_id}: {e}")
        return jsonify({"error": "Failed to save data"}), 500

    inv_index.upsert(USI_DATA_DIR, None, inv_id=system_id)
    removed = original_count - len(data["photos"])
    return jsonify({"ok": True, "removed": removed, "remaining": len(data["photos"])})

@investments_bp.route("/investment/<system_id>/reload", methods=["POST"])
def reload_investment(system_id):
    success = _get_sync().update_investment(system_id)
    if not success:
        return jsonify({"ok": False, "error": "Failed to update"}), 500
    inv_index.upsert(USI_DATA_DIR, None, inv_id=system_id)
    updated_inv = get_shared_repository().get_investment_json(system_id)
    return jsonify({"ok": True, "investment": updated_inv})

@investments_bp.route("/investment/<system_id>/recalc-nearby", methods=["POST"])
def recalc_nearby(system_id):
    inv = get_shared_repository().get_investment_json(system_id)
    if not inv:
        abort(404)
    return jsonify({"ok": True, "investment": inv})

@investments_bp.route("/investment/<system_id>/open-folder", methods=["POST"])
def open_investment_folder(system_id):
    import subprocess
    from python_worker.services.investment_identity import InvestmentIdentityResolver
    from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR
    
    resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)
    resources = resolver.get_investment_resources(system_id)
    if not resources or not resources.get("base_dir") or not resources["base_dir"].exists():
        abort(404, "Katalog inwestycji nie istnieje na dysku")
        
    subprocess.call(["open", str(resources["base_dir"])])
    return jsonify({"status": "ok"})

@investments_bp.route("/investment/<system_id>/refresh", methods=["POST"])
def refresh_investment_route(system_id):
    inv = get_shared_repository().get_investment_json(system_id)
    if not inv:
        abort(404)

    def run_refresh_job(job_id, i_name, system_id, members):
        try:
            sync = _get_sync()
            targets = [system_id] + [m.get("usi_inv_id") for m in members if m.get("usi_inv_id")]
            total = len(targets)
            success_count = 0
            for idx_i, target_id in enumerate(targets):
                job_manager.update_progress(job_id, int(10 + (idx_i / total) * 80), f"Odświeżanie [{idx_i+1}/{total}]: {target_id}")
                if sync.update_investment(target_id):
                    success_count += 1
            if success_count > 0:
                job_manager.update_progress(job_id, 100, f"Ukończono odświeżanie: {i_name} ({success_count}/{total})")
            else:
                job_manager.update_progress(job_id, 100, f"Brak danych do odświeżenia: {i_name}", status="failed")
        except Exception as e:
            logger.exception(f"Exception during refresh job for {system_id}: {e}")
            job_manager.update_progress(job_id, 100, f"Wyjątek: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Refresh: {inv.get('name', system_id)}", run_refresh_job, inv.get('name', system_id), system_id, inv.get("members", []))
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/investment/<system_id>/download-raw", methods=["POST"])
def download_raw_route(system_id):
    try:
        data = get_shared_repository().get_investment_json(system_id)
        if not data:
            abort(404)
        sources = data.get("sources", {})
        sync = _get_sync()
        success = False
        for p in ["rp", "oto", "to"]:
            if p in sources:
                identifier = sources[p].get("id") or sources[p].get("url")
                if identifier and sync.download_raw_json(p, identifier, system_id):
                    success = True
        return jsonify({"ok": success})
    except Exception as e:
        logger.error(f"API Error in {request.path}: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@investments_bp.route("/stats")
def get_stats():
    data_root = Path(USI_DATA_DIR)
    count = sum(1 for dev in data_root.iterdir() if dev.is_dir()
                for inv in dev.iterdir() if inv.is_dir() and list(inv.glob("usi_*.json"))) if data_root.exists() else 0
    return jsonify({"count": count})


# ── Developer API ──────────────────────────────────────────────────────────────

@investments_bp.route("/developers")
def list_developers():
    import time
    cache_key = request.full_path

    # Check if cache is still valid
    with _list_dev_lock:
        if cache_key in _list_dev_cache:
            entry = _list_dev_cache[cache_key]
            if (time.time() - entry["timestamp"]) < 30:
                logger.info(f"Returning cached developers list for {cache_key}")
                return jsonify(entry["data"])

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
    
    # Update cache
    with _list_dev_lock:
        _list_dev_cache[cache_key] = {
            "data": devs,
            "timestamp": time.time()
        }

    t3 = time.time()
    logger.info(f"[TIMING] /developers - total: {t3-t0:.3f}s")
    
    return jsonify(devs)


from python_worker.services.developer_service import DeveloperService

@investments_bp.route("/developer/badge-reset/<usi_dev_id>", methods=["POST"])
def badge_reset(usi_dev_id):
    """
    Zeruje licznik nowych inwestycji odkrytych od ostatniego przeglądu dewelopera.
    """
    dev_data = developer_manager.get_developer_by_id(usi_dev_id)
    if not dev_data:
        abort(404)

    dev_data["new_since_review"] = 0
    developer_manager.create_developer_file(dev_data)
    return jsonify({"ok": True})

@investments_bp.route("/developer/<usi_dev_id>/refresh", methods=["POST"])
def refresh_developer_route(usi_dev_id):
    """
    Asynchroniczne odświeżenie profilu dewelopera ze wszystkich sparowanych platform.
    Gwarantuje nieblokowanie wątku głównego aplikacji poprzez użycie job_managera.
    """
    dev_data = developer_manager.get_developer_by_id(usi_dev_id)
    if not dev_data:
        abort(404, description="Developer not found")
        
    dev_name = dev_data.get("name", usi_dev_id)
    
    def run_dev_refresh_job(job_id, d_id, d_name):
        job_manager.update_progress(job_id, 10, f"Inicjalizacja pobierania danych dla: {d_name}")
        try:
            dev_service = DeveloperService(Path(USI_DATA_DIR), Path(USI_DATA_DIR).parent / "USIdev")
            success = dev_service.update_developer_profile(d_id)
            
            dev_service.record_maintenance(dev_data.get("developer_slug"), success=success)
            
            if success:
                job_manager.update_progress(job_id, 100, f"Dane dewelopera {d_name} zostały pomyślnie zaktualizowane.")
            else:
                job_manager.update_progress(job_id, 100, f"Brak zmian lub błąd podczas odświeżania profilu {d_name}.", status="failed")
        except Exception as e:
            logger.exception(f"Critical failure inside dev refresh job {job_id}: {e}")
            job_manager.update_progress(job_id, 100, f"Błąd krytyczny: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Refresh Deweloper: {dev_name}", run_dev_refresh_job, usi_dev_id, dev_name)
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/developer/<usi_dev_id>")
def get_developer_detail(usi_dev_id):
    """Pobiera pełne dane dewelopera (agregacja inwestycji, logów, sugestii)."""
    dev = developer_service.get_developer_enriched(usi_dev_id)
    if not dev:
        abort(404)
        
    # Wymuszamy brak jakiegokolwiek cache'owania HTTP dla tego widoku
    response = jsonify(dev)
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


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
            count = results if isinstance(results, int) else len(results)
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
    if not source_id:
        return jsonify({"ok": False, "error": "Missing source_id"}), 400
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if not im.merge_by_id(target_id=system_id, source_id=source_id):
        return jsonify({"ok": False, "error": "Merge failed — check server logs"}), 422
    updated = get_shared_repository().get_investment_json(system_id)
    return jsonify({"ok": True, "updated": updated})


@investments_bp.route("/investment/<system_id>/unmerge", methods=["POST"])
def unmerge_investment(system_id):
    payload = request.get_json() or {}
    source_id = payload.get("source_id")
    if not source_id:
        return jsonify({"ok": False, "error": "Missing source_id"}), 400
    from python_worker.investment_merger import InvestmentMerger
    im = InvestmentMerger()
    if not im.unmerge_by_id(target_id=system_id, source_id=source_id):
        return jsonify({"ok": False, "error": "Unmerge failed — check server logs"}), 422
    updated = get_shared_repository().get_investment_json(system_id)
    return jsonify({"ok": True, "updated": updated})


@investments_bp.route("/investment/<system_id>/review", methods=["POST"])
def mark_reviewed(system_id):
    if _get_editor().mark_as_reviewed(system_id):
        return jsonify({"ok": True})
    abort(404, "Investment update failed")

@investments_bp.route("/investment/<system_id>/add-report", methods=["POST"])
def add_report(system_id):
    payload = request.get_json(silent=True) or {}
    note = payload.get("note")
    if not note:
        abort(400, "note is required")
    success = _get_editor().add_report(system_id, note)
    if success:
        return jsonify({"ok": True})
    abort(404, "Failed to add report")
@investments_bp.route("/register-bulk", methods=["POST"])
def register_bulk():
    payload = request.get_json()
    from python_worker.services.scraper_gateway import ScraperGateway
    try:
        portal = ScraperGateway.normalize_portal_name(payload.get("portal", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    investments = payload.get("investments", [])
    if not investments:
        return jsonify({"error": "Missing investments list"}), 400

    def run_bulk_job(job_id, p, invs):
        def progress_wrapper(report):
            msg = report.get("message", "Przetwarzanie danych...")
            percent = report.get("progress_percent", 0)
            job_manager.update_progress(job_id, percent, msg)
        try:
            _get_sync().process_batch(p, invs, on_progress_callback=progress_wrapper)
            job_manager.update_progress(job_id, 100, f"Zakończono pobieranie zbiorcze ({len(invs)} pozycji)")
        except Exception as e:
            logger.error(f"Bulk job error: {e}")
            job_manager.update_progress(job_id, 100, f"Błąd zadania zbiorczego: {str(e)}", status="failed")

    job_id = job_manager.start_job(f"Bulk Register: {portal.upper()} ({len(investments)})", run_bulk_job, portal, investments)
    return jsonify({"ok": True, "job_id": job_id})

@investments_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json() or {}
    raw_portal = payload.get("portal", "")
    try:
        from python_worker.services.scraper_gateway import ScraperGateway
        portal = ScraperGateway.normalize_portal_name(raw_portal)
        sync = _get_sync()
        dev_name = payload.get("developer_name")
        if dev_name and dev_name.lower() in ("nieznany deweloper", "unknown", ""):
            dev_name = None
        dev_slug, inv_slug, usi_inv_id, data, path = sync.register_investment(
            portal=portal, developer_name=dev_name, name=payload.get("name"),
            item_id=payload.get("id"), url=payload.get("url"),
            vendor_id=payload.get("vendor_id"), allow_existing=True
        )
        return jsonify({"ok": True, "usi_inv_id": usi_inv_id, "slug": f"{dev_slug}/{inv_slug}", "message": "Rejestracja zakończona sukcesem"}), 200
    except ValueError as e:
        logger.warning(f"Registration failed - bad input: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Registration critical error: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route('/investments/group-records', methods=['POST'])
def group_records():
    data = request.get_json() or {}
    source_id = data.get('source_id')
    target_id = data.get('target_id')
    if not source_id or not target_id:
        return jsonify({"error": "Missing source_id or target_id"}), 400
    try:
        from python_worker.services.investment_group_service import InvestmentGroupService
        group_service = InvestmentGroupService()
        master_id = group_service.create_or_extend_group(source_id, target_id)
        return jsonify({"status": "success", "master_id": master_id}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
