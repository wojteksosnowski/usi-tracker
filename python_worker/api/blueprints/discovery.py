import logging
from flask import Blueprint, jsonify, request, abort
from python_worker.services.discovery_service import DiscoveryService
from python_worker.jobs import job_manager
from python_worker.api.utils import _valid_slug

logger = logging.getLogger(__name__)

_VALID_PORTALS = {"rp", "oto", "to"}

discovery_bp = Blueprint('discovery', __name__)
discovery_service = DiscoveryService()

@discovery_bp.route("/developer/<dev_slug>/discover", methods=["POST"])
def discover_dev_new(dev_slug):
    if not _valid_slug(dev_slug):
        abort(400)
    job_id = job_manager.start_job(
        f"Discovery: {dev_slug}",
        discovery_service.discover_for_developer,
        dev_slug,
        job_manager=job_manager
    )
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
