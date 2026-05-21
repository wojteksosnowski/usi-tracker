import fcntl
import json
import logging
import re
import threading
from pathlib import Path
from datetime import datetime
from .slug_utils import slugify

_counter_lock = threading.Lock()

logger = logging.getLogger(__name__)

class DeveloperManager:
    def __init__(self, data_dir: Path, dev_dir: Path = None):
        self.data_dir = data_dir
        self.dev_dir = dev_dir or (data_dir.parent / "USIdev")
        self.dev_raw_dir = self.dev_dir / "raw"
        try:
            self.dev_dir.mkdir(parents=True, exist_ok=True)
            self.dev_raw_dir.mkdir(parents=True, exist_ok=True)
        except (PermissionError, OSError) as e:
            logger.warning(f"Note: Could not verify/create directories {self.dev_dir} or {self.dev_raw_dir} due to OS permissions. Proceeding anyway. Error: {e}")
        self.counters_path = Path(__file__).parent / "data" / "usi_counters.json"

        from python_worker.config import get_scraper_config
        from usi_scrapers.manager import TechnicalDataManager
        config = get_scraper_config()
        self.tech_manager = TechnicalDataManager(config) if config else None

    def _get_next_counter(self, key: str) -> int:
        """Atomic counter increment — thread-safe (threading.Lock) and process-safe (flock)."""
        self.counters_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.counters_path.exists():
            self.counters_path.write_text('{"dev": 0, "inv": 0, "dm": 0}', encoding="utf-8")
        with _counter_lock:
            with open(self.counters_path, "r+", encoding="utf-8") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                try:
                    data = json.load(f)
                    data[key] = data.get(key, 0) + 1
                    f.seek(0)
                    json.dump(data, f, indent=2)
                    f.truncate()
                    return data[key]
                finally:
                    fcntl.flock(f, fcntl.LOCK_UN)

    def generate_usi_id(self, prefix: str) -> str:
        """Generates a new USI ID (e.g., DEV-0001, INV-0001, DM-0001)."""
        key = {"DEV": "dev", "INV": "inv", "DM": "dm"}.get(prefix, "dev")
        num = self._get_next_counter(key)
        return f"{prefix}-{num:04d}"

    # -------------------------------------------------------------------------
    # File path helpers
    # -------------------------------------------------------------------------

    def _dev_file_path(self, dev_slug: str, usi_dev_id: str = None) -> Path | None:
        """New-format path: USIdev/{slug}/usi_dev_{usi_dev_id}_{slug}.json
        Returns None if no existing file found via glob (when usi_dev_id not given)."""
        subdir = self.dev_dir / dev_slug
        if usi_dev_id:
            return subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
        if subdir.exists():
            candidates = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if candidates:
                return candidates[0]
        return None

    def _dev_file_path_old_canonical(self, dev_slug: str) -> Path:
        """Pre-ID canonical path: USIdev/{slug}/usi_dev_{slug}.json"""
        return self.dev_dir / dev_slug / f"usi_dev_{dev_slug}.json"

    def _dev_file_path_legacy(self, dev_slug: str) -> Path:
        """Flat legacy path: USIdev/usi_dev_{dev_slug}.json"""
        return self.dev_dir / f"usi_dev_{dev_slug}.json"

    def _dev_master_path(self, master_id: str, master_slug: str) -> Path:
        return self.dev_dir / master_slug / f"dev_master_{master_id}.json"

    # -------------------------------------------------------------------------
    # Level 3 (dev_master) helpers
    # -------------------------------------------------------------------------

    def _read_dev_master(self, master_id: str, master_slug: str) -> dict | None:
        path = self._dev_master_path(master_id, master_slug)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.warning(f"Could not read dev_master {path}: {e}")
            return None

    def _save_dev_master(self, master: dict, master_slug: str) -> None:
        path = self._dev_master_path(master["dev_master_id"], master_slug)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")

    def _get_or_create_dev_master(self, master_slug: str, master_dev: dict) -> dict:
        """Reads existing dev_master or creates a new one; sets master_id on master_dev in-place."""
        master_id = master_dev.get("master_id")
        if master_id:
            existing = self._read_dev_master(master_id, master_slug)
            if existing:
                return existing
        dm_id = self.generate_usi_id("DM")
        master = {
            "dev_master_id": dm_id,
            "master_usi_dev_id": master_dev.get("usi_dev_id"),
            "master_slug": master_slug,
            "merged_from": [],
            "dismissed": [],
        }
        master_dev["master_id"] = dm_id
        return master

    # -------------------------------------------------------------------------
    # Log helpers
    # -------------------------------------------------------------------------

    def append_dev_log(self, dev_slug: str, event: dict) -> None:
        """Appends one JSONL event to dev_log_{slug}.txt."""
        log_path = self.dev_dir / dev_slug / f"dev_log_{dev_slug}.txt"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {"at": datetime.now().isoformat(), **event}
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _append_event(self, dev: dict, event: dict):
        """Deprecated shim — logs to dev_log_*.txt instead of dev['events']."""
        dev_slug = dev.get("developer_slug")
        if dev_slug:
            self.append_dev_log(dev_slug, event)

    # -------------------------------------------------------------------------
    # Identifiers scan (investment files)
    # -------------------------------------------------------------------------

    def get_existing_identifiers(self) -> dict:
        """
        Scans USI_DATA_DIR for existing investments and returns a dict with sets of IDs.
        Includes a 5-minute cache to speed up repeated UI calls.
        """
        now = datetime.now()
        if hasattr(self, "_identifiers_cache"):
            cache_time, cache_data = self._identifiers_cache
            if (now - cache_time).total_seconds() < 300:
                logger.info("Using cached identifiers (valid for 5m)")
                return cache_data

        rp_ids = set()
        oto_ids = set()
        oto_slugs = set()
        to_ids = set()

        logger.info(f"Scanning {self.data_dir} for existing identifiers...")

        for json_file in self.data_dir.rglob("usi_*.json"):
            if json_file.name.startswith("usi_dev_"):
                continue
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                sources = data.get("sources", {})
                if not sources:
                    continue

                rp_src = sources.get("rp", {})
                if rp_src and rp_src.get("id"):
                    val = str(rp_src["id"])
                    if val and val != "None":
                        rp_ids.add(val)

                oto_src = sources.get("oto", {})
                if oto_src:
                    if oto_src.get("id"):
                        val = str(oto_src["id"])
                        if val and val != "None":
                            oto_ids.add(val)
                    url = oto_src.get("url")
                    if url:
                        from .url_parser import parse_url
                        parsed = parse_url(url)
                        if parsed.get("investment_slug"):
                            full_slug = parsed["investment_slug"]
                            oto_slugs.add(full_slug)
                            # Extract ID from slug if present (canonical Otodom pattern)
                            if "-ID" in full_slug:
                                hash_id = full_slug.split("-ID")[-1]
                                oto_ids.add(hash_id)
                        if parsed.get("agency_id"):
                            oto_ids.add(parsed["agency_id"])

                to_src = sources.get("to", {})
                if to_src:
                    if to_src.get("id"):
                        val = str(to_src["id"])
                        if val and val != "None":
                            to_ids.add(val)
                    elif to_src.get("url"):
                        from .url_parser import parse_url
                        parsed = parse_url(to_src["url"])
                        if parsed.get("to_id"):
                            to_ids.add(str(parsed["to_id"]))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        logger.info(f"Found {len(rp_ids)} RP IDs, {len(oto_ids)} Otodom IDs, and {len(to_ids)} TO IDs.")
        result = {
            "rp_ids": rp_ids,
            "oto_ids": oto_ids,
            "oto_slugs": oto_slugs,
            "to_ids": to_ids,
        }
        self._identifiers_cache = (now, result)
        return result

    # -------------------------------------------------------------------------
    # Raw file saves
    # -------------------------------------------------------------------------

    def save_raw_json(self, data: dict, dev_slug: str, inv_slug: str, portal_prefix: str) -> Path:
        """Delegates raw investment JSON saving to the library manager."""
        if self.tech_manager:
            from usi_scrapers import api as scraper_api
            return scraper_api.save_raw(self.tech_manager.config, data, dev_slug, inv_slug, portal_prefix)
        inv_dir = self.data_dir / dev_slug / inv_slug
        inv_dir.mkdir(parents=True, exist_ok=True)
        filename = f"raw_{portal_prefix}_{inv_slug}.json"
        file_path = inv_dir / filename
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    def save_dev_raw_json(self, data: dict, dev_slug: str, portal_prefix: str, portal_id: str = None) -> Path:
        """Delegates raw developer JSON saving to the library manager."""
        if self.tech_manager:
            from usi_scrapers.utils.io import save_dev_raw_json as lib_save_dev_raw
            return lib_save_dev_raw(data, self.tech_manager.config.public_dir, dev_slug, portal_prefix, portal_id=portal_id)
        
        # Fallback
        filename = f"raw_{portal_prefix}_{portal_id}.json" if portal_id else f"raw_{portal_prefix}_{dev_slug}.json"
        file_path = self.dev_dir / dev_slug / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return file_path

    # -------------------------------------------------------------------------
    # Core CRUD — Level 2 files
    # -------------------------------------------------------------------------

    def create_developer_file(self, developer_data: dict) -> Path:
        """
        Creates or updates usi_dev_{usi_dev_id}_{slug}.json in USIdev/{slug}/.
        Strips events[] and merged_from[] — those belong in Level 3 / log files.
        Auto-removes the pre-ID old-format file if present.
        """
        dev_slug = developer_data.get("developer_slug")
        if not dev_slug:
            raise ValueError("developer_slug is required")

        subdir = self.dev_dir / dev_slug
        subdir.mkdir(parents=True, exist_ok=True)

        # Load existing data for audit/id preservation.
        # When incoming data targets a specific portal, match by that portal to avoid
        # reusing the DEV ID from a different portal's file (1:1 rule).
        existing_data = {}
        incoming_pm = developer_data.get("portal_mapping") or {}
        incoming_portal = next((p for p in ("rp", "oto", "to") if incoming_pm.get(p)), None)

        if incoming_portal:
            for f in sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json")):
                try:
                    d = json.loads(f.read_text(encoding="utf-8"))
                    if d.get("portal_mapping", {}).get(incoming_portal):
                        existing_data = d
                        break
                except Exception as e:
                    logger.warning(f"Could not read existing dev file {f}: {e}")
        else:
            for candidate in [
                self._dev_file_path(dev_slug),           # new format (glob)
                self._dev_file_path_old_canonical(dev_slug),  # pre-ID canonical
                self._dev_file_path_legacy(dev_slug),    # flat legacy
                self.data_dir / dev_slug / f"usi_dev_{dev_slug}.json",
            ]:
                if candidate and candidate.exists():
                    try:
                        existing_data = json.loads(candidate.read_text(encoding="utf-8"))
                        break
                    except Exception as e:
                        logger.warning(f"Could not read existing dev file {candidate}: {e}")

        # Ensure portal_mapping exists
        if "portal_mapping" not in developer_data:
            developer_data["portal_mapping"] = existing_data.get("portal_mapping", {
                "rp": None, "oto": None, "to": None
            })

        # Preserve audit timestamps
        developer_data["audit"] = existing_data.get("audit", {
            "created_at": datetime.now().isoformat()
        })
        developer_data["audit"]["updated_at"] = datetime.now().isoformat()

        # Ensure usi_dev_id
        if not developer_data.get("usi_dev_id"):
            if existing_data.get("usi_dev_id"):
                developer_data["usi_dev_id"] = existing_data["usi_dev_id"]
            else:
                developer_data["usi_dev_id"] = self.generate_usi_id("DEV")

        # Strip Level 3 fields — they live in dev_master_*.json
        developer_data.pop("events", None)
        developer_data.pop("merged_from", None)
        developer_data.pop("parent_id", None)

        usi_dev_id = developer_data["usi_dev_id"]
        file_path = subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
        file_path.write_text(json.dumps(developer_data, indent=2, ensure_ascii=False), encoding="utf-8")

        # Auto-remove old-format file in same directory if it's a different path
        old_canonical = self._dev_file_path_old_canonical(dev_slug)
        if old_canonical.exists() and old_canonical != file_path:
            try:
                old_canonical.unlink()
                logger.info(f"Removed old-format file {old_canonical}")
            except Exception as e:
                logger.warning(f"Could not remove old-format file {old_canonical}: {e}")

        logger.info(f"Saved developer file: {file_path}")
        return file_path

    def _enrich_with_master(self, dev: dict) -> dict:
        """Add merged_from from Level 3 for master developers (not for merged children)."""
        master_id = dev.get("master_id")
        if master_id:
            master = self._read_dev_master(master_id, dev.get("developer_slug", ""))
            if master and dev.get("usi_dev_id") == master.get("master_usi_dev_id"):
                dev["merged_from"] = master.get("merged_from", [])
            else:
                dev.setdefault("merged_from", [])
        else:
            dev.setdefault("merged_from", [])
        return dev

    def get_developer(self, dev_slug: str) -> dict | None:
        """Loads developer data. Returns merged view: Level 2 + merged_from from Level 3."""
        dev = None
        for candidate in [
            self._dev_file_path(dev_slug),              # new format (glob) — may be None
            self._dev_file_path_old_canonical(dev_slug),
            self._dev_file_path_legacy(dev_slug),
            self.data_dir / dev_slug / f"usi_dev_{dev_slug}.json",
        ]:
            if candidate and candidate.exists():
                try:
                    dev = json.loads(candidate.read_text(encoding="utf-8"))
                    break
                except Exception as e:
                    logger.error(f"Error reading developer file {candidate}: {e}")
                    return None

        if dev is None:
            return None

        return self._enrich_with_master(dev)

    def get_developer_by_id(self, usi_dev_id: str) -> dict | None:
        """Find developer by usi_dev_id. Fast path uses ID embedded in new filename."""
        if not usi_dev_id:
            return None
        # Fast path: new format — usi_dev_id is part of the filename
        for dev_file in self.dev_dir.glob(f"*/usi_dev_{usi_dev_id}_*.json"):
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
                if data.get("usi_dev_id") == usi_dev_id:
                    return self._enrich_with_master(data)
            except Exception:
                continue
        # Fallback: legacy format in dev_dir (subdirs + flat)
        for pattern in ("*/usi_dev_*.json", "usi_dev_*.json"):
            for dev_file in self.dev_dir.glob(pattern):
                if re.match(r"usi_dev_[A-Z]+-\d+_", dev_file.name):
                    continue  # already checked above
                try:
                    data = json.loads(dev_file.read_text(encoding="utf-8"))
                    if data.get("usi_dev_id") == usi_dev_id:
                        return self._enrich_with_master(data)
                except Exception:
                    continue
        # Fallback: legacy location in data_dir (USIdata/{slug}/usi_dev_{slug}.json)
        for dev_file in self.data_dir.glob("*/usi_dev_*.json"):
            if re.match(r"usi_dev_[A-Z]+-\d+_", dev_file.name):
                continue
            try:
                data = json.loads(dev_file.read_text(encoding="utf-8"))
                if data.get("usi_dev_id") == usi_dev_id:
                    return self._enrich_with_master(data)
            except Exception:
                continue
        return None

    def resolve_id_to_slug(self, usi_dev_id: str) -> str | None:
        """Return developer_slug for a given usi_dev_id, or None if not found."""
        dev = self.get_developer_by_id(usi_dev_id)
        return dev.get("developer_slug") if dev else None

    def list_developers(self, only_merged: bool = False) -> list:
        """Returns top-level developer records; merged-source children excluded."""
        # Build child IDs from all dev_master files — children are listed in merged_from[]
        child_ids: set[str] = set()
        for master_file in self.dev_dir.glob("*/dev_master_*.json"):
            try:
                master = json.loads(master_file.read_text(encoding="utf-8"))
                for m in master.get("merged_from", []):
                    if cid := m.get("usi_dev_id"):
                        child_ids.add(cid)
            except Exception:
                pass

        developers = []
        seen_ids: set[str] = set()

        def _add(dev: dict) -> None:
            dev_id = dev.get("usi_dev_id", "")
            if dev_id in seen_ids:
                return
            seen_ids.add(dev_id)
            if dev_id in child_ids:
                return
            if only_merged:
                has_master = bool(dev.get("master_id") or dev.get("merged_from"))
                pm = dev.get("portal_mapping", {})
                has_mapping = any(pm.get(p) for p in ("rp", "oto", "to"))
                if not (has_master or has_mapping):
                    return
            developers.append(dev)

        for json_file in self.dev_dir.glob("*/usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    _add(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        # Legacy flat files not yet migrated
        for json_file in self.dev_dir.glob("usi_dev_*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    _add(json.load(f))
            except Exception as e:
                logger.warning(f"Error reading {json_file}: {e}")

        return developers

    def get_total_pending_count(self) -> int:
        """Returns sum of unregistered investments for all active developers."""
        from .services.discovery_service import DiscoveryService
        ds = DiscoveryService(self.data_dir)
        identifiers = self.get_existing_identifiers()
        total = 0
        for dev in self.list_developers():
            total += ds.get_unregistered_count(dev["developer_slug"], identifiers)
        return total

    # -------------------------------------------------------------------------
    # Merge / Unmerge
    # -------------------------------------------------------------------------

    def merge_by_id(self, target_id: str, source_id: str) -> bool:
        """Merge two developers by usi_dev_id."""
        target_dev = self.get_developer_by_id(target_id)
        source_dev = self.get_developer_by_id(source_id)
        if not target_dev or not source_dev:
            logger.error(f"merge_by_id: not found — target={target_id}, source={source_id}")
            return False
        return self._do_merge(target_dev, source_dev)

    def unmerge_by_id(self, target_id: str, source_id: str) -> bool:
        """Unmerge two developers by usi_dev_id."""
        target_dev = self.get_developer_by_id(target_id)
        source_dev = self.get_developer_by_id(source_id)
        if not target_dev or not source_dev:
            logger.error(f"unmerge_by_id: not found — target={target_id}, source={source_id}")
            return False
        return self._do_unmerge(target_dev, source_dev)

    def dismiss_suggestion_by_id(self, target_id: str, suggested_id: str) -> bool:
        """Dismiss a suggestion by target usi_dev_id."""
        dev = self.get_developer_by_id(target_id)
        if not dev:
            logger.error(f"dismiss_suggestion_by_id: target not found — {target_id}")
            return False
        return self._do_dismiss(dev, suggested_id)

    def _do_merge(self, target_dev: dict, source_dev: dict) -> bool:
        """Core merge logic operating on pre-loaded developer objects — no slug-based lookups."""
        target_id = target_dev.get("usi_dev_id")
        target_slug = target_dev.get("developer_slug", "")
        source_slug = source_dev.get("developer_slug", "")

        if not target_id:
            logger.error(f"_do_merge: target has no usi_dev_id (slug={target_slug})")
            return False

        # Enrich target metadata (non-destructive)
        target_meta = target_dev.setdefault("metadata", {})
        for k, v in source_dev.get("metadata", {}).items():
            if not target_meta.get(k) and v:
                target_meta[k] = v

        # Remove source from suggestions on target — by usi_dev_id, never by slug
        source_id = source_dev.get("usi_dev_id")
        target_dev["suggestions"] = [
            s for s in target_dev.get("suggestions", [])
            if s.get("usi_dev_id") != source_id
        ]

        # Remove target from suggestions on source (reciprocal cleanup)
        source_dev["suggestions"] = [
            s for s in source_dev.get("suggestions", [])
            if s.get("usi_dev_id") != target_id
        ]

        # Update Level 3 (dev_master)
        master = self._get_or_create_dev_master(target_slug, target_dev)
        merged_from = master.setdefault("merged_from", [])
        if not any(m.get("usi_dev_id") == source_id for m in merged_from):
            merged_from.append({
                "slug": source_slug,
                "name": source_dev.get("name", source_slug),
                "usi_dev_id": source_id,
                "merged_at": datetime.now().isoformat(),
            })

        # Point source to the master file
        source_dev["master_id"] = master["dev_master_id"]

        self._save_dev_master(master, target_slug)

        dm_id = master["dev_master_id"]

        # Log event on target
        self.append_dev_log(target_slug, {
            "type": "merge_in",
            "source_slug": source_slug,
            "source_id": source_id,
            "source_name": source_dev.get("name", source_slug),
        })

        # Log event on source — DEV records are children of DM, include master_id
        self.append_dev_log(source_slug, {
            "type": "merged_into",
            "target_id": target_id,
            "target_slug": target_slug,
            "target_name": target_dev.get("name", target_slug),
            "master_id": dm_id,
        })

        self.create_developer_file(target_dev)
        self.create_developer_file(source_dev)

        # Remove any legacy USIdata dev file for source
        for lp in [self.data_dir / source_slug / f"usi_dev_{source_slug}.json"]:
            if lp.exists():
                try:
                    lp.unlink()
                    logger.info(f"Removed legacy dev file {lp}")
                except Exception as e:
                    logger.warning(f"Could not remove legacy file {lp}: {e}")

        logger.info(f"Merged {source_slug} ({source_id}) → {target_slug} ({target_id})")
        return True

    def _do_unmerge(self, target_dev: dict, source_dev: dict) -> bool:
        """Core unmerge logic operating on pre-loaded developer objects — no slug-based lookups."""
        target_slug = target_dev.get("developer_slug", "")
        source_slug = source_dev.get("developer_slug", "")
        source_id = source_dev.get("usi_dev_id")

        master_id = target_dev.get("master_id")
        if not master_id:
            logger.warning(f"unmerge: {target_slug} has no master_id — nothing to unmerge")
            return False

        master = self._read_dev_master(master_id, target_slug)
        if not master:
            logger.warning(f"unmerge: dev_master_{master_id}.json not found for {target_slug}")
            return False

        before = len(master.get("merged_from", []))
        master["merged_from"] = [
            m for m in master.get("merged_from", [])
            if m.get("usi_dev_id") != source_id
        ]
        if len(master["merged_from"]) == before:
            logger.warning(f"unmerge: {source_id} not found in merged_from of {target_slug}")
            return False

        self._save_dev_master(master, target_slug)

        # Clear master_id from source
        source_dev.pop("master_id", None)

        # If master is now empty, clean up master_id on target
        if not master.get("merged_from") and not master.get("dismissed"):
            target_dev.pop("master_id", None)
            master_path = self._dev_master_path(master_id, target_slug)
            master_path.unlink(missing_ok=True)

        # Log event
        self.append_dev_log(target_slug, {
            "type": "unmerge",
            "source_slug": source_slug,
            "source_id": source_id,
            "source_name": source_dev.get("name", source_slug),
        })

        self.create_developer_file(target_dev)
        self.create_developer_file(source_dev)

        logger.info(f"Unmerged {source_slug} ({source_id}) from {target_slug}")
        return True

    def _do_dismiss(self, dev: dict, suggested_id: str) -> bool:
        """Core dismiss logic operating on a pre-loaded developer object — no slug-based lookups."""
        dev_slug = dev.get("developer_slug", "")

        if "suggestions" not in dev:
            return False

        dismissed_item = next(
            (s for s in dev["suggestions"] if s["usi_dev_id"] == suggested_id), None
        )
        new_suggestions = [s for s in dev["suggestions"] if s["usi_dev_id"] != suggested_id]
        if len(new_suggestions) == len(dev["suggestions"]):
            return False

        dev["suggestions"] = new_suggestions

        dismissed_at = datetime.now().isoformat()
        dismisser_id = dev.get("usi_dev_id")
        dismissed_slug = dismissed_item.get("developer_slug") if dismissed_item else None
        reason = dismissed_item.get("reason") if dismissed_item else None
        score = dismissed_item.get("score") if dismissed_item else None

        master = self._get_or_create_dev_master(dev_slug, dev)
        dismissed_list = master.setdefault("dismissed", [])
        if not any(d.get("usi_dev_id") == suggested_id for d in dismissed_list):
            dismissed_list.append({
                "usi_dev_id": suggested_id,
                "slug": dismissed_slug,
                "dismisser_id": dismisser_id,
                "reason": reason,
                "score": score,
                "dismissed_at": dismissed_at,
            })
        self._save_dev_master(master, dev_slug)

        # Central registry — append-only JSONL with full pair metadata
        central_file = self.dev_dir / "dismissed_pairs.jsonl"
        central_entry = {
            "dismissed_at": dismissed_at,
            "dismisser_id": dismisser_id,
            "dismisser_slug": dev_slug,
            "dismissed_id": suggested_id,
            "dismissed_slug": dismissed_slug,
            "reason": reason,
            "score": score,
        }
        try:
            with open(central_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(central_entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.warning(f"_do_dismiss: failed to write central registry: {e}")

        self.append_dev_log(dev_slug, {
            "type": "dismiss_suggestion",
            "dismissed_slug": dismissed_slug,
            "dismissed_id": suggested_id,
        })

        self.create_developer_file(dev)
        return True

    # -------------------------------------------------------------------------
    # Portal-level lookups
    # -------------------------------------------------------------------------

    def resolve_dev_slug(self, name: str) -> str:
        """Standardizes a developer name into a slug."""
        if not name:
            return "unknown"
            
        # Find by name in current index (case-insensitive)
        for dev in self.list_developers(only_merged=False):
            if dev.get("name") and dev["name"].lower() == name.lower():
                return dev["developer_slug"]

        # WE HAVE A NAME, BUT NO RECORD. 
        # Mandate: Never slugify(name). Fallback to 'unknown' to force manual/ID link.
        return "unknown"

    def find_developer_by_id(self, portal: str, portal_id: str) -> dict | None:
        """Finds a developer by its portal-specific ID (e.g., rp id, oto agency_id)."""
        if not portal or not portal_id:
            return None

        clean_id = str(portal_id).strip()
        if portal == "oto":
            clean_id = re.sub(r"^ID", "", clean_id)

        for dev in self.list_developers(only_merged=False):
            pm = dev.get("portal_mapping", {})
            p_data = pm.get(portal)
            if not p_data:
                continue
            existing_id = p_data.get("id") or p_data.get("agency_id")
            if str(existing_id) == clean_id:
                return dev
        return None

    def find_by_portal_id(self, portal: str, portal_id: str) -> dict | None:
        """O(n) scan — finds developer with matching portal_mapping id/slug/agency_id."""
        pid = str(portal_id)
        seen_slugs = set()
        for pattern in ("*/usi_dev_*.json", "usi_dev_*.json"):
            for dev_file in self.dev_dir.glob(pattern):
                try:
                    data = json.loads(dev_file.read_text(encoding="utf-8"))
                except Exception:
                    continue
                slug = data.get("developer_slug", "")
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                pm = (data.get("portal_mapping") or {}).get(portal) or {}
                if (str(pm.get("id", "")) == pid
                        or str(pm.get("slug", "")) == pid
                        or str(pm.get("agency_id", "")) == pid):
                    return data
                for aid in pm.get("agency_ids", []):
                    if str(aid) == pid:
                        return data
        return None

    # -------------------------------------------------------------------------
    # Generic event log
    # -------------------------------------------------------------------------

    def log_event(self, dev_slug: str, event: dict) -> bool:
        """Append a generic event to the developer's log file."""
        dev = self.get_developer(dev_slug)
        if not dev:
            return False
        self.append_dev_log(dev_slug, event)
        return True
