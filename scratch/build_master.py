import json
from pathlib import Path
from python_worker.config import PUBLIC_DIR

def build_master_record(master_id: str, member_ids: list):
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
        "investment_slug": None
    }
    
    min_price = float('inf')
    max_price = 0
    min_price_m2 = float('inf')
    max_price_m2 = 0
    
    seen_images = set()
    seen_amenities = set()
    
    for idx, mid in enumerate(member_ids):
        res = identity.get_investment_resources(mid)
        if not res or not res["files"].get("anchor"): continue
        try:
            data = json.loads(res["files"]["anchor"].read_text())
        except:
            continue
            
        if idx == 0:
            master_record["location"] = data.get("location", {})
            master_record["developer_slug"] = res["metadata"].get("developer_slug")
            master_record["investment_slug"] = res["metadata"].get("investment_slug")
            
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
    master_dir = PUBLIC_DIR / "USImaster"
    master_dir.mkdir(parents=True, exist_ok=True)
    out_path = master_dir / f"usi_{master_id}.json"
    
    import tempfile, os
    tmp_fd, tmp_path = tempfile.mkstemp(dir=str(master_dir))
    with os.fdopen(tmp_fd, 'w', encoding='utf-8') as f:
        json.dump(master_record, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, out_path)
    print(f"Built {out_path}")

build_master_record("IM-0028", ["INV-29824", "INV-29825"])
