"""
Wędrowiec — unified background crawler.

Two modes in a single daemon thread, chosen each tick:

  Wizyta     — visits a known developer and runs investment discovery
               (inherited from the old DeveloperCrawler)
  Eksploracja — slowly pages through developer catalogue pages on RP/OTO/TO
               and registers newly found developers

Tick interval: 60 s.  At each tick the crawler picks whichever task is most
overdue (exploration portal vs developer visit) and executes one unit of work.
"""
import json
import logging
import random
import re
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Wizyta constants ───────────────────────────────────────────────────────────
_SPREAD_DAYS = 14
_REVISIT_DAYS = 30
_REVISIT_JITTER_DAYS = 5
_MIN_VISIT_GAP_MINUTES = 10
_MAX_VISIT_GAP_MINUTES = 20

# ── Eksploracja constants ──────────────────────────────────────────────────────
_EXPLORATION_CONFIG = {
    "rp":  {"max_pages": 217, "min_gap_min": 8,  "max_gap_min": 15},
    "oto": {"max_pages": 230, "min_gap_min": 15, "max_gap_min": 25},
    "to":  {"max_pages": 210, "min_gap_min": 8,  "max_gap_min": 15},
}
# After completing a full cycle, wait this many days before restarting
_EXPLORATION_CYCLE_PAUSE_DAYS = 30

_TICK_SECONDS = 60


def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class Wedrowiec:
    def __init__(self, data_dir: Path, dev_dir: Path):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self._exploration_file = dev_dir / "wedrowiec_exploration.json"
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
        self._thread = threading.Thread(target=self._run, daemon=True, name="wedrowiec")
        self._thread.start()
        logger.info("Wędrowiec started")

    def stop(self):
        self._stop_event.set()
        logger.info("Wędrowiec stop requested")

    def pause(self):
        self._paused = True
        logger.info("Wędrowiec paused")

    def resume(self):
        self._paused = False
        logger.info("Wędrowiec resumed")

    def get_status(self) -> dict:
        with self._lock:
            return {
                "running": bool(self._thread and self._thread.is_alive()),
                "paused": self._paused,
                "current_dev": self._current_dev,
                "next_visit_at": _iso(self._next_visit_at) if self._next_visit_at else None,
            }

    def get_exploration_status(self) -> dict:
        state = self._load_exploration_state()
        result = {}
        for portal, cfg in _EXPLORATION_CONFIG.items():
            ps = state.get(portal, {})
            result[portal] = {
                "page": ps.get("page", 0),
                "max_pages": cfg["max_pages"],
                "next_at": ps.get("next_at"),
                "total_seen": ps.get("total_seen", 0),
                "new_reg": ps.get("new_reg", 0),
                "cycle_start": ps.get("cycle_start"),
            }
        return result

    def reset_badge(self, dev_slug: str):
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

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _run(self):
        startup_delay = random.uniform(30, 120)
        logger.info("Wędrowiec waiting %.0fs before first tick", startup_delay)
        self._stop_event.wait(startup_delay)

        while not self._stop_event.is_set():
            if not self._paused:
                try:
                    self._tick()
                except Exception as e:
                    logger.error("Wędrowiec tick error: %s", e, exc_info=True)
            self._stop_event.wait(_TICK_SECONDS)

    def _tick(self):
        now = _now_utc()

        # Which exploration portal is most overdue?
        exp_portal, exp_overdue_since = self._most_overdue_exploration(now)
        # Which developer visit is most overdue?
        visit_dev, visit_overdue_since = self._most_overdue_visit(now)

        if exp_portal is None and visit_dev is None:
            # Nothing overdue — schedule unvisited devs if any
            self._schedule_all_unvisited()
            return

        # Pick the task that has been waiting the longest
        if exp_portal and (visit_dev is None or exp_overdue_since >= visit_overdue_since):
            self._explore_one_page(exp_portal)
        else:
            # Guard: respect min gap between visits
            with self._lock:
                if self._next_visit_at and now < self._next_visit_at:
                    return
            self._do_visit(visit_dev)

    # ── Exploration ───────────────────────────────────────────────────────────

    def _load_exploration_state(self) -> dict:
        if self._exploration_file.exists():
            try:
                return json.loads(self._exploration_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def _save_exploration_state(self, state: dict):
        try:
            self._exploration_file.write_text(
                json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except Exception as e:
            logger.error("Failed to save exploration state: %s", e)

    def _most_overdue_exploration(self, now: datetime):
        """Return (portal, seconds_overdue) for the most overdue portal, or (None, 0)."""
        state = self._load_exploration_state()
        best_portal = None
        best_overdue = 0

        for portal, cfg in _EXPLORATION_CONFIG.items():
            ps = state.get(portal, {})
            next_at_str = ps.get("next_at")
            if not next_at_str:
                # Never started — immediately overdue
                overdue = float("inf")
            else:
                try:
                    next_at = _parse_iso(next_at_str)
                    if next_at > now:
                        continue  # Not yet due
                    overdue = (now - next_at).total_seconds()
                except ValueError:
                    overdue = float("inf")

            if overdue > best_overdue:
                best_overdue = overdue
                best_portal = portal

        return best_portal, best_overdue

    def _explore_one_page(self, portal: str):
        state = self._load_exploration_state()
        ps = state.setdefault(portal, {})
        cfg = _EXPLORATION_CONFIG[portal]

        # Determine next page to fetch
        current_page = ps.get("page", 0)
        cycle_start = ps.get("cycle_start")

        if current_page >= cfg["max_pages"]:
            # Cycle complete — schedule next cycle
            next_cycle = _now_utc() + timedelta(days=_EXPLORATION_CYCLE_PAUSE_DAYS)
            ps["page"] = 0
            ps["next_at"] = _iso(next_cycle)
            ps["cycle_start"] = None
            state[portal] = ps
            self._save_exploration_state(state)
            logger.info("Wędrowiec: %s exploration cycle complete — next cycle at %s", portal, _iso(next_cycle))
            return

        next_page = current_page + 1
        if not cycle_start:
            ps["cycle_start"] = _iso(_now_utc())

        logger.info("Wędrowiec: exploring %s page %d/%d", portal, next_page, cfg["max_pages"])

        try:
            devs = self._fetch_dev_page(portal, next_page)
        except Exception as e:
            logger.error("Wędrowiec: %s page %d fetch failed: %s", portal, next_page, e)
            devs = []

        if not devs and next_page == 1:
            logger.warning(
                "Wędrowiec: %s page 1 returned 0 results — portal may be blocking "
                "curl_cffi impersonation. Exploration will proceed but may stay empty.",
                portal,
            )

        new_reg = 0
        for dev_info in devs:
            if self._register_if_new(portal, dev_info):
                new_reg += 1

        total_seen = ps.get("total_seen", 0) + len(devs)
        ps["page"] = next_page
        ps["total_seen"] = total_seen
        ps["new_reg"] = ps.get("new_reg", 0) + new_reg

        # Schedule next page
        gap_min = random.uniform(cfg["min_gap_min"], cfg["max_gap_min"])
        ps["next_at"] = _iso(_now_utc() + timedelta(minutes=gap_min))
        state[portal] = ps
        self._save_exploration_state(state)
        logger.info(
            "Wędrowiec: %s page %d → %d devs, %d new registered",
            portal, next_page, len(devs), new_reg,
        )

    # ── Portal page parsers ───────────────────────────────────────────────────

    def _get_fetcher(self):
        from python_worker.config import get_scraper_config
        from usi_scrapers.fetcher import Fetcher
        config = get_scraper_config()
        return Fetcher(config) if config else None

    def _fetch_dev_page(self, portal: str, page: int) -> list[dict]:
        if portal == "rp":
            return self._fetch_rp_page(page)
        elif portal == "oto":
            return self._fetch_oto_page(page)
        elif portal == "to":
            return self._fetch_to_page(page)
        return []

    def _fetch_rp_page(self, page: int) -> list[dict]:
        """RP developer catalogue — plain HTML, no curl_cffi or ScraperAPI needed.
        Links are in the form /deweloperzy/{slug}-{id}/ with vendor name as link text.
        """
        import requests as std_requests
        url = f"https://rynekpierwotny.pl/deweloperzy/?page={page}"
        try:
            r = std_requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            r.raise_for_status()
            html = r.text
        except Exception as e:
            logger.warning("RP dev page %d fetch failed: %s", page, e)
            return []

        devs = []
        seen = set()
        for m in re.finditer(
            r'href=["\'](?:https?://rynekpierwotny\.pl)?/deweloperzy/([a-z0-9\-]+)-(\d+)/["\'][^>]*>\s*([^<\n]+)',
            html,
        ):
            slug, vid, name = m.group(1), m.group(2), m.group(3).strip()
            if vid not in seen and name:
                seen.add(vid)
                devs.append({"name": name, "id": vid, "slug": slug})
        return devs

    def _fetch_oto_page(self, page: int) -> list[dict]:
        """OTO developer catalogue — legacy SSR page (not Next.js), curl_cffi works fine.
        Links are in the form /pl/firmy/deweloperzy/{slug}-ID{agency_id} with name as text.
        No ScraperAPI needed.
        """
        fetcher = self._get_fetcher()
        if not fetcher:
            return []

        url = f"https://www.otodom.pl/firmy/deweloperzy/?sq=&page={page}"
        html = fetcher.fetch(url, use_impersonate=True, use_scraperapi=False)
        if not html:
            return []

        devs = []
        seen = set()
        for m in re.finditer(
            r'href=["\'](?:https?://www\.otodom\.pl)?/pl/firmy/deweloperzy/([^"\']+?)-ID(\d+)["\'][^>]*>\s*([^<\n]+)',
            html,
        ):
            slug_hint, aid, name = m.group(1), m.group(2), m.group(3).strip()
            if aid not in seen and name:
                seen.add(aid)
                devs.append({"name": name, "agency_id": aid})
        return devs

    def _fetch_to_page(self, page: int) -> list[dict]:
        fetcher = self._get_fetcher()
        if not fetcher:
            return []

        url = f"https://tabelaofert.pl/katalog-firm/deweloperzy?page={page}"
        html = fetcher.fetch(url, use_scraperapi=False, use_impersonate=True)
        if not html:
            return []

        devs = []
        for m in re.finditer(
            r'href=["\'](?:https?://tabelaofert\.pl)?/katalog-firm/deweloperzy/([^"\'/?#]+)["\'][^>]*>\s*([^<]+)',
            html,
        ):
            slug = m.group(1).strip()
            name = m.group(2).strip()
            if slug and name and slug != "deweloperzy":
                devs.append({"name": name, "slug": slug})

        # Deduplicate by slug
        seen = set()
        unique = []
        for d in devs:
            if d["slug"] not in seen:
                seen.add(d["slug"])
                unique.append(d)
        return unique

    # ── Developer registration ─────────────────────────────────────────────────

    def _register_if_new(self, portal: str, dev_info: dict) -> bool:
        """Register dev_info as a new developer if not already known. Returns True if new."""
        from python_worker.developer_manager import DeveloperManager
        from python_worker.csv_importer import slugify

        dm = DeveloperManager(self.data_dir, self.dev_dir)

        # Determine the portal identifier for lookup
        if portal == "rp":
            portal_id = dev_info.get("id") or dev_info.get("slug")
            lookup_portal = "rp"
        elif portal == "oto":
            portal_id = dev_info.get("agency_id")
            lookup_portal = "oto"
        else:  # to
            portal_id = dev_info.get("slug")
            lookup_portal = "to"

        if not portal_id:
            return False

        existing = dm.find_by_portal_id(lookup_portal, str(portal_id))
        if existing:
            return False

        # New developer — create a skeleton profile
        dev_slug = slugify(dev_info["name"])
        if not dev_slug:
            return False

        if portal == "rp":
            portal_mapping = {"rp": {"id": dev_info["id"], "slug": dev_info.get("slug", "")}}
        elif portal == "oto":
            portal_mapping = {"oto": {"agency_id": dev_info["agency_id"]}}
        else:
            portal_mapping = {"to": {"slug": dev_info["slug"]}}

        developer_data = {
            "developer_slug": dev_slug,
            "name": dev_info["name"],
            "portal_mapping": portal_mapping,
        }
        try:
            dm.create_developer_file(developer_data)
            logger.info("Wędrowiec: registered new developer %s (%s) from %s", dev_info["name"], dev_slug, portal)
            return True
        except Exception as e:
            logger.error("Wędrowiec: failed to register %s: %s", dev_info["name"], e)
            return False

    # ── Wizyta (developer visit) ───────────────────────────────────────────────

    def _most_overdue_visit(self, now: datetime):
        """Return (dev_slug, seconds_overdue) for most overdue developer, or (None, 0)."""
        oldest_slug = None
        oldest_overdue = 0

        for dev_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            mapping = data.get("portal_mapping", {})
            if not any(mapping.get(p) for p in ("rp", "oto", "to")):
                continue

            crawler = data.get("crawler", {})
            next_visit_str = crawler.get("next_visit")
            if not next_visit_str:
                continue

            try:
                next_visit = _parse_iso(next_visit_str)
            except ValueError:
                continue

            if next_visit > now:
                continue

            overdue = (now - next_visit).total_seconds()
            if overdue > oldest_overdue:
                oldest_overdue = overdue
                oldest_slug = data.get("developer_slug") or dev_file.stem.removeprefix("usi_dev_")

        return oldest_slug, oldest_overdue

    def _schedule_all_unvisited(self):
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

        logger.info("Wędrowiec: scheduling %d unvisited devs over %d days", len(devs_to_schedule), _SPREAD_DAYS)
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

    def _do_visit(self, dev_slug: str):
        logger.info("Wędrowiec: visiting %s", dev_slug)
        with self._lock:
            self._current_dev = dev_slug

        from python_worker.services.discovery_service import DiscoveryService
        svc = DiscoveryService(self.data_dir)
        try:
            new_count = svc.discover_for_developer(None, dev_slug)
        except Exception as e:
            logger.error("Wędrowiec: visit failed for %s: %s", dev_slug, e)
            new_count = 0
        finally:
            with self._lock:
                self._current_dev = None
                gap_min = random.uniform(_MIN_VISIT_GAP_MINUTES, _MAX_VISIT_GAP_MINUTES)
                self._next_visit_at = _now_utc() + timedelta(minutes=gap_min)

        self._record_visit(dev_slug, new_count)
        logger.info("Wędrowiec: done visiting %s — %d new investments", dev_slug, new_count)

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
            events = data.setdefault("events", [])
            events.insert(0, {"at": _iso(_now_utc()), "type": "discover", "by": "wedrowiec", "found": new_count})
            data["events"] = events[:100]
            dev_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            from python_worker.logger_utils import log_to_dev_log
            log_to_dev_log(dev_slug,
                f"Wędrowiec — wizyta zakończona. Znaleziono: {new_count} nowych inwestycji. "
                f"Kolejna wizyta: {crawler['next_visit']}")
        except Exception as e:
            logger.error("_record_visit(%s) failed: %s", dev_slug, e)


# ── Module-level singleton — started by ui_server.py ─────────────────────────
# Keep old name aliases so ui_server.py and crawler_api.py need no changes
_instance: Wedrowiec | None = None

DeveloperCrawler = Wedrowiec  # backwards-compat alias


def get_crawler() -> Wedrowiec | None:
    return _instance


def init_crawler(data_dir: Path, dev_dir: Path) -> Wedrowiec:
    global _instance
    _instance = Wedrowiec(data_dir, dev_dir)
    return _instance
