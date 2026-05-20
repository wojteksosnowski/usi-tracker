import json
import logging
from pathlib import Path
from flask import Blueprint, jsonify, abort, request, send_file
from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename
import python_worker.investment_index as inv_index

logger = logging.getLogger(__name__)

def _count_valid_investments(dev_dir: Path) -> int:
    """Count investment folders that have a usi_*.json file (loadable investments)."""
    if not dev_dir.exists():
        return 0
    return sum(
        1 for d in dev_dir.iterdir()
        if d.is_dir() and not d.name.startswith('.') and list(d.glob("usi_*.json"))
    )


def _count_portal_investments(inv_dir: Path, dev_portals: set) -> int:
    """Count investments whose sources match at least one of dev_portals."""
    if not dev_portals:
        return _count_valid_investments(inv_dir)
    if not inv_dir.exists():
        return 0
    count = 0
    for sub in inv_dir.iterdir():
        if not sub.is_dir() or sub.name.startswith("."):
            continue
        for uf in sub.glob("usi_*.json"):
            try:
                src = json.loads(uf.read_text(encoding="utf-8")).get("sources") or {}
                if any(src.get(p) for p in dev_portals):
                    count += 1
                    break
            except Exception:
                pass
    return count


def _inv_matches_dev(inv: dict, dev: dict) -> bool:
    """Return True only when a portal developer ID from sources exactly matches portal_mapping.
    No fallback guessing — missing ID means no match."""
    pm = dev.get("portal_mapping") or {}
    src = inv.get("sources") or {}
    for portal in ("rp", "oto", "to"):
        if not pm.get(portal) or not src.get(portal):
            continue
        pm_p = pm[portal]
        src_p = src[portal]
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
            pm_id = str(pm_p.get("id") or pm_p.get("slug", ""))
            src_id = str(src_p.get("id") or "")
            if pm_id and src_id and pm_id == src_id:
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
    if entries is not None:
        return jsonify(entries)

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
    return jsonify(investments)


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
    from pathlib import Path
    inv_dir = Path(USI_DATA_DIR) / dev_slug / inv_slug
    usi_file = inv_dir / f"usi_{inv_slug}.json"
    if not usi_file.exists():
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
    from python_worker.developer_manager import DeveloperManager
    from python_worker.services.discovery_service import DiscoveryService
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    ds = DiscoveryService(USI_DATA_DIR)

    only_merged = request.args.get("only_merged", "false").lower() == "true"

    # Pre-fetch identifiers once for all developers
    identifiers = dm.get_existing_identifiers()

    developers = dm.list_developers(only_merged=only_merged)
    developers.sort(key=lambda x: x.get("name", "").lower())
    for dev in developers:
        slugs = [dev["developer_slug"]]
        slugs.extend([m["slug"] for m in dev.get("merged_from", []) if m.get("slug")])
        
        total_count = 0
        all_mtimes = []
        
        # Aggregate portal mapping from children (non-destructive)
        aggregated_pm = (dev.get("portal_mapping") or {}).copy()
        for member in dev.get("merged_from", []):
            child_id = member.get("usi_dev_id")
            if not child_id: continue
            child_record = dm.get_developer_by_id(child_id)
            if child_record:
                child_pm = child_record.get("portal_mapping") or {}
                for p in ("rp", "oto", "to"):
                    if not aggregated_pm.get(p) and child_pm.get(p):
                        aggregated_pm[p] = child_pm[p]
        
        dev["portal_mapping"] = aggregated_pm
        dev_portals = {p for p in ("rp", "oto", "to") if aggregated_pm.get(p)}

        for slug in slugs:
            inv_dir = Path(USI_DATA_DIR) / slug
            if inv_dir.exists():
                total_count += _count_portal_investments(inv_dir, dev_portals)
                for d in inv_dir.iterdir():
                    if d.is_dir() and not d.name.startswith('.'):
                        for uf in d.glob("usi_*.json"):
                            all_mtimes.append(uf.stat().st_mtime)
                            break

        dev["investments_count"] = total_count
        dev["last_updated"] = max(all_mtimes) if all_mtimes else None
        
        # Crawler badge
        dev["new_since_review"] = dev.get("crawler", {}).get("new_since_review", 0)
        # Discovery snapshot badge
        dev["unregistered_count"] = ds.get_unregistered_count(dev["developer_slug"], identifiers)
        
    return jsonify(developers)

@investments_bp.route("/developer/suggest", methods=["POST"])
def trigger_suggestions():
    """Triggers the developer similarity algorithm globally (via Doktor)."""
    from python_worker.doktor import get_doktor
    doktor = get_doktor()
    if doktor:
        import threading
        # Run it in a separate thread so it doesn't block the UI response
        # It's better than running the old O(N^2) detect_similar
        threading.Thread(target=doktor._refresh_index, name="manual-doktor-refresh", daemon=True).start()
        return jsonify({"ok": True, "message": "Doktor is refreshing the index and investigating."})
    
    # Fallback to old method if Doktor is not available
    from python_worker.detect_similar_devs import detect_similar
    try:
        detect_similar()
        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("trigger_suggestions error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500

@investments_bp.route("/developer/<dev_slug>")
def get_developer_detail(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from python_worker.api.utils import _load_investment
    from pathlib import Path
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    usi_dev_id = request.args.get("id")
    if usi_dev_id:
        dev = dm.get_developer_by_id(usi_dev_id)
    else:
        dev = dm.get_developer(dev_slug)
    if not dev: abort(404)

    target_id = dev.get("usi_dev_id")

    # Helper to load investments from a directory
    def _load_inv_dir(d_slug: str) -> list:
        result = []
        d = Path(USI_DATA_DIR) / d_slug
        if d.exists():
            for inv_dir in d.iterdir():
                if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                    # Find all usi_*.json files in this folder
                    usi_files = list(inv_dir.glob("usi_*.json"))
                    for usi_file in usi_files:
                        # Extract portal from filename: usi_{portal}_{inv_slug}.json
                        parts = usi_file.name.split("_")
                        portal = parts[1] if len(parts) == 3 else None
                        inv = _load_investment(d_slug, inv_dir.name, portal=portal)
                        if inv: result.append(inv)
        return result

    # PRESERVE BASE RECORD: before aggregation, capture the state of the "host" record
    base_pm = (dev.get("portal_mapping") or {}).copy()
    base_portals = {p for p in ("rp", "oto", "to") if base_pm.get(p)}
    base_invs_raw = _load_inv_dir(dev_slug)
    base_invs = [i for i in base_invs_raw if not base_portals or _inv_matches_dev(i, dev)]
    
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

    # Aggregate portal mapping from children (non-destructive)
    aggregated_pm = base_pm.copy()
    for member in dev.get("merged_from", []):
        child_id = member.get("usi_dev_id")
        if not child_id: continue
        child_record = dm.get_developer_by_id(child_id)
        if child_record:
            child_pm = child_record.get("portal_mapping") or {}
            for p in ("rp", "oto", "to"):
                if not aggregated_pm.get(p) and child_pm.get(p):
                    aggregated_pm[p] = child_pm[p]
    
    dev["portal_mapping"] = aggregated_pm
    dev_portals = {p for p in ("rp", "oto", "to") if aggregated_pm.get(p)}

    # Collect investments from this dev and all children (merged_from)
    investments = list(base_invs)

    # Enrich merged_from entries — resolve child by usi_dev_id (not slug)
    for member in dev.get("merged_from", []):
        child_id = member.get("usi_dev_id")
        child_slug = member.get("slug")
        child_dev = (dm.get_developer_by_id(child_id) if child_id
                     else (dm.get_developer(child_slug) if child_slug else None))

        # ARCHITECTURAL FIX: Use ID to prevent self-loop, NEVER slug
        if not child_dev or child_dev.get("usi_dev_id") == dev.get("usi_dev_id"):
            continue

        child_slug = child_dev.get("developer_slug", child_slug)
        member["slug"] = child_slug  # keep for UI display

        # Load and strictly filter child's investments by its portal mapping
        child_portals = {p for p in ("rp", "oto", "to") if (child_dev.get("portal_mapping") or {}).get(p)}
        child_invs_raw = _load_inv_dir(child_slug)
        child_invs = [i for i in child_invs_raw if not child_portals or _inv_matches_dev(i, child_dev)]

        # Deduplicate into main list using ONLY usi_inv_id
        existing_inv_ids = {i.get("usi_inv_id") for i in investments if i.get("usi_inv_id")}
        for ci in child_invs:
            ci_id = ci.get("usi_inv_id")
            if ci_id and ci_id not in existing_inv_ids:
                investments.append(ci)
                existing_inv_ids.add(ci_id)
            elif not ci_id:
                # Fallback for legacy unmigrated data
                investments.append(ci)

        member["portal_mapping"] = child_dev.get("portal_mapping", {})
        member["website"] = child_dev.get("website")
        child_dir = Path(USI_DATA_DIR) / child_slug

        # Count strictly by portal to avoid cross-contamination in shared folders
        member["investments_count"] = _count_portal_investments(child_dir, child_portals)

        member["inv_list"] = [
            {"name": inv.get("name", inv.get("investment_slug", "")), "slug": inv.get("investment_slug", "")}
            for inv in child_invs[:10]
        ]

    # Enrich suggestions — resolve suggested dev by usi_dev_id (not slug)
    for s in dev.get("suggestions", []):
        s_id = s.get("usi_dev_id")
        s_slug = s.get("developer_slug")
        s_dev = (dm.get_developer_by_id(s_id) if s_id
                 else (dm.get_developer(s_slug) if s_slug else None))
        if s_dev:
            s["developer_slug"] = s_dev.get("developer_slug", s_slug)  # refresh slug
            s["name"] = s_dev.get("name", s_slug)
            s["portal_mapping"] = s_dev.get("portal_mapping", {})
            s["website"] = s_dev.get("website")
            s_dir = Path(USI_DATA_DIR) / s_dev["developer_slug"]
            s_portals = {p for p in ("rp", "oto", "to") if (s_dev.get("portal_mapping") or {}).get(p)}
            s["investments_count"] = _count_portal_investments(s_dir, s_portals)

    dev["investments"] = investments
    dev["investments_count"] = len(investments)
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
