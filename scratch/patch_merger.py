import re
from pathlib import Path

merger_py = Path('/Volumes/Samsam/claude-py/usi-tracker/python_worker/investment_merger.py')
content = merger_py.read_text()

build_func = """
    def _build_and_save_master(self, master_id: str, primary_inv_id: str, secondary_inv_id: str):
        # Znajdź wszystkie pliki z tym master_id
        from python_worker.investment_index import get_investment_index
        index = get_investment_index()
        # Odświeżamy indeks żeby zobaczyć nowe master_id dodane przez wywołanie _atomic_write wcześniej
        index.add_or_update(primary_inv_id, {"master_id": master_id})
        index.add_or_update(secondary_inv_id, {"master_id": master_id})
        
        member_ids = []
        for e in index.get_all():
            # it might not return is_grouped so we check internal
            pass
            
        # Właściwie, members = index._index
        with index._index_lock:
            for uid, e in index._index.items():
                if e.get("master_id") == master_id:
                    member_ids.append(uid)
                    
        # Teraz budujemy pełny plik T3
        from python_worker.identity import USIIdentity
        identity = USIIdentity()
        
        master_record = {
            "usi_inv_id": master_id,
            "location": {},
            "financials": {},
            "specifications": {"units_count": 0},
            "amenities_matched": [],
            "image_paths": [],
            "sources": {},
            "developer_slug": None,
            "investment_slug": master_id
        }
        
        min_price = float('inf')
        max_price = 0
        min_price_m2 = float('inf')
        max_price_m2 = 0
        
        seen_images = set()
        seen_amenities = set()
        
        # Ensure the primary is processed first to grab location
        if primary_inv_id in member_ids:
            member_ids.remove(primary_inv_id)
            member_ids.insert(0, primary_inv_id)
            
        for idx, mid in enumerate(member_ids):
            res = identity.get_investment_resources(mid)
            if not res or not res["files"].get("anchor"): continue
            try:
                import json
                data = json.loads(res["files"]["anchor"].read_text())
            except:
                continue
                
            if idx == 0:
                master_record["location"] = data.get("location", {})
                master_record["developer_slug"] = res["metadata"].get("developer_slug")
                
            # Merge financials
            fin = data.get("financials", {})
            if fin.get("price_min"): min_price = min(min_price, float(fin["price_min"]))
            if fin.get("price_max"): max_price = max(max_price, float(fin["price_max"]))
            if fin.get("price_m2_min"): min_price_m2 = min(min_price_m2, float(fin["price_m2_min"]))
            if fin.get("price_m2_max"): max_price_m2 = max(max_price_m2, float(fin["price_m2_max"]))
            
            # Merge units
            units = data.get("specifications", {}).get("units_count")
            if units: master_record["specifications"]["units_count"] += int(units)
            
            # Merge amenities
            for am in data.get("amenities_matched", []):
                if am["code"] not in seen_amenities:
                    seen_amenities.add(am["code"])
                    master_record["amenities_matched"].append(am)
                    
            # Merge images
            for img in data.get("image_paths", []):
                if img not in seen_images:
                    seen_images.add(img)
                    master_record["image_paths"].append(img)
                    
            # Merge sources
            master_record["sources"].update(data.get("sources", {}))

        if min_price != float('inf'): master_record["financials"]["price_min"] = min_price
        if max_price != 0: master_record["financials"]["price_max"] = max_price
        if min_price_m2 != float('inf'): master_record["financials"]["price_m2_min"] = min_price_m2
        if max_price_m2 != 0: master_record["financials"]["price_m2_max"] = max_price_m2
        
        # Save it
        master_dir = self.data_dir.parent / "USImaster"
        master_dir.mkdir(parents=True, exist_ok=True)
        out_path = master_dir / f"usi_{master_id}.json"
        
        _atomic_write(out_path, master_record)
        # Notify index of new master!
        index.add_or_update(master_id, master_record)
"""

content = content.replace("class InvestmentMerger:", "class InvestmentMerger:\n" + build_func)

# Replace the merge_by_id logic
# We need to find the old master_data creation logic and remove it
new_merge_logic = """
        # --- Wyznacz lub utwórz master_id ---
        master_id = p_data.get("master_id")
        if not master_id:
            from python_worker.developer_indexer import DeveloperIndexer
            master_id = DeveloperIndexer(None).generate_usi_id("IM")

        # --- Aktualizuj oba rekordy anchor ---
        p_data["master_id"] = master_id
        p_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

        s_data["master_id"] = master_id
        s_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
        s_data["audit"].setdefault("history", []).append({
            "timestamp": datetime.now().isoformat(),
            "event": "Merged into group",
            "changes": [{"field": "master_id", "old": old_s_master, "new": master_id}]
        })

        # --- Atomowe zapisy ---
        _atomic_write(p_file, p_data)
        _atomic_write(s_file, s_data)
        
        # Build master
        self._build_and_save_master(master_id, primary_inv_id, secondary_inv_id)
"""

content = re.sub(
    r"# --- Wyznacz lub utwórz master_id ---.*?_atomic_write\(master_path, master_data\).*?_atomic_write\(s_file, s_data\)",
    new_merge_logic.strip(),
    content,
    flags=re.DOTALL
)

merger_py.write_text(content)
