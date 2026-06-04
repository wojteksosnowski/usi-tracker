import logging
from flask import Blueprint, jsonify, request, abort
from python_worker.services.discovery_service import DiscoveryService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug

logger = logging.getLogger(__name__)

_VALID_PORTALS = {"rp", "oto", "to"}

discovery_bp = Blueprint('discovery', __name__)
discovery_service = DiscoveryService()

@discovery_bp.route("/developer/<system_id>/discover", methods=["POST"])
def discover_dev_new(system_id):
    if not system_id:
        abort(400)

    def _run_with_event(job_id, s_id, job_manager=None):
        result = discovery_service.discover_for_developer(s_id, job_id=job_id, job_manager=job_manager)
        try:
            from python_worker.api.blueprints.investments import developer_manager
            dm = developer_manager
            dm.log_event(s_id, {"type": "discover", "by": "user", "found": result or 0})
        except Exception:
            pass
        return result

    job_id = job_manager.start_job(
        f"Discovery: {system_id}",
        _run_with_event,
        system_id,
        job_manager=job_manager
    )
    return jsonify({"ok": True, "job_id": job_id})

@discovery_bp.route("/discovery/<portal>/job", methods=["POST"])
def discovery_job(portal):
    if portal not in _VALID_PORTALS:
        return jsonify({"error": f"Unknown portal: {portal}"}), 400
    identifier = request.args.get("id", "").strip()
    limit = request.args.get("limit")
    pages = request.args.get("pages")

    if limit:
        try: limit = int(limit)
        except ValueError: limit = None
    if pages:
        try: pages = int(pages)
        except ValueError: pages = None
    
    def _run_discovery_job(job_id, p, ident, lim, pgs):
        job_manager.update_progress(job_id, 10, f"Skanowanie portalu {p}...")
        results = discovery_service.discovery_by_portal(p, ident, limit=lim, pages=pgs)
        job_manager.update_progress(job_id, 100, f"Znaleziono {len(results)} inwestycji na {p}.")
        return results

    job_id = job_manager.start_job(f"Discovery: {portal}", _run_discovery_job, portal, identifier, limit, pages)
    return jsonify({"ok": True, "job_id": job_id})

@discovery_bp.route("/discovery/<portal>")
def discovery(portal):
    if portal not in _VALID_PORTALS:
        return jsonify({"error": f"Unknown portal: {portal}"}), 400
    identifier = request.args.get("id", "").strip()
    try:
        results = discovery_service.discovery_by_portal(portal, identifier)
        return jsonify(results)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Discovery error for {portal}: {e}")
        return jsonify({"error": str(e)}), 500
