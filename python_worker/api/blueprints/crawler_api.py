import logging
from flask import Blueprint, jsonify, abort, request
from python_worker.api.utils import _valid_slug

logger = logging.getLogger(__name__)

crawler_bp = Blueprint('crawler', __name__)


def _get_crawler():
    from python_worker.daemons import get_crawler
    return get_crawler()


@crawler_bp.route("/crawler/status", methods=["GET"])
def crawler_status():
    c = _get_crawler()
    if not c:
        return jsonify({"running": False, "paused": False})
    return jsonify(c.get_status())


@crawler_bp.route("/crawler/pause", methods=["POST"])
def crawler_pause():
    c = _get_crawler()
    if c:
        c.pause()
    return jsonify({"ok": True})


@crawler_bp.route("/crawler/resume", methods=["POST"])
def crawler_resume():
    c = _get_crawler()
    if c:
        c.resume()
    return jsonify({"ok": True})


@crawler_bp.route("/crawler/badge-reset/<system_id>", methods=["POST"])
def badge_reset(system_id):
    if not system_id:
        abort(400)
    c = _get_crawler()
    if c:
        c.reset_badge(system_id)
    return jsonify({"ok": True})



@crawler_bp.route("/crawler/exploration", methods=["GET"])
def crawler_exploration():
    c = _get_crawler()
    if not c:
        return jsonify({})
    return jsonify(c.get_exploration_status())


@crawler_bp.route("/doktor/status", methods=["GET"])
def doktor_status():
    from python_worker.daemons import get_doktor
    d = get_doktor()
    if not d:
        return jsonify({"running": False})
    return jsonify(d.get_status())
