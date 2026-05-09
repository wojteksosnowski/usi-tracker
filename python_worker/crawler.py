"""
DeveloperCrawler — background thread that periodically runs discovery for all developers.

Schedule: each developer is visited at most once per month.
All developers are covered within ~2 weeks (staggered random delays).
Interval between individual visits: 10-20 minutes (random, to avoid detection).
"""
import json
import logging
import random
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Visit spread window: 14 days total, then repeat monthly
_SPREAD_DAYS = 14
_REVISIT_DAYS = 30
_REVISIT_JITTER_DAYS = 5
# Gap between crawler ticks
_TICK_SECONDS = 60
# Minimum gap between two consecutive developer visits
_MIN_VISIT_GAP_MINUTES = 10
_MAX_VISIT_GAP_MINUTES = 20


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


class DeveloperCrawler:
    def __init__(self, data_dir: Path, dev_dir: Path):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        self._paused = False
        self._current_dev: str | None = None
        self._next_visit_at: datetime | None = None
        self._lock = threading.Lock()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True, name="dev-crawler")
        self._thread.start()
        logger.info("DeveloperCrawler started")

    def stop(self):
        self._stop_event.set()
        logger.info("DeveloperCrawler stop requested")

    def pause(self):
        self._paused = True
        logger.info("DeveloperCrawler paused")

    def resume(self):
        self._paused = False
        logger.info("DeveloperCrawler resumed")

    def get_status(self) -> dict:
        with self._lock:
            return {
                "running": bool(self._thread and self._thread.is_alive()),
                "paused": self._paused,
                "current_dev": self._current_dev,
                "next_visit_at": _iso(self._next_visit_at) if self._next_visit_at else None,
            }

    def reset_badge(self, dev_slug: str):
        """Clear new_since_review counter for a developer (call when user opens dev detail)."""
        dev_file = self.dev_dir / f"usi_dev_{dev_slug}.json"
        if not dev_file.exists():
            return
        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            crawler = data.get("crawler", {})
            if crawler.get("new_since_review", 0):
                crawler["new_since_review"] = 0
                data["crawler"] = crawler
                dev_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning("reset_badge(%s) failed: %s", dev_slug, e)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self):
        # Initial stagger so crawler doesn't hit dev #1 immediately on startup
        startup_delay = random.uniform(30, 120)
        logger.info("DeveloperCrawler waiting %.0fs before first tick", startup_delay)
        self._stop_event.wait(startup_delay)

        while not self._stop_event.is_set():
            if not self._paused:
                try:
                    self._tick()
                except Exception as e:
                    logger.error("Crawler tick error: %s", e, exc_info=True)
            self._stop_event.wait(_TICK_SECONDS)

    def _tick(self):
        now = _now_utc()

        # Check if it's time for the next visit
        with self._lock:
            if self._next_visit_at and now < self._next_visit_at:
                return

        dev_slug = self._pick_next_dev()
        if not dev_slug:
            # No dev due — schedule first-time visits for all devs
            self._schedule_all_unvisited()
            return

        with self._lock:
            self._current_dev = dev_slug

        try:
            self._visit(dev_slug)
        finally:
            with self._lock:
                self._current_dev = None
                gap_minutes = random.uniform(_MIN_VISIT_GAP_MINUTES, _MAX_VISIT_GAP_MINUTES)
                self._next_visit_at = _now_utc() + timedelta(minutes=gap_minutes)

    def _pick_next_dev(self) -> str | None:
        """Return the developer whose next_visit is oldest and overdue."""
        now = _now_utc()
        oldest_slug = None
        oldest_time = None

        for dev_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            # Skip devs with no portal mapping (nothing to discover)
            mapping = data.get("portal_mapping", {})
            has_portals = any(
                mapping.get(p) for p in ("rp", "oto", "to")
            )
            if not has_portals:
                continue

            crawler = data.get("crawler", {})
            next_visit_str = crawler.get("next_visit")
            if not next_visit_str:
                continue  # Not yet scheduled — handled by _schedule_all_unvisited

            try:
                next_visit = datetime.fromisoformat(next_visit_str.replace("Z", "+00:00"))
            except ValueError:
                continue

            if next_visit > now:
                continue  # Not due yet

            if oldest_time is None or next_visit < oldest_time:
                oldest_time = next_visit
                oldest_slug = data.get("developer_slug") or dev_file.stem.removeprefix("usi_dev_")

        return oldest_slug

    def _schedule_all_unvisited(self):
        """Assign initial next_visit timestamps spread over _SPREAD_DAYS for unvisited devs."""
        devs_to_schedule = []
        for dev_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            mapping = data.get("portal_mapping", {})
            if not any(mapping.get(p) for p in ("rp", "oto", "to")):
                continue
            if data.get("crawler", {}).get("next_visit"):
                continue
            devs_to_schedule.append(dev_file)

        if not devs_to_schedule:
            return

        logger.info("Scheduling %d unvisited developers over %d days", len(devs_to_schedule), _SPREAD_DAYS)
        now = _now_utc()
        spread_seconds = _SPREAD_DAYS * 86400
        random.shuffle(devs_to_schedule)

        for i, dev_file in enumerate(devs_to_schedule):
            offset = (i / len(devs_to_schedule)) * spread_seconds + random.uniform(-3600, 3600)
            offset = max(0, offset)
            next_visit = now + timedelta(seconds=offset)
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
                data.setdefault("crawler", {})["next_visit"] = _iso(next_visit)
                dev_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to schedule %s: %s", dev_file.name, e)

    def _visit(self, dev_slug: str):
        logger.info("Crawler visiting: %s", dev_slug)
        from python_worker.services.discovery_service import DiscoveryService
        svc = DiscoveryService(self.data_dir)
        try:
            new_count = svc.discover_for_developer(None, dev_slug)
        except Exception as e:
            logger.error("Crawler visit failed for %s: %s", dev_slug, e)
            new_count = 0

        self._record_visit(dev_slug, new_count)
        logger.info("Crawler done: %s — %d new investments", dev_slug, new_count)

    def _log_dev_event(self, dev_slug: str, event: dict):
        try:
            from python_worker.developer_manager import DeveloperManager
            dm = DeveloperManager(self.data_dir, self.dev_dir)
            dm.log_event(dev_slug, event)
        except Exception as e:
            logger.warning("_log_dev_event(%s) failed: %s", dev_slug, e)

    def _record_visit(self, dev_slug: str, new_count: int):
        dev_file = self.dev_dir / f"usi_dev_{dev_slug}.json"
        if not dev_file.exists():
            return
        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            crawler = data.get("crawler", {})
            crawler["last_visit"] = _iso(_now_utc())
            jitter = random.uniform(-_REVISIT_JITTER_DAYS, _REVISIT_JITTER_DAYS)
            crawler["next_visit"] = _iso(_now_utc() + timedelta(days=_REVISIT_DAYS + jitter))
            crawler["last_new_count"] = new_count
            crawler["new_since_review"] = crawler.get("new_since_review", 0) + new_count
            data["crawler"] = crawler
            # Append to events log
            events = data.setdefault("events", [])
            events.insert(0, {"at": _iso(_now_utc()), "type": "discover", "by": "crawler", "found": new_count})
            data["events"] = events[:100]
            dev_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error("_record_visit(%s) failed: %s", dev_slug, e)


# Module-level singleton — started by ui_server.py
_instance: DeveloperCrawler | None = None


def get_crawler() -> DeveloperCrawler | None:
    return _instance


def init_crawler(data_dir: Path, dev_dir: Path) -> DeveloperCrawler:
    global _instance
    _instance = DeveloperCrawler(data_dir, dev_dir)
    return _instance
