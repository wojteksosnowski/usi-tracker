import json
import logging
from flask import Blueprint, jsonify, abort, request, send_file
from python_worker.services.investment_service import InvestmentService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug, _valid_filename

logger = logging.getLogger(__name__)

investments_bp = Blueprint('investments', __name__)
investment_service = InvestmentService()

@investments_bp.route("/image/<dev_slug>/<inv_slug>/<filename>")
def serve_image(dev_slug, inv_slug, filename):
    from python_worker.config import PUBLIC_USI_DIR
    from pathlib import Path
    if not _valid_slug(dev_slug) or not _valid_slug(inv_slug) or not _valid_filename(filename):
        abort(400)
    img_path = Path(PUBLIC_USI_DIR) / dev_slug / inv_slug / filename
    if not img_path.exists():
        abort(404)
    return send_file(img_path)

@investments_bp.route("/investments")
def list_investments():
    investments = []
    data_root = investment_service.data_dir
    if not data_root.exists():
        return jsonify([])

    for dev_dir in sorted(data_root.iterdir()):
        if not dev_dir.is_dir(): continue
        for inv_dir in sorted(dev_dir.iterdir()):
            if not inv_dir.is_dir(): continue
            inv = investment_service.get_investment(dev_dir.name, inv_dir.name)
            if inv: investments.append(inv)
    return jsonify(investments)

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
        return jsonify({"error": str(e)}), 500

@investments_bp.route("/fetch-status")
def fetch_status():
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    data_root = Path(USI_DATA_DIR)
    count = sum(1 for dev in data_root.iterdir() if dev.is_dir()
                for inv in dev.iterdir() if inv.is_dir() and list(inv.glob("usi_*.json"))) if data_root.exists() else 0
    return jsonify({"count": count})

# ── Developer API ──────────────────────────────────────────────────────────────

@investments_bp.route("/developers")
def list_developers():
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    developers = dm.list_developers()
    developers.sort(key=lambda x: x.get("name", "").lower())
    for dev in developers:
        slug = dev["developer_slug"]
        inv_dir = Path(USI_DATA_DIR) / slug
        if inv_dir.exists():
            inv_dirs = [d for d in inv_dir.iterdir() if d.is_dir()]
            dev["investments_count"] = len(inv_dirs)
            mtimes = []
            for d in inv_dirs:
                usi_files = list(d.glob("usi_*.json"))
                if usi_files:
                    mtimes.append(usi_files[0].stat().st_mtime)
            dev["last_updated"] = max(mtimes) if mtimes else None
        else:
            dev["investments_count"] = 0
            dev["last_updated"] = None
        # Crawler badge
        dev["new_since_review"] = dev.get("crawler", {}).get("new_since_review", 0)
    return jsonify(developers)

@investments_bp.route("/developer/<dev_slug>")
def get_developer_detail(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from python_worker.api.utils import _load_investment
    from pathlib import Path
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    dev = dm.get_developer(dev_slug)
    if not dev: abort(404)

    target_id = dev.get("usi_dev_id")

    # Collect investments from this dev and all children (merged_from)
    def _load_inv_dir(d_slug: str) -> list:
        result = []
        d = Path(USI_DATA_DIR) / d_slug
        if d.exists():
            for inv_dir in d.iterdir():
                if inv_dir.is_dir() and not inv_dir.name.startswith("."):
                    inv = _load_investment(d_slug, inv_dir.name)
                    if inv: result.append(inv)
        return result

    investments = _load_inv_dir(dev_slug)

    # Enrich merged_from entries with portal_mapping and investments_count
    for member in dev.get("merged_from", []):
        child_slug = member.get("slug")
        if not child_slug or child_slug == dev_slug:
            continue
        investments.extend(_load_inv_dir(child_slug))
        child_dev = dm.get_developer(child_slug)
        if child_dev:
            member["portal_mapping"] = child_dev.get("portal_mapping", {})
            child_dir = Path(USI_DATA_DIR) / child_slug
            member["investments_count"] = sum(
                1 for d in child_dir.iterdir() if d.is_dir()
            ) if child_dir.exists() else 0

    # Enrich suggestions with portal_mapping, name, investments_count
    for s in dev.get("suggestions", []):
        s_slug = s.get("developer_slug")
        if not s_slug:
            continue
        s_dev = dm.get_developer(s_slug)
        if s_dev:
            s["name"] = s_dev.get("name", s_slug)
            s["portal_mapping"] = s_dev.get("portal_mapping", {})
            s_dir = Path(USI_DATA_DIR) / s_slug
            s["investments_count"] = sum(
                1 for d in s_dir.iterdir() if d.is_dir()
            ) if s_dir.exists() else 0

    dev["investments"] = investments
    return jsonify(dev)

@investments_bp.route("/developer/<dev_slug>/merge", methods=["POST"])
def merge_developer(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    from python_worker.developer_manager import DeveloperManager
    from python_worker.config import USI_DATA_DIR
    from pathlib import Path
    payload = request.get_json() or {}
    source_slug = payload.get("source_slug")
    if not source_slug or not _valid_slug(source_slug):
        abort(400)
    try:
        dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
        if dm.merge_developers(dev_slug, source_slug):
            return jsonify({"ok": True})
        return jsonify({"ok": False, "error": "Merge failed — check server logs"}), 422
    except Exception as e:
        logger.exception("merge_developer error: %s", e)
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
    if not suggested_id: abort(400)
    dm = DeveloperManager(USI_DATA_DIR, Path(USI_DATA_DIR).parent / "USIdev")
    if dm.dismiss_suggestion(dev_slug, suggested_id):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 500

@investments_bp.route("/register", methods=["POST"])
def register():
    payload = request.get_json()
    try:
        portal = payload.get("portal", "")
        if "rynekpierwotny" in portal or portal == "rp": portal = "rp"
        elif "otodom" in portal or portal == "oto": portal = "oto"
        elif "tabelaofert" in portal or portal == "to": portal = "to"

        dev_slug, inv_slug = investment_service.register_investment(
            portal=portal,
            developer_name=payload.get("developer_name"),
            inv_slug=payload.get("inv_slug"),
            name=payload.get("name"),
            item_id=payload.get("id"),
            url=payload.get("url")
        )

        def run_register_job(job_id, d_slug, i_slug, inv_name):
            job_manager.update_progress(job_id, 10, f"Rozpoczęto pobieranie: {inv_name}")
            if investment_service.update_investment(d_slug, i_slug):
                job_manager.update_progress(job_id, 100, f"Ukończono: {inv_name}")
            else:
                job_manager.update_progress(job_id, 100, f"Błąd pobierania: {inv_name}", status="failed")

        job_id = job_manager.start_job(f"Register: {payload.get('name')}", run_register_job, dev_slug, inv_slug, payload.get('name'))
        return jsonify({"ok": True, "job_id": job_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
