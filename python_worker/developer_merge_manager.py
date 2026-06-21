import json
import logging
import re
import threading
from pathlib import Path
from datetime import datetime
from python_worker.slug_utils import slugify

_counter_lock = threading.Lock()
logger = logging.getLogger(__name__)

class DeveloperMergeManager:

    def __init__(self, repo, indexer):
        self.repo = repo
        self.indexer = indexer

    def append_dev_log(self, dev_slug: str, event: dict):
        return self.repo.append_dev_log(dev_slug, event)

    def merge_by_id(self, target_id: str, source_id: str) -> bool:
        """Merge two developers by usi_dev_id."""
        target_dev = self.repo.get_developer_by_id(target_id)
        source_dev = self.repo.get_developer_by_id(source_id)
        if not target_dev or not source_dev:
            logger.error(f"merge_by_id: not found — target={target_id}, source={source_id}")
            return False
        return self._do_merge(target_dev, source_dev)

    def unmerge_by_id(self, target_id: str, source_id: str) -> bool:
        """Unmerge two developers by usi_dev_id."""
        target_dev = self.repo.get_developer_by_id(target_id)
        source_dev = self.repo.get_developer_by_id(source_id)
        if not target_dev or not source_dev:
            logger.error(f"unmerge_by_id: not found — target={target_id}, source={source_id}")
            return False
        return self._do_unmerge(target_dev, source_dev)



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
        master = self.repo._get_or_create_dev_master(target_slug, target_dev)
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

        self.repo._save_dev_master(master, target_slug)

        dm_id = master["dev_master_id"]

        # Log event on target
        self.repo.append_dev_log(target_slug, {
            "type": "merge_in",
            "source_slug": source_slug,
            "source_id": source_id,
            "source_name": source_dev.get("name", source_slug),
        })

        # Log event on source — DEV records are children of DM, include master_id
        self.repo.append_dev_log(source_slug, {
            "type": "merged_into",
            "target_id": target_id,
            "target_slug": target_slug,
            "target_name": target_dev.get("name", target_slug),
            "master_id": dm_id,
        })

        self.repo.create_developer_file(target_dev)
        self.repo.create_developer_file(source_dev)

        # Remove any legacy USIdata dev file for source
        for lp in [self.repo.data_dir / source_slug / f"usi_dev_{source_slug}.json"]:
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

        master = self.repo._read_dev_master(master_id)
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

        self.repo._save_dev_master(master, target_slug)

        # Clear master_id from source
        source_dev.pop("master_id", None)

        # If master is now empty, clean up master_id on target
        if not master.get("merged_from") and not master.get("dismissed"):
            target_dev.pop("master_id", None)
            master_path = self.repo._dev_master_path(master_id, target_slug)
            master_path.unlink(missing_ok=True)

        # Log event
        self.append_dev_log(target_slug, {
            "type": "unmerge",
            "source_slug": source_slug,
            "source_id": source_id,
            "source_name": source_dev.get("name", source_slug),
        })

        self.repo.create_developer_file(target_dev)
        self.repo.create_developer_file(source_dev)

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

        master = self.repo._get_or_create_dev_master(dev_slug, dev)
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
        self.repo._save_dev_master(master, dev_slug)

        # Central registry — append-only JSONL with full pair metadata
        central_file = self.repo.dev_dir / "dismissed_pairs.jsonl"
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

        self.repo.create_developer_file(dev)
        return True

    # -------------------------------------------------------------------------
    # Portal-level lookups
    # -------------------------------------------------------------------------
