import json
import uuid
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver
import python_worker.investment_index as inv_index

class InvestmentGroupService:
    def __init__(self):
        self.data_dir = Path(USI_DATA_DIR)
        self.identity = InvestmentIdentityResolver(self.data_dir, self.data_dir)

    def create_or_extend_group(self, source_id: str, target_id: str) -> str:
        source_res = self.identity.get_investment_resources(source_id)
        target_res = self.identity.get_investment_resources(target_id)
        
        if not source_res or not target_res:
            raise ValueError("Nie można odnaleźć plików USI dla podanych ID.")
            
        src_file = source_res["files"].get("anchor")
        tgt_file = target_res["files"].get("anchor")
        
        src_data = json.loads(src_file.read_text(encoding="utf-8"))
        tgt_data = json.loads(tgt_file.read_text(encoding="utf-8"))
        
        # --- NOWA LOGIKA: Wykrywanie i automatyczne łączenie deweloperów ---
        src_dev_id = src_data.get("usi_dev_id")
        tgt_dev_id = tgt_data.get("usi_dev_id")
        
        if src_dev_id and tgt_dev_id and src_dev_id != tgt_dev_id:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"[DEV_MERGE] Wykryto różnych deweloperów: {src_dev_id} oraz {tgt_dev_id}. Uruchamiam fuzję.")
            self._merge_developers(master_dev_id=src_dev_id, secondary_dev_id=tgt_dev_id)
        # ------------------------------------------------------------------
        
        master_id = src_data.get("master_id") or tgt_data.get("master_id")
        if not master_id:
            master_id = f"MST-{uuid.uuid4().hex[:8].upper()}"
            
        for file_path, data in [(src_file, src_data), (tgt_file, tgt_data)]:
            data["master_id"] = master_id
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

        inv_dir = source_res["base_dir"]
        master_file_path = inv_dir / f"master_{master_id}.json"
        
        grouped_ids = set([source_id, target_id])
        for p in inv_dir.glob("usi_*.json"):
            try:
                p_data = json.loads(p.read_text(encoding="utf-8"))
                if p_data.get("master_id") == master_id:
                    grouped_ids.add(p_data.get("usi_inv_id") or p.stem.replace("usi_", ""))
            except Exception:
                pass

        master_payload = {
            "master_id": master_id,
            "updated_at": Path(src_file).stat().st_mtime,
            "investments": sorted(list(grouped_ids)),
            "primary_name": src_data.get("name") or tgt_data.get("name")
        }
        master_file_path.write_text(json.dumps(master_payload, indent=2, ensure_ascii=False), encoding="utf-8")
        
        inv_index.rebuild(self.data_dir, self.data_dir) 
        return master_id

    def _merge_developers(self, master_dev_id: str, secondary_dev_id: str):
        import logging
        logger = logging.getLogger(__name__)
        from python_worker.developer_merge_manager import DeveloperMergeManager
        
        merge_mgr = DeveloperMergeManager(self.data_dir)
        success = merge_mgr.merge_developer_records(master_id=master_dev_id, slave_id=secondary_dev_id)
        
        if success:
            logger.info(f"[DEV_MERGE] Pomyślnie scalono rekordy deweloperów w strukturze USIdev.")
            self._backfill_investments_with_new_dev(secondary_dev_id, master_dev_id)
            
            from python_worker.developer_manager import DeveloperManager
            dm = DeveloperManager(self.data_dir)
            dm.invalidate_identifiers_cache()

    def _backfill_investments_with_new_dev(self, old_dev_id: str, new_dev_id: str):
        import logging
        from datetime import datetime
        logger = logging.getLogger(__name__)
        logger.info(f"[DEV_MERGE] Rozpoczynam aktualizację usi_dev_id we wszystkich inwestycjach z {old_dev_id} -> {new_dev_id}")
        
        for usi_file in self.data_dir.glob("**/usi_*.json"):
            try:
                data = json.loads(usi_file.read_text(encoding="utf-8"))
                if data.get("usi_dev_id") == old_dev_id:
                    data["usi_dev_id"] = new_dev_id
                    
                    if "audit" in data and "history" in data["audit"]:
                        data["audit"]["history"].append({
                            "timestamp": datetime.now().isoformat(),
                            "event": "Auto Developer Merge (Cascade)",
                            "changes": [{"field": "usi_dev_id", "old": old_dev_id, "new": new_dev_id}]
                        })
                        
                    usi_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
                    logger.debug(f"[DEV_MERGE] Zaktualizowano inwestycję: {usi_file.name}")
            except Exception as e:
                logger.error(f"Błąd podczas kaskadowej aktualizacji dewelopera w pliku {usi_file}: {e}")
