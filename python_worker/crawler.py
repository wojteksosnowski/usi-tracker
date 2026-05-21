"""
Wędrowiec — unified background crawler.

Two modes in a single daemon thread, chosen each tick:

  Wizyta     — visits a known developer and runs investment discovery
               (inherited from the old DeveloperCrawler)
  Eksploracja — slowly pages through developer catalogue pages on RP/OTO/TO
               and registers newly found developers
  Konserwacja — (Maintenance) refreshes developer metadata, logos and raw files

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

from python_worker.developer_manager import DeveloperManager

logger = logging.getLogger(__name__)

# ── Wizyta constants ───────────────────────────────────────────────────────────
_SPREAD_DAYS = 14
_REVISIT_DAYS = 30
_REVISIT_JITTER_DAYS = 5
_MIN_VISIT_GAP_MINUTES = 10
_MAX_VISIT_GAP_MINUTES = 60
_INGESTION_PAUSE_SECONDS = 15  # Delay after full ingestion to avoid portal pressure

# ── Eksploracja constants ──────────────────────────────────────────────────────
_EXPLORATION_CONFIG = {
    "rp":  {"min_gap_min": 8,  "max_gap_min": 15},
    "oto": {"min_gap_min": 15, "max_gap_min": 25},
    "to":  {"min_gap_min": 8,  "max_gap_min": 15},
}
# After completing a full cycle, wait this many days before restarting
_EXPLORATION_CYCLE_PAUSE_DAYS = 30

# ── Konserwacja constants ──────────────────────────────────────────────────────
_MAINTENANCE_WEIGHT = 0.3  # Probability of picking maintenance if overdue
_MIN_MAINTENANCE_GAP_MINUTES = 2

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
        self._current_task: str | None = None  # 'visit', 'exploration', 'maintenance'
        self._next_visit_at: datetime | None = None
        self._next_maint_at: datetime | None = None
        self._last_suggest_at: datetime | None = None
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
            status = {
                "running": bool(self._thread and self._thread.is_alive()),
                "paused": self._paused,
                "current_dev": self._current_dev,
                "current_task": self._current_task,
                "next_visit_at": _iso(self._next_visit_at) if self._next_visit_at else None,
                "next_maint_at": _iso(self._next_maint_at) if self._next_maint_at else None,
            }
            # Include exploration stats if running
            try:
                status["exploration"] = self.get_exploration_status()
            except Exception:
                status["exploration"] = {}
            return status

    def get_exploration_status(self) -> dict:
        state = self._load_exploration_state()
        result = {}
        for portal in _EXPLORATION_CONFIG:
            ps = state.get(portal, {})
            result[portal] = {
                "page": ps.get("page", 0),
                "total_pages": ps.get("total_pages"),
                "next_at": ps.get("next_at"),
                "total_seen": ps.get("total_seen", 0),
                "new_reg": ps.get("new_reg", 0),
                "cycle_start": ps.get("cycle_start"),
            }
        return result

    def _find_dev_file(self, dev_slug: str) -> "Path | None":
        """Return path to primary usi_dev_*.json for slug (lowest DEV-ID), or None."""
        subdir = self.dev_dir / dev_slug
        if subdir.is_dir():
            hits = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if hits:
                return hits[0]
        return None

    def reset_badge(self, dev_slug: str):
        dev_file = self._find_dev_file(dev_slug)
        if not dev_file:
            return
        try:
            from python_worker.developer_manager import DeveloperManager
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            crawler = data.get("crawler", {})
            if crawler.get("new_since_review", 0):
                crawler["new_since_review"] = 0
                data["crawler"] = crawler
                DeveloperManager(self.data_dir, self.dev_dir).create_developer_file(data)
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

        # 1. Which exploration portal is most overdue?
        exp_portal, exp_overdue_since = self._most_overdue_exploration(now)
        # Which developer visit is most overdue?
        visit_dev, visit_overdue_since = self._most_overdue_visit(now)
        # Which developer needs maintenance most?
        maint_dev, maint_priority = self._most_overdue_maintenance(now)

        if exp_portal is None and visit_dev is None and maint_dev is None:
            # Nothing overdue — schedule unvisited devs if any
            self._schedule_all_unvisited()
            return

        # Decision 1: Maintenance check (weighted)
        if maint_dev:
            # If priority is extremely high (missing logo/data) or random hit
            if maint_priority >= 1000 or random.random() < _MAINTENANCE_WEIGHT:
                with self._lock:
                    if not self._next_maint_at or now >= self._next_maint_at:
                        self._do_maintenance(maint_dev)
                        return

        # Decision 2: Normal priority (longest waiting)
        if exp_portal and (visit_dev is None or exp_overdue_since >= visit_overdue_since):
            self._explore_one_page(exp_portal)
        else:
            # Guard: respect min gap between visits
            with self._lock:
                if self._next_visit_at and now < self._next_visit_at:
                    # If we can't visit, maybe we can explore?
                    if exp_portal:
                        self._explore_one_page(exp_portal)
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
        with self._lock:
            self._current_task = f"exploring {portal}"
        
        try:
            state = self._load_exploration_state()
            ps = state.setdefault(portal, {})
            cfg = _EXPLORATION_CONFIG[portal]

            current_page = ps.get("page", 0)
            cycle_start = ps.get("cycle_start")
            saved_total = ps.get("total_pages")

            # If we already know total_pages and have finished, start next cycle
            if saved_total and current_page >= saved_total:
                self._save_exploration_state(self._mark_cycle_done(state, portal, ps))
                return

            next_page = current_page + 1
            if not cycle_start:
                ps["cycle_start"] = _iso(_now_utc())

            try:
                result = self._fetch_dev_page(portal, next_page)
            except Exception as e:
                logger.error("Wędrowiec: %s page %d fetch failed: %s", portal, next_page, e)
                result = None

            if result is None:
                gap_min = random.uniform(cfg["min_gap_min"], cfg["max_gap_min"])
                ps["next_at"] = _iso(_now_utc() + timedelta(minutes=gap_min))
                state[portal] = ps
                self._save_exploration_state(state)
                return

            total_pages = result.total_pages
            devs = result.developers
            ps["total_pages"] = total_pages

            logger.info("Wędrowiec: exploring %s page %d/%d", portal, next_page, total_pages)

            if not devs and next_page == 1:
                logger.warning(
                    "Wędrowiec: %s page 1 returned 0 results — portal may be blocking requests.",
                    portal,
                )

            known_ids = self._build_known_dev_ids()
            new_reg = 0
            for dev_info in devs:
                if self._register_if_new(portal, dev_info, known_ids):
                    new_reg += 1

            total_seen = ps.get("total_seen", 0) + len(devs)
            ps["page"] = next_page
            ps["total_seen"] = total_seen
            ps["new_reg"] = ps.get("new_reg", 0) + new_reg

            if next_page >= total_pages:
                state = self._mark_cycle_done(state, portal, ps)
            else:
                gap_min = random.uniform(cfg["min_gap_min"], cfg["max_gap_min"])
                ps["next_at"] = _iso(_now_utc() + timedelta(minutes=gap_min))
                state[portal] = ps

            self._save_exploration_state(state)
            logger.info(
                "Wędrowiec: %s page %d/%d → %d devs, %d new registered",
                portal, next_page, total_pages, len(devs), new_reg,
            )
        finally:
            with self._lock:
                self._current_task = None

    # ── Portal page fetcher ───────────────────────────────────────────────────

    def _fetch_dev_page(self, portal: str, page: int):
        """Fetch one page of developer catalogue via usi-scrapers library.

        Returns DeveloperPage(developers, total_pages, page) or None on error.
        Each developer dict has keys: url, name (may be None for TO), slug.
        """
        from python_worker.config import get_scraper_config
        from usi_scrapers import api as scraper_api
        from usi_scrapers.fetcher import Fetcher

        config = get_scraper_config()
        if not config:
            return None

        portal_name = {"rp": "rp", "oto": "otodom", "to": "tabelaofert"}.get(portal)
        if not portal_name:
            return None

        return scraper_api.list_developers(config, Fetcher(config), portal_name, page=page)

    # ── Developer registration ─────────────────────────────────────────────────

    def _build_known_dev_ids(self) -> dict:
        """Scan all developer files once; return sets for O(1) dedup in _register_if_new."""
        rp: set = set()
        oto: set = set()
        to: set = set()
        for f in self.dev_dir.glob("*/usi_dev_*.json"):
            try:
                pm = json.loads(f.read_text(encoding="utf-8")).get("portal_mapping") or {}
                rp_m = pm.get("rp") or {}
                if rp_m.get("slug"): rp.add(str(rp_m["slug"]))
                if rp_m.get("id"): rp.add(str(rp_m["id"]))
                oto_m = pm.get("oto") or {}
                if oto_m.get("agency_id"): oto.add(str(oto_m["agency_id"]))
                for aid in oto_m.get("agency_ids", []): oto.add(str(aid))
                to_m = pm.get("to") or {}
                if to_m.get("slug"): to.add(str(to_m["slug"]))
                if to_m.get("id"): to.add(str(to_m["id"]))
            except Exception:
                continue
        return {"rp": rp, "oto": oto, "to": to}

    def _mark_cycle_done(self, state: dict, portal: str, ps: dict) -> dict:
        next_cycle = _now_utc() + timedelta(days=_EXPLORATION_CYCLE_PAUSE_DAYS)
        ps["page"] = 0
        ps["total_pages"] = None
        ps["next_at"] = _iso(next_cycle)
        ps["cycle_start"] = None
        state[portal] = ps
        logger.info("Wędrowiec: %s exploration cycle complete — next cycle at %s", portal, _iso(next_cycle))
        return state

    def _register_if_new(self, portal: str, dev_info: dict, known_ids: dict) -> bool:
        """Register dev as new if not in known_ids. Updates known_ids on registration.

        dev_info from usi-scrapers list_developers(): {"url", "name", "slug"}.
        name may be None (TabelaOfert doesn't expose names on the listing page).
        developer_slug comes directly from the portal slug — never slugify(name).
        Writes a mock raw_{portal}_{slug}.json first, then builds usi_dev via
        _build_dev_from_raws() — maintains the 1:1 raw↔usi_dev rule.
        """
        from python_worker.developer_manager import DeveloperManager
        from python_worker.url_parser import parse_url

        if portal == "rp":
            portal_id = dev_info.get("slug")
        elif portal == "oto":
            # Extract numeric agency_id from URL: .../deweloperzy/{slug}-ID{id}
            parsed = parse_url(dev_info.get("url") or "")
            portal_id = parsed.get("agency_id")
        else:  # to
            portal_id = dev_info.get("slug")

        if not portal_id or str(portal_id) in known_ids[portal]:
            return False

        # Slug comes from the portal — never derived from company name.
        dev_slug = dev_info.get("slug")
        if not dev_slug:
            return False

        display_name = dev_info.get("name") or dev_slug

        try:
            dm = DeveloperManager(self.data_dir, self.dev_dir)
            dev_data = dm.get_developer(dev_slug)
            if not dev_data:
                dev_data = {
                    "developer_slug": dev_slug,
                    "name": display_name,
                    "portal_mapping": {"rp": None, "oto": None, "to": None}
                }
            
            if portal == "rp":
                dev_data["portal_mapping"]["rp"] = {"id": str(portal_id), "slug": dev_info.get("slug", "")}
            elif portal == "oto":
                if not dev_data["portal_mapping"].get("oto"):
                    dev_data["portal_mapping"]["oto"] = {"agency_id": str(portal_id), "agency_ids": []}
                if str(portal_id) not in dev_data["portal_mapping"]["oto"]["agency_ids"]:
                    dev_data["portal_mapping"]["oto"]["agency_ids"].append(str(portal_id))
            elif portal == "to":
                dev_data["portal_mapping"]["to"] = {"agency_id": str(portal_id)}
            
            dm.create_developer_file(dev_data)
            known_ids[portal].add(str(portal_id))
            logger.info("Wędrowiec: registered new developer %s (%s) from %s", display_name, dev_slug, portal)
            return True
        except Exception as e:
            logger.error("Wędrowiec: failed to register %s: %s", display_name, e)
            return False

    # ── Wizyta (developer visit) ───────────────────────────────────────────────

    def _most_overdue_visit(self, now: datetime):
        """Return (dev_slug, seconds_overdue) for most overdue developer, or (None, 0)."""
        oldest_slug = None
        oldest_overdue = 0

        seen_slugs: set = set()
        for dev_file in sorted(self.dev_dir.glob("*/usi_dev_*.json")):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            slug = data.get("developer_slug") or dev_file.parent.name
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

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
                oldest_slug = slug

        return oldest_slug, oldest_overdue

    def _schedule_all_unvisited(self):
        devs_to_schedule = []
        seen_slugs: set = set()
        for dev_file in sorted(self.dev_dir.glob("*/usi_dev_*.json")):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue
            slug = data.get("developer_slug") or dev_file.parent.name
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)
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

        dm = DeveloperManager(self.data_dir, self.dev_dir)
        for i, dev_file in enumerate(devs_to_schedule):
            offset = (i / len(devs_to_schedule)) * spread_seconds + random.uniform(-3600, 3600)
            offset = max(0, offset)
            next_visit = now + timedelta(seconds=offset)
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
                data.setdefault("crawler", {})["next_visit"] = _iso(next_visit)
                dm.create_developer_file(data)
            except Exception as e:
                logger.warning("Failed to schedule %s: %s", dev_file.name, e)

    def _do_visit(self, dev_slug: str):
        logger.info("Wędrowiec: visiting %s (Full Ingestion enabled)", dev_slug)
        with self._lock:
            self._current_dev = dev_slug
            self._current_task = "visit"

        from python_worker.services.discovery_service import DiscoveryService
        svc = DiscoveryService(self.data_dir)
        try:
            # Deep Visit: auto_register=True creates skeletons, download=True triggers process_batch
            new_count = svc.discover_for_developer(None, dev_slug, download=True, auto_register=True)
        except Exception as e:
            logger.error("Wędrowiec: visit failed for %s: %s", dev_slug, e)
            new_count = 0
        finally:
            with self._lock:
                self._current_dev = None
                self._current_task = None
                gap_min = random.uniform(_MIN_VISIT_GAP_MINUTES, _MAX_VISIT_GAP_MINUTES)
                self._next_visit_at = _now_utc() + timedelta(minutes=gap_min)

        self._record_visit(dev_slug, new_count)
        logger.info("Wędrowiec: done visiting %s — %d new investments processed", dev_slug, new_count)

    def _record_visit(self, dev_slug: str, new_count: int):
        dev_file = self._find_dev_file(dev_slug)
        if not dev_file:
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
            DeveloperManager(self.data_dir, self.dev_dir).create_developer_file(data)
            from python_worker.logger_utils import log_to_dev_log
            log_to_dev_log(dev_slug,
                f"Wędrowiec — wizyta zakończona. Znaleziono: {new_count} nowych inwestycji. "
                f"Kolejna wizyta: {crawler['next_visit']}")
        except Exception as e:
            logger.error("_record_visit(%s) failed: %s", dev_slug, e)

    # ── Konserwacja (Maintenance) ─────────────────────────────────────────────

    def _most_overdue_maintenance(self, now: datetime):
        """Return (dev_slug, priority_score) for developer needing maintenance most."""
        from python_worker.services.developer_service import DeveloperService
        svc = DeveloperService(self.data_dir, self.dev_dir)

        best_slug = None
        best_score = -1.0

        seen_slugs: set = set()
        for dev_file in sorted(self.dev_dir.glob("*/usi_dev_*.json")):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            slug = data.get("developer_slug") or dev_file.parent.name
            if slug in seen_slugs:
                continue
            seen_slugs.add(slug)

            score = svc.get_maintenance_overdue_score(data)
            if score > best_score:
                best_score = score
                best_slug = slug

        if best_score <= 0:
            return None, 0
        return best_slug, best_score

    def _do_maintenance(self, dev_slug: str):
        logger.info("Wędrowiec: maintenance for %s", dev_slug)
        with self._lock:
            self._current_dev = dev_slug
            self._current_task = "maintenance"

        from python_worker.services.developer_service import DeveloperService
        svc = DeveloperService(self.data_dir, self.dev_dir)
        success = False
        try:
            success = svc.update_developer_profile(dev_slug)
        except Exception as e:
            logger.error("Wędrowiec: maintenance failed for %s: %s", dev_slug, e)
        finally:
            with self._lock:
                self._current_dev = None
                self._current_task = None
                self._next_maint_at = _now_utc() + timedelta(minutes=_MIN_MAINTENANCE_GAP_MINUTES)

        svc.record_maintenance(dev_slug, success)
        logger.info("Wędrowiec: maintenance done for %s (success=%s)", dev_slug, success)


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
