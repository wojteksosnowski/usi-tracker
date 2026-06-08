import json
import logging
import os
import threading
import time
from pathlib import Path
from urllib.parse import unquote
from flask import Blueprint, jsonify, abort, request, send_file, redirect, send_from_directory
from werkzeug.utils import safe_join

from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename
import python_worker.investment_index as inv_index
import python_worker.developer_index as dev_index
from python_worker.config import PUBLIC_USI_DIR, USI_DATA_DIR, USI_DEV_DIR, get_shared_config, get_shared_fetcher, get_shared_tech_manager
from usi_scrapers import api as scraper_api

logger = logging.getLogger(__name__)

# Przeniesione z wnętrza funkcji stałe globalne (Zgodność z PEP 8)
_PLACEHOLDER_DIR = Path(__file__).parent.parent.parent / "ui" / "assets"
_PLACEHOLDER_FILE = _PLACEHOLDER_DIR / "image-placeholder.svg"



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
    """
    Pancerna wersja obsługująca URL-encoded znaki (%20, %7B, itp.).
    Eliminuje pętle rglob/skanowanie dysku przy nieprawidłowo zmapowanych ścieżkach.
    """
    if not filepath:
        abort(400)

    # KRYTYCZNA POPRAWKA: Odkodowanie znaków procenta (%20 -> spacja, %7B -> {)
    # Przed tą poprawką os.path.exists() zwracało False i odpalało morderczy dla CPU fallback skanowania dysku.
    decoded_filepath = unquote(filepath)

    # Bezpieczne łączenie odkodowanej ścieżki do katalogu PUBLIC_USI_DIR (tam są zdjęcia)
    target_path = safe_join(str(PUBLIC_USI_DIR), decoded_filepath)
    
    # Sprawdzamy fizyczną ścieżkę - operacja O(1), zero narzutu CPU
    if target_path and os.path.exists(target_path):
        response = send_file(target_path, conditional=False)
        response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response

    # BEZLITOSNA BLOKADA: Jeśli plik nie istnieje, NATYCHMIAST zwracamy placeholder.
    # Zakaz jakiegokolwiek rglob(), glob() czy szukania plików na dysku Dropboxa!
    if _PLACEHOLDER_FILE.exists():
        response = send_file(_PLACEHOLDER_FILE, mimetype="image/svg+xml")
        response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response

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
    investments = entries or []

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
def get_investment_data(system_id):
    """
    Zwraca pełne, zunifikowane dane inwestycji bezpośrednio z pamięci podręcznej indeksu.
    Gwarantuje zgodność struktury danych z frontendem, likwiduje pętle żądań i CPU spike.
    """
    if not system_id:
        abort(400)

    # KRYTYCZNA POPRAWKA: Pobieramy dane bezpośrednio z pamięci RAM (inv_index).
    # Indeks zawiera w 100% zunifikowane dane, poprawne tablice 'photos' ze wszystkimi 7 zdjęciami.
    try:
        # Uwaga: get_entry_by_id przyjmuje tylko system_id, korzystając z globalnego gorącego indeksu.
        raw_entry = inv_index.get_entry_by_id(system_id)
        if raw_entry:
            # Tworzymy kopię, aby nie modyfikować globalnego cache'u w pamięci RAM
            entry = raw_entry.copy()
            
            # Gwarantujemy istnienie struktury wymaganej przez frontend, aby zatrzymać rerender loop
            if "specifications" not in entry:
                entry["specifications"] = {}
            
            photos = entry.get("photos", [])
            if not photos:
                entry["photos"] = []
                
            logger.info(f"get_investment_data: Returning {len(photos)} photos for {system_id} from index memory")
            
            response = jsonify(entry)
            # Wymuszamy brak cache'u dla danych, aby frontend zawsze widział pełną galerię po przebudowie indeksu
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            return response
    except Exception as e:
        logger.error(f"[PERF_ALERT] Failed to fetch investment {system_id} from index memory: {e}")

    # Awaryjny fallback na wypadek, gdyby nowa inwestycja nie była jeszcze w indeksie
    tech_manager = get_shared_tech_manager()
    if tech_manager:
        try:
            res = tech_manager.get_investment_technical_data(system_id)
            if res:
                return jsonify(res)
        except Exception as e:
            logger.error(f"Tech manager failed for fallback: {e}")

    abort(404)

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
    import time
    from pathlib import Path
    import json
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR

    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    dev = dm.get_developer_by_id(usi_dev_id)
    
    if not dev: 
        abort(404)

    target_id = dev.get("usi_dev_id")

    # Inicjalizacja indeksu inwestycji
    import python_worker.investment_index as inv_index
    all_invs = inv_index.load(USI_DATA_DIR) or []
    
    base_invs = []
    invs_by_dev_id = {}
    
    # MANDAT ID-ONLY: Inwestycje przypisujemy WYŁĄCZNIE po usi_dev_id.
    # Uzupełnienie: Jako ID traktujemy również dopasowanie po technicznych portal_id z źródeł (user hint).
    target_pm = dev.get("portal_mapping", {})
    for i in all_invs:
        did = i.get("usi_dev_id")
        is_match = False
        
        if did:
            s_did = str(did)
            invs_by_dev_id.setdefault(s_did, []).append(i)
            if s_did == str(target_id):
                is_match = True
        
        if not is_match and _inv_matches_dev(i, target_pm):
            is_match = True
            
        if is_match:
            base_invs.append(i)
            
    # Ładowanie historii zdarzeń
    events = []
    res_info = dm.get_developer_resources(usi_dev_id)
    if res_info and "files" in res_info and res_info["files"].get("logs"):
        log_files = res_info["files"]["logs"]
        if log_files:
            log_path = Path(log_files[0])
            if log_path.exists():
                try:
                    with open(log_path, "r", encoding="utf-8") as lf:
                        for line in lf:
                            if line.strip():
                                events.append(json.loads(line.strip()))
                except Exception as le:
                    logger.warning(f"Nie udało się odczytać dziennika zdarzeń dla {usi_dev_id}: {le}")
    dev["events"] = sorted(events, key=lambda x: x.get("at", ""), reverse=True)

    # Transformacja na rzecz maintenance
    dev_service = DeveloperService(Path(USI_DATA_DIR), Path(USI_DATA_DIR).parent / "USIdev")
    crawler = dev.setdefault("crawler", {})
    maintenance_score = dev_service.get_maintenance_overdue_score(dev)
    
    crawler["last_visit"] = dev.get("last_maintenance", None)
    crawler["last_new_count"] = dev.get("new_since_review", 0)
    crawler["next_visit"] = "Wymaga uwagi" if maintenance_score > 500 else "Zintegrowany"
    dev["maintenance_overdue_score"] = maintenance_score

    # Skład rekordu
    base_pm = (dev.get("original_portal_mapping") or dev.get("portal_mapping") or {}).copy()
    valid_members = []
    
    for member in dev.get("merged_from", []):
        child_id = member.get("usi_dev_id")
        child_dev = dm.get_developer_by_id(child_id) if child_id else None
        if not child_dev or str(child_dev.get("usi_dev_id")) == str(dev.get("usi_dev_id")):
            continue
            
        member["slug"] = child_dev.get("developer_slug")
        child_pm = (child_dev.get("original_portal_mapping") or child_dev.get("portal_mapping") or {}).copy()
        member["_pm"] = child_pm
        member["_dev"] = child_dev
        
        # MANDAT ID-ONLY: Pobieramy inwestycje po ID oraz po portal_id (user hint)
        child_invs = list(invs_by_dev_id.get(str(child_id), []))
        # Dodajemy inwestycje pasujące po portal_id do tego dziecka
        for i in all_invs:
            if _inv_matches_dev(i, child_pm):
                iid = i.get("usi_inv_id")
                if iid and not any(ci.get("usi_inv_id") == iid for ci in child_invs):
                    child_invs.append(i)
        
        member["_invs"] = child_invs
        valid_members.append(member)

    # Budowa bazy (Root record)
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
        
        for p, pdata in m["_pm"].items():
            if not aggregated_pm.get(p) and pdata:
                aggregated_pm[p] = pdata
        
        for inv in m["_invs"]:
            iid = inv.get("usi_inv_id")
            if iid and iid not in existing_inv_ids:
                investments.append(inv)
                existing_inv_ids.add(iid)
        
        m.pop("_pm", None); m.pop("_dev", None); m.pop("_invs", None)
        final_members.append(m)

    dev["merged_from"] = final_members
    merged_ids = {str(m.get("usi_dev_id")) for m in final_members if m.get("usi_dev_id")}

    # --- BEZPIECZNE SUGESTIE: PASYWNY ODCZYT + RAM REVERSE LOOKUP ---
    # Całkowicie rezygnujemy z uruchamiania silnika LIVE podczas żądania GET.
    # Zapobiega to wydłużeniu czasu ładowania i "mieszaniu" danych przez błędy parowania w locie.
    suggestions_dict = {str(s.get("usi_dev_id") or s.get("target_id")): s for s in dev.get("suggestions", []) if (s.get("usi_dev_id") or s.get("target_id"))}

    try:
        # Pobieramy pełny stan deweloperów z hot-cache pamięci RAM (Zero Disk I/O)
        # Służy tylko do wykrycia czy inni mają sugestie skierowane do nas.
        all_devs_cached = dm.list_developers() or []
        for other_dev in all_devs_cached:
            other_id = other_dev.get("usi_dev_id")
            if not other_id or str(other_id) == str(target_id):
                continue
                
            for other_sug in other_dev.get("suggestions", []):
                if str(other_sug.get("usi_dev_id") or other_sug.get("target_id")) == str(target_id) and other_sug.get("score", 0) >= 0.75:
                    if str(other_id) not in suggestions_dict:
                        suggestions_dict[str(other_id)] = {
                            "usi_dev_id": other_id,
                            "target_id": other_id,
                            "developer_slug": other_dev.get("developer_slug"),
                            "reason": f"[Relacja zwrotna] {other_sug.get('reason')}",
                            "score": other_sug.get("score", 0.0)
                        }
    except Exception as cache_err:
        logger.error(f"Błąd budowania relacji zwrotnych: {cache_err}")

    valid_suggestions = []
    for s_id, s in suggestions_dict.items():
        if s_id in merged_ids or s_id == str(target_id):
            continue

        s_dev = dm.get_developer_by_id(s_id)
        if s_dev:
            valid_suggestions.append({
                "usi_dev_id": s_id,
                "target_id": s_id,
                "developer_slug": s_dev.get("developer_slug", "unknown"),
                "name": s_dev.get("name", s_id),
                "reason": s.get("reason", "Podobieństwo systemowe"),
                "score": s.get("score", 1.0),
                "portal_mapping": s_dev.get("portal_mapping", {}),
                "website": s_dev.get("website"),
                "investments_count": len(invs_by_dev_id.get(s_id, []))
            })

    dev["suggestions"] = valid_suggestions
    dev["investments"] = investments
    dev["investments_count"] = len(investments)
    dev["portal_mapping"] = aggregated_pm
    
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
