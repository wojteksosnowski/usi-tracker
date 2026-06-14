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
