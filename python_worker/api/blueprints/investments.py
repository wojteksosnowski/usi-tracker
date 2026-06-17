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

from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename, get_anchor_path, update_anchor_json, filter_investments
import python_worker.developer_index as dev_index
import python_worker.investment_index as inv_index
from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR, USI_DEV_DIR, get_shared_config, get_shared_fetcher, get_shared_tech_manager
from usi_scrapers import api as scraper_api

logger = logging.getLogger(__name__)

# Przeniesione z wnętrza funkcji stałe globalne (Zgodność z PEP 8)
_PLACEHOLDER_DIR = Path(__file__).parent.parent.parent / "ui" / "assets"
_PLACEHOLDER_FILE = _PLACEHOLDER_DIR / "image-placeholder.svg"


investments_bp = Blueprint('investments', __name__)
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.services.developer_service import DeveloperService

investment_service = InvestmentService()
developer_manager = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
developer_service = DeveloperService(Path(USI_DATA_DIR), Path(USI_DATA_DIR).parent / "USIdev")

# Rejestracja po zmianie będzie bezpieczna - wyczyści tylko słownik RAM serwisu
inv_index.on_change(investment_service.invalidate_cache)

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
    from python_worker.services.investment_service import InvestmentService
    service = InvestmentService()
    
    filters = _parse_investment_filters(request)
    print(f"DEBUG FILTERS: {filters}")
    try:
        results = service.list_investments_filtered(**filters)
        
        # Odtworzenie struktury wymaganej przez data.jsx
        all_invs = inv_index.load(Path(USI_DATA_DIR)) or []
        unreviewed_count = sum(1 for inv in all_invs if inv.get("reviewed") is False)
        
        # Build ratingsMap for nearby investments fallback when filtered
        ratings_map = {
            i.get("usi_inv_id"): i.get("ratings")
            for i in all_invs
            if i.get("ratings") and i.get("usi_inv_id")
        }
        
        return jsonify({"data": results, "unreviewedCount": unreviewed_count, "ratingsMap": ratings_map}), 200
    except Exception as e:
        logger.error(f"Failed to list investments: {e}")
        return jsonify({"error": "Internal server error"}), 500

@investments_bp.route("/investments/nearby", methods=["GET"])
def get_nearby_investments_api():
    """
    Zwraca inwestycje w pobliżu współrzędnych podanych w Query String.
    Parametry: lat (wymagany), lon (wymagany), radius (opcjonalny), limit (opcjonalny), exclude_id (opcjonalny).
    """
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
        radius = float(request.args.get("radius", 5.0))
        limit = int(request.args.get("limit", 12))
    except ValueError:
        return jsonify({"error": "Parameter 'radius' must be a float, and 'limit' must be an integer"}), 400

    if radius <= 0 or limit <= 0:
        return jsonify({"error": "Parameters 'radius' and 'limit' must be strictly positive values"}), 400

    try:
        results = investment_service.list_nearby_by_coordinates(
            lat=lat, 
            lon=lon, 
            max_dist_km=radius, 
            limit=limit,
            exclude_id=exclude_id
        )
        return jsonify({
            "status": "ok",
            "count": len(results),
            "data": results
        }), 200
        
    except Exception as e:
        logger.error(f"Spatial query failed for lat={lat}, lon={lon}: {e}", exc_info=True)
        return jsonify({"error": "Internal server error during spatial processing"}), 500


@investments_bp.route("/investments/rebuild-index", methods=["POST"])
def rebuild_index():
    def _run_rebuild(job_id):
        try:
            job_manager.update_job(job_id, status="running", message="Budowanie indeksu inwestycji...")
            count = investment_service.rebuild_index()
            job_manager.update_job(job_id, status="done", message=f"Indeks gotowy: {count} inwestycji")
        except Exception as e:
            job_manager.update_job(job_id, status="error", message=str(e))

    job_id = job_manager.start_job("rebuild-index", _run_rebuild)
    return jsonify({"job_id": job_id})

@investments_bp.route("/investment/<system_id>/data")
def get_investment_data(system_id):
    """Pobiera pełne dane inwestycji. O(1) z gorącego indeksu RAM."""
    if not system_id:
        abort(400)

    try:
        # Pobieramy zunifikowane dane (agregacja, zdjęcia, oceny) via Service
        entry = investment_service.get_investment(system_id)
        if entry:
            response = jsonify(entry)
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
    except Exception as e:
        logger.error(f"Failed to fetch investment {system_id}: {e}")

    abort(404)

@investments_bp.route("/investment/<system_id>/ratings", methods=["POST"])
def save_ratings(system_id):
    payload = request.get_json(silent=True) or {}
    if not payload:
        return jsonify({"error": "Missing payload"}), 400
        
    success = investment_service.save_ratings(system_id, payload)
    if not success:
        return jsonify({"error": f"Investment {system_id} not found or save failed"}), 404
        
    return jsonify({"ok": True, "status": "success"}), 200

@investments_bp.route("/investment/<system_id>/mark-delete", methods=["POST"])
def save_deletion_list(system_id):
    payload = request.get_json(silent=True) or {}
    paths = payload.get("paths", [])
    if not isinstance(paths, list):
        abort(400, "paths must be a list")
        
    success = investment_service.mark_deleted_photos(system_id, paths)
    if success:
        return jsonify({"ok": True, "count": len(paths)})
    abort(404, "Failed to mark photos as deleted")

@investments_bp.route("/investment/<system_id>/reload", methods=["POST"])
def reload_investment(system_id):
    success = investment_service.update_investment(system_id)
    if not success:
        return jsonify({"ok": False, "error": "Failed to update"}), 500
    
    updated_inv = investment_service.get_investment(system_id)
    return jsonify({"ok": True, "investment": updated_inv})

@investments_bp.route("/investment/<system_id>/recalc-nearby", methods=["POST"])
def recalc_nearby(system_id):
    # Backward compatibility endpoint - nearby investments are now calculated dynamically in the frontend UI.
    inv = investment_service.get_investment(system_id)
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
    inv = investment_service.get_investment(system_id)
    if not inv:
        abort(404)
    
    def run_refresh_job(job_id, i_name, system_id):
        job_manager.update_progress(job_id, 10, f"Rozpoczęto odświeżanie: {i_name}")
        try:
            if investment_service.update_investment(system_id):
                logger.info(f"Finished background refresh for {i_name}.")
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

@investments_bp.route("/developer/suggest", methods=["POST"])
def trigger_suggestions():
    """Triggers the developer similarity algorithm globally (via Doktor)."""
    try:
        from python_worker.daemons import get_doktor
        doktor = get_doktor()
        
        # Jeśli Doktor jest niedostępny, bezpiecznie sprawdzamy alternatywny fallback
        # uruchomienia analizy deweloperów bezpośrednio z poziomu serwisu deweloperskiego
        if not doktor:
            from python_worker.daemons import HAS_CRAWLERS, run_manual_doktor_analysis
            from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
            
            if HAS_CRAWLERS:
                logger.info("Doktor daemon not found, triggering manual similarity analysis fallback.")
                def _run_manual():
                    run_manual_doktor_analysis(Path(USI_DATA_DIR), Path(USI_DEV_DIR))
                
                import threading
                threading.Thread(target=_run_manual, name="manual-dev-similarity-fallback", daemon=True).start()
                return jsonify({"ok": True, "message": "Uruchomiono analizę podobieństwa deweloperów w tle."})
            else:
                logger.warning("Doktor daemon and crawler library both unavailable. Falling back to simple index rebuild.")
                from python_worker.developer_index import rebuild_master_index
                
                def _run_local_fallback():
                    try:
                        rebuild_master_index(Path(USI_DEV_DIR))
                        logger.info("Local fallback developer index rebuild finished.")
                    except Exception as ex:
                        logger.error(f"Local fallback developer index rebuild failed: {ex}")
                
                import threading
                threading.Thread(target=_run_local_fallback, name="manual-dev-refresh-fallback", daemon=True).start()
                return jsonify({"ok": True, "message": "Uruchomiono lokalną przebudowę indeksu deweloperów w tle."})

        # Jeśli doktor istnieje, sprawdzamy bezpiecznie jego metody publiczne
        # Zapobiegamy wywaleniu aplikacji poprzez rygorystyczny duck-typing i bezpieczny wątek
        def _safe_doktor_execution():
            try:
                if hasattr(doktor, "investigate") and callable(doktor.investigate):
                    doktor.investigate()
                elif hasattr(doktor, "refresh") and callable(doktor.refresh):
                    doktor.refresh()
                elif hasattr(doktor, "_refresh_index") and callable(doktor._refresh_index):
                    doktor._refresh_index()
                else:
                    logger.error("Doktor daemon does not expose any known refresh or investigate method!")
            except Exception as thread_err:
                logger.error(f"Error inside background Doktor thread execution: {thread_err}", exc_info=True)

        import threading
        threading.Thread(target=_safe_doktor_execution, name="manual-doktor-refresh", daemon=True).start()
        return jsonify({"ok": True, "message": "Zadanie analizy podobieństwa deweloperów zostało przekazane do demona."})

    except Exception as route_err:
        logger.error(f"Krytyczny błąd w endpoint /developer/suggest: {route_err}", exc_info=True)
        return jsonify({"ok": False, "error": str(route_err)}), 500

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

@investments_bp.route("/developer/<usi_dev_id>/suggest", methods=["POST"])
def trigger_isolated_developer_suggestions(usi_dev_id):
    """
    Uruchamia analizę podobieństwa wyłącznie dla jednego dewelopera.
    Gwarantuje wykonanie dokładnie 1 operacji zapisu dyskowego (izolacja I/O).
    """
    try:
        from python_worker.algorithms.similarity.engine import DeveloperMatcher
        from python_worker.daemons import TrackerDoktorDelegate
        
        # 1. Pobierz profil dewelopera z dysku
        target_dev = developer_manager.get_developer_by_id(usi_dev_id)
        if not target_dev:
            abort(404)
            
        # 2. Załaduj bazę z gotowego indeksu w pamięci RAM (Zero Disk I/O narzutu)
        delegate = TrackerDoktorDelegate(Path(USI_DATA_DIR), Path(USI_DEV_DIR))
        all_developers = delegate.get_developers_for_analysis()
        dismissed = delegate.get_dismissed_cache()
        
        # 3. Wylicz powiązania tylko i wyłącznie dla tego jednego dewelopera
        matcher = DeveloperMatcher()
        suggestions = matcher.find_suggestions_for_developer(target_dev, all_developers, dismissed)
        
        # 4. Rygorystyczny filtr progowy - odcinamy szum o niskim score
        MIN_SCORE = 0.75
        filtered_suggestions = [
            {
                "usi_dev_id": s["target_id"],
                "developer_slug": s["target_slug"],
                "reason": s["reason"],
                "score": s["score"]
            }
            for s in suggestions if s["score"] >= MIN_SCORE
        ]
        
        # 5. Zapis izolowany - modyfikujemy tylko wywołany rekord
        target_dev["suggestions"] = filtered_suggestions
        developer_manager.create_developer_file(target_dev)
        
        # WYMUSZENIE: Aktualizujemy obiekt w globalnej pamięci podręcznej indeksu (RAM),
        # aby inne kontrolery i widoki detaliczne natychmiast zobaczyły nowe, poprawne dane.
        try:
            import python_worker.developer_index as dev_index
            # Invalidate global hot index cache to reflect the disk change
            dev_index.invalidate_cache_for_id(usi_dev_id)
        except (ImportError, AttributeError):
            pass

        logger.info(f"[IO_SUCCESS] Izolowany skan dla {usi_dev_id}. Zapisano 1 plik, wykryto {len(filtered_suggestions)} sugestii.")
        return jsonify({"ok": True, "count": len(filtered_suggestions)})
        
    except Exception as e:
        logger.error(f"Isolated suggest crash: {e}", exc_info=True)
        return jsonify({"ok": False, "error": str(e)}), 500

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

    # 1. Guard clause - jeśli merge się nie udał, wychodzimy natychmiast
    if not im.merge_by_id(system_id, source_id):
        return jsonify({"ok": False, "error": "Merge failed"}), 422

    # 2. Czysta delegacja - zero instrukcji 'if' w prawo
    dm.suggest_merge_from_investments(target_entry, source_entry)
    
    return jsonify({"ok": True})

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
    abort(404, "Investment update failed")

@investments_bp.route("/investment/<system_id>/add-report", methods=["POST"])
def add_report(system_id):
    payload = request.get_json(silent=True) or {}
    note = payload.get("note")
    if not note:
        abort(400, "note is required")

    success = investment_service.add_report(system_id, note)
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
            investment_service.process_batch(p, invs, on_progress_callback=progress_wrapper)
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
        
        result = investment_service.register_investment(portal=portal, payload=payload)
        return jsonify(result), 200
        
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
