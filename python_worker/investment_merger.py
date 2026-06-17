import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.developer_manager import DeveloperManager
import python_worker.investment_index as inv_index
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class InvestmentMerger:
    def __init__(self, data_dir: Path = None, public_dir: Path = None):
        self.data_dir = data_dir or Path(USI_DATA_DIR)
        self.public_dir = public_dir or Path(PUBLIC_USI_DIR)
        self.dm = DeveloperManager(self.data_dir)
        self.identity = InvestmentIdentityResolver(self.data_dir, self.public_dir)

    def _load_json(self, path: Path) -> dict:
        if not path.exists() or not path.is_file():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def aggregate_data(self, anchors: list[dict]) -> dict:
        """Agreguje dane z wielu kotwic (Anchor/T2) w jeden obiekt Master (T3)."""
        if not anchors:
            return {}

        first = anchors[0]
        # Generate stable Master ID from system ID
        system_id = first.get("id") or f"{first.get('portal', 'legacy')}_{first.get('portal_id', 'legacy')}"
        master_id = f"MASTER-{system_id}"
        
        master = {
            "master_id": master_id,
            "master_usi_inv_id": master_id, # for backwards compatibility or just use master_id
            "merged_from": [a["portal_id"] for a in anchors],
            "portals": [a["portal"] for a in anchors],
            "last_updated": datetime.now().isoformat(),
            "unified_data": {}
        }

        # Aggregate data from T0 (Raw) and T1 (Meta)
        for anchor in anchors:
            raw_path = self.public_dir / "USIdata" / anchor.get("raw_file", "")
            meta_path = self.public_dir / "USIdata" / anchor.get("meta_file", "")
            
            raw_data = self._load_json(raw_path)
            meta_data = self._load_json(meta_path)
            
            # Simple merge: prefer meta, then raw
            master["unified_data"][anchor["portal"]] = {
                "raw": raw_data,
                "meta": meta_data
            }
            
        return master

    def sync_master(self, inv_id: str, anchors: list[dict]):
        """Tworzy lub aktualizuje rekord Master (T3) dla zestawu kotwic."""
        master = self.aggregate_data(anchors)
        master_path = self.public_dir / "USIdata" / f"inv_master_{master['master_id']}.json"
        
        # Ensure directory exists
        master_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write: write to temp then rename
        temp_path = master_path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(master, indent=2, ensure_ascii=False))
        temp_path.replace(master_path)
        
        logger.info(f"Sync complete: Master {master['master_id']} persisted.")

    def _find_index_entry(self, usi_inv_id: str) -> Optional[dict]:
        index_data = inv_index.load(self.data_dir)
        if not index_data:
            return None
        for entry in index_data:
            if entry.get("usi_inv_id") == usi_inv_id:
                return entry
        return None

    def merge_by_id(self, target_inv_id: str, source_inv_id: str) -> bool:
        if target_inv_id == source_inv_id:
            logger.error("Cannot merge investment into itself.")
            return False

        target_entry = self._find_index_entry(target_inv_id)
        source_entry = self._find_index_entry(source_inv_id)

        if not target_entry or not source_entry:
            logger.error("Target or Source investment not found in index.")
            return False

        t_dev_slug = target_entry["developer_slug"]
        t_inv_slug = target_entry["investment_slug"]
        s_dev_slug = source_entry["developer_slug"]
        s_inv_slug = source_entry["investment_slug"]

        t_res = self.identity.get_investment_resources(target_inv_id)
        s_res = self.identity.get_investment_resources(source_inv_id)

        if not t_res or not s_res:
            logger.error("Target or Source resource mapping could not be resolved.")
            return False

        t_inv_dir = t_res["base_dir"]
        s_inv_dir = s_res["base_dir"]
        t_usi_file = t_res["files"].get("anchor")
        s_usi_file = s_res["files"].get("anchor")

        if not t_usi_file or not s_usi_file:
            logger.error("Underlying USI JSON files not found.")
            return False

        # Load Source
        with open(s_usi_file, "r", encoding="utf-8") as f:
            s_data = json.load(f)

        # Ensure target is not already merged into something else
        # Actually, target_entry could already have a master_id if it's merged
        with open(t_usi_file, "r", encoding="utf-8") as f:
            t_data = json.load(f)

        if t_data.get("master_id"):
            logger.warning(f"Target investment {target_inv_id} is already merged into {t_data.get('master_id')}. Redirecting merge.")
            # Merge into the existing master instead
            target_master_id = t_data.get("master_id")
            # For simplicity, we can just reject or we could recurse. Reject for now.
            logger.error("Target is already a child. Cannot merge into a child.")
            return False

        # Find or create master file for target
        # The master file will be inv_master_{IM_ID}.json in target's directory
        master_file_path = None
        master_id = None
        master_data = {}

        for mf in t_inv_dir.glob("inv_master_*.json"):
            master_file_path = mf
            master_id = mf.name.replace("inv_master_", "").replace(".json", "")
            with open(mf, "r", encoding="utf-8") as f:
                master_data = json.load(f)
            break

        if not master_file_path:
            master_id = f"MASTER-{target_inv_id}"
            master_file_path = t_inv_dir / f"inv_master_{master_id}.json"
            master_data = {
                "inv_master_id": master_id,
                "master_usi_inv_id": target_inv_id,
                "master_slug": f"{t_dev_slug}/{t_inv_slug}",
                "merged_from": [],
                "dismissed": [],
                "ratings": {}, # Master can collect combined ratings
                "audit": {
                    "created_at": datetime.now().isoformat()
                }
            }

        # Check if source is already merged
        old_master_id = s_data.get("master_id")
        if old_master_id == master_id:
            logger.info("Source is already merged into this target.")
            return True

        if old_master_id:
            logger.warning(f"Source {source_inv_id} was merged into {old_master_id}. Removing from old master.")
            self.unmerge_by_id(old_master_id, source_inv_id)
            # reload source data as unmerge modifies it
            with open(s_usi_file, "r", encoding="utf-8") as f:
                s_data = json.load(f)

        # Add target itself to merged_from if not already there, so we have a full list of sources
        target_in_list = any(m.get("usi_inv_id") == target_inv_id for m in master_data["merged_from"])
        if not target_in_list:
            master_data["merged_from"].append({
                "usi_inv_id": target_inv_id,
                "dev_slug": t_dev_slug,
                "inv_slug": t_inv_slug,
                "merged_at": datetime.now().isoformat(),
                "role": "primary"
            })

        # Add source
        master_data["merged_from"].append({
            "usi_inv_id": source_inv_id,
            "dev_slug": s_dev_slug,
            "inv_slug": s_inv_slug,
            "merged_at": datetime.now().isoformat()
        })
        master_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

        # Update source
        s_data["master_id"] = master_id
        s_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
        s_data["audit"].setdefault("history", []).append({
            "timestamp": datetime.now().isoformat(),
            "event": "Merged",
            "changes": [{"field": "master_id", "old": None, "new": master_id}]
        })

        # Także daj targetowi master_id pointing to the same master!
        if not t_data.get("master_id"):
            t_data["master_id"] = master_id
            t_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

        # NOWY BLOK: Propagacja i unifikacja słowników sources z obsługą duplikatów portali
        if "sources" not in t_data:
            t_data["sources"] = {}

        for src_k, src_v in s_data.get("sources", {}).items():
            if src_k in t_data["sources"]:
                # Jeśli klucz portalu już istnieje (np. oba to 'oto'), tworzymy unikalny klucz powiązania
                unique_key = f"{src_k}_merged_{source_inv_id}"
                t_data["sources"][unique_key] = src_v
            else:
                t_data["sources"][src_k] = src_v

        with open(t_usi_file, "w", encoding="utf-8") as f:
            json.dump(t_data, f, indent=2, ensure_ascii=False)

        # Save files
        with open(master_file_path, "w", encoding="utf-8") as f:
            json.dump(master_data, f, indent=2, ensure_ascii=False)

        with open(s_usi_file, "w", encoding="utf-8") as f:
            json.dump(s_data, f, indent=2, ensure_ascii=False)

        # Always update index for target because merged_from has changed
        inv_index.upsert(self.data_dir, self.public_dir, t_dev_slug, t_inv_slug)
        # Update index for source
        inv_index.upsert(self.data_dir, self.public_dir, s_dev_slug, s_inv_slug)

        # Logs
        # Master gets a log entry
        log_path = t_inv_dir / f"inv_master_log_{master_id}.txt"
        with open(log_path, "a", encoding="utf-8") as lf:
            lf.write(f"[{datetime.now().isoformat()}] Merged {s_dev_slug}/{s_inv_slug} ({source_inv_id}) into this master.\n")

        # Source isolated log
        log_to_processing_log(s_dev_slug, s_inv_slug, f"Merged into master {master_id} (Target: {target_inv_id})")

        return True

    def unmerge_by_id(self, master_id: str, source_inv_id: str) -> bool:
        source_entry = self._find_index_entry(source_inv_id)
        if not source_entry:
            logger.error("Source investment not found in index.")
            return False

        s_dev_slug = source_entry["developer_slug"]
        s_inv_slug = source_entry["investment_slug"]
        s_inv_dir = self.data_dir / s_dev_slug / s_inv_slug
        s_res = self.identity.get_investment_resources(source_inv_id)
        s_usi_file = s_res["files"].get("anchor") if s_res else None

        if not s_usi_file:
            return False

        with open(s_usi_file, "r", encoding="utf-8") as f:
            s_data = json.load(f)

        if s_data.get("master_id") != master_id:
            logger.error("Source is not merged into the specified master.")
            return False

        s_data["master_id"] = None
        s_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
        s_data["audit"].setdefault("history", []).append({
            "timestamp": datetime.now().isoformat(),
            "event": "Unmerged",
            "changes": [{"field": "master_id", "old": master_id, "new": None}]
        })

        # POPRAWKA: Rekonstrukcja identyfikatora docelowego z master_id i poprawne mapowanie zasobów
        target_inv_id = master_id.replace("MASTER-", "")
        t_res = self.identity.get_investment_resources(target_inv_id)
        
        if not t_res:
            logger.error(f"Target investment resources for ID {target_inv_id} could not be resolved.")
            return False
            
        t_inv_dir = t_res["base_dir"]
        master_file_path = t_inv_dir / f"inv_master_{master_id}.json"

        if master_file_path.exists():
            with open(master_file_path, "r", encoding="utf-8") as f:
                master_data = json.load(f)

            master_data["merged_from"] = [m for m in master_data.get("merged_from", []) if m.get("usi_inv_id") != source_inv_id]
            master_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

            with open(master_file_path, "w", encoding="utf-8") as f:
                json.dump(master_data, f, indent=2, ensure_ascii=False)

            # Logowanie do pliku master_log w katalogu inwestycji docelowej
            log_path = t_inv_dir / f"inv_master_log_{master_id}.txt"
            with open(log_path, "a", encoding="utf-8") as lf:
                lf.write(f"[{datetime.now().isoformat()}] Unmerged {s_dev_slug}/{s_inv_slug} ({source_inv_id}).\n")

            # Aktualizacja indeksu inwestycji docelowej przy użyciu właściwych slugów z t_res
            inv_index.upsert(self.data_dir, self.public_dir, t_res["metadata"]["developer_slug"], t_res["metadata"]["investment_slug"])
        else:
            logger.error(f"Master file not found at expected location: {master_file_path}")
            return False

        with open(s_usi_file, "w", encoding="utf-8") as f:
            json.dump(s_data, f, indent=2, ensure_ascii=False)

        inv_index.upsert(self.data_dir, self.public_dir, s_dev_slug, s_inv_slug)
        log_to_processing_log(s_dev_slug, s_inv_slug, f"Unmerged from master {master_id}")

        return True

    def dismiss_suggestion_by_id(self, target_inv_id: str, suggested_inv_id: str) -> bool:
        # Central dismissed pairs logic
        dismiss_file = self.data_dir / "dismissed_inv_pairs.jsonl"
        entry = json.dumps({
            "dismisser_id": target_inv_id,
            "dismissed_id": suggested_inv_id,
            "at": datetime.now().isoformat()
        }, ensure_ascii=False)
        
        with open(dismiss_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
            
        # Also remove from local suggestions
        target_entry = self._find_index_entry(target_inv_id)
        if target_entry:
            t_res = self.identity.get_investment_resources(target_inv_id)
            if not t_res:
                return False
                
            t_inv_dir = t_res["base_dir"]
            t_usi_file = t_res["files"].get("anchor")
            if t_usi_file:
                with open(t_usi_file, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                suggestions = t_data.get("suggestions", [])
                t_data["suggestions"] = [s for s in suggestions if s.get("usi_inv_id") != suggested_inv_id]
                with open(t_usi_file, "w", encoding="utf-8") as f:
                    json.dump(t_data, f, indent=2, ensure_ascii=False)
                # POPRAWKA: Pobranie zmiennych ze słownika target_entry przed wykonaniem upsert
                t_dev_slug = target_entry["developer_slug"]
                t_inv_slug = target_entry["investment_slug"]
                inv_index.upsert(self.data_dir, self.public_dir, t_dev_slug, t_inv_slug)
        
        return True
