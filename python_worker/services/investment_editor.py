import json
import logging
from datetime import datetime
from pathlib import Path

from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class InvestmentEditorService:
    def __init__(self, identity_resolver, data_dir: Path, public_usi_dir: Path, investment_repo=None):
        from python_worker.investment_repository import InvestmentRepository
        self.repo = investment_repo or InvestmentRepository(identity_resolver, data_dir)
        self.identity = identity_resolver
        self.data_dir = data_dir
        self.public_usi_dir = public_usi_dir

    def save_ratings(self, system_id, payload):
        from python_worker.api.utils import _CATS, USI_STATUSES
        
        resources = self.identity.get_investment_resources(system_id)
        if not resources or not resources["files"]["anchor"]:
            logger.error(f"Cannot save ratings: Investment {system_id} not found.")
            return False
            
        inv_dir = resources["base_dir"]
        usi_file = resources["files"]["anchor"]
        
        # Meta file for legacy compatibility
        meta_slug = resources["metadata"]["slug"].split("/")[-1]
        ratings_file = inv_dir / f"meta_{meta_slug}_ratings.json"
        
        existing_ratings = {}
        if ratings_file.exists():
            try:
                existing_ratings = json.loads(ratings_file.read_text())
            except: pass

        changes = []
        for cat in _CATS:
            if cat in payload:
                val = payload[cat]
                if val is not None:
                    if not isinstance(val, (int, float)) or not (0 <= val <= 4):
                        raise ValueError(f"Invalid value for {cat}: {val}")
                    new_val = float(val)
                else:
                    new_val = None
                
                if existing_ratings.get(cat) != new_val:
                    changes.append({"field": f"ratings.{cat}", "old": existing_ratings.get(cat), "new": new_val})
                    existing_ratings[cat] = new_val

        if "komentarz" in payload:
            if existing_ratings.get("komentarz") != str(payload["komentarz"]):
                changes.append({"field": "komentarz", "old": existing_ratings.get("komentarz"), "new": str(payload["komentarz"])})
            existing_ratings["komentarz"] = str(payload["komentarz"])
            
        if "status" in payload:
            new_status = payload["status"]
            if new_status not in USI_STATUSES:
                raise ValueError(f"Invalid status: {new_status}")
            if existing_ratings.get("status") != new_status:
                changes.append({"field": "status", "old": existing_ratings.get("status"), "new": new_status})
            existing_ratings["status"] = new_status

        if "Segment" in payload:
            new_seg = payload["Segment"]
            if existing_ratings.get("Segment") != new_seg:
                changes.append({"field": "specifications.segment", "old": existing_ratings.get("Segment"), "new": new_seg})
                existing_ratings["Segment"] = new_seg

        try:
            usi_data = json.loads(usi_file.read_text())
            
            # Aktualny status
            current_status = existing_ratings.get("status", usi_data.get("status", "Brak"))
            
            # Automatyczna zmiana statusu na "Wstępna" gdy edytowano coś z ocen i status to "Brak"
            if changes and "status" not in payload and (not current_status or current_status.lower() == "brak"):
                current_status = "Wstępna"
                existing_ratings["status"] = current_status
                changes.append({"field": "status", "old": "Brak", "new": "Wstępna"})

            usi_data["ratings"] = {**usi_data.get("ratings", {}), **existing_ratings}
            usi_data["status"] = current_status
            if "Segment" in existing_ratings:
                spec = usi_data.setdefault("specifications", {})
                spec["segment"] = existing_ratings["Segment"]

            audit = usi_data.setdefault("audit", {})
            audit["updated_at"] = datetime.now().isoformat()
            if changes:
                audit.setdefault("history", []).append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "Rating Updated",
                    "changes": changes
                })
                # Log to processing log (requires slugs)
                slug_parts = resources["metadata"]["slug"].split("/")
                log_to_processing_log(slug_parts[0], slug_parts[1], f"Ratings updated via ID {system_id}. Changes: {len(changes)}")
            
            self.repo.save_investment_json(system_id, usi_data)
        except Exception as e:
            logger.error(f"Service ratings update error for {system_id}: {e}")

        # Update legacy ratings file
        self.repo.save_ratings(system_id, existing_ratings)

        try:
            import python_worker.investment_index as inv_index
            inv_index.upsert(self.data_dir, self.public_usi_dir, inv_id=system_id)
        except Exception as _ie:
            logger.debug(f"Index upsert skipped after ratings save for {system_id}: {_ie}")

        return True

    def mark_as_reviewed(self, system_id):
        """Sets the reviewed flag to true for the specified investment."""
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            logger.error(f"Cannot mark as reviewed: Investment {system_id} not found.")
            return False
            
        slug_parts = resources["metadata"]["slug"].split("/")
        
        try:
            data = self.repo.get_investment_json(system_id)
            if not data:
                return False

            data["reviewed"] = True
            data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

            self.repo.save_investment_json(system_id, data)

            log_to_processing_log(slug_parts[0], slug_parts[1], f"Investment {system_id} marked as reviewed by analyst.")
            return True
        except Exception as e:
            logger.error(f"Failed to mark as reviewed for {system_id}: {e}")
            return False
            
        usi_file = resources["files"]["anchor"]
        slug_parts = resources["metadata"]["slug"].split("/")

        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["reviewed"] = True
            data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

            with open(usi_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_to_processing_log(slug_parts[0], slug_parts[1], f"Investment {system_id} marked as reviewed by analyst.")
            return True
        except Exception as e:
            logger.error(f"Failed to mark as reviewed for {system_id}: {e}")
            return False

    def add_report(self, system_id, note):
        """Adds a problem report note to the investment record."""
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            logger.error(f"Cannot add report: Investment {system_id} not found.")
            return False
            
        slug_parts = resources["metadata"]["slug"].split("/")

        try:
            data = self.repo.get_investment_json(system_id)
            if not data:
                return False

            reports = data.setdefault("issue_reports", [])
            reports.insert(0, {
                "note": note,
                "at": datetime.now().isoformat()
            })

            audit = data.setdefault("audit", {})
            audit["updated_at"] = datetime.now().isoformat()
            audit["audit_needed"] = True

            self.repo.save_investment_json(system_id, data)

            log_to_processing_log(slug_parts[0], slug_parts[1], f"Issue reported for {system_id}: {note[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add report for {system_id}: {e}")
            return False
            
        usi_file = resources["files"]["anchor"]
        slug_parts = resources["metadata"]["slug"].split("/")

        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            reports = data.setdefault("issue_reports", [])
            reports.insert(0, {
                "note": note,
                "at": datetime.now().isoformat()
            })

            audit = data.setdefault("audit", {})
            audit["updated_at"] = datetime.now().isoformat()
            audit["audit_needed"] = True

            with open(usi_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_to_processing_log(slug_parts[0], slug_parts[1], f"Issue reported for {system_id}: {note[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add report for {system_id}: {e}")
            return False

    def mark_deleted_photos(self, system_id, paths):
        resources = self.identity.get_investment_resources(system_id)
        if not resources:
            return False
            
        try:
            deleted = set(self.repo.get_deleted_items(system_id))
            for path in paths:
                deleted.add(path)
                
            self.repo.mark_as_deleted(system_id, list(deleted))
            
            slug_parts = resources["metadata"]["slug"].split("/")
            log_to_processing_log(slug_parts[0], slug_parts[1], f"Marked {len(paths)} photos as deleted via ID {system_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark deleted photos for {system_id}: {e}")
            return False
            
        inv_dir = resources["base_dir"]
        deletion_file = inv_dir / "deletion_list.json"
        
        try:
            deleted = set()
            if deletion_file.exists():
                deleted = set(json.loads(deletion_file.read_text()))
                
            for path in paths:
                deleted.add(path)
                
            self.repo.mark_as_deleted(system_id, list(deleted))
            
            slug_parts = resources["metadata"]["slug"].split("/")
            log_to_processing_log(slug_parts[0], slug_parts[1], f"Marked {len(paths)} photos as deleted via ID {system_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to mark deleted photos for {system_id}: {e}")
            return False
