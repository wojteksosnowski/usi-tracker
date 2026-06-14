import sys
file_path = 'python_worker/api/blueprints/investments.py'
with open(file_path, 'r') as f:
    content = f.read()

old_code = """        results = service.list_investments_filtered(**filters)
        
        # Odtworzenie struktury wymaganej przez data.jsx
        unreviewed_count = sum(1 for inv in (inv_index.load(Path(USI_DATA_DIR)) or []) if inv.get("reviewed") is False)
        return jsonify({"data": results, "unreviewedCount": unreviewed_count}), 200"""

new_code = """        results = service.list_investments_filtered(**filters)
        
        # Odtworzenie struktury wymaganej przez data.jsx
        all_invs = inv_index.load(Path(USI_DATA_DIR)) or []
        unreviewed_count = sum(1 for inv in all_invs if inv.get("reviewed") is False)
        
        # Build ratingsMap for nearby investments fallback when filtered
        ratings_map = {
            i.get("usi_inv_id"): i.get("ratings")
            for i in all_invs
            if i.get("ratings") and i.get("usi_inv_id")
        }
        
        return jsonify({"data": results, "unreviewedCount": unreviewed_count, "ratingsMap": ratings_map}), 200"""

if old_code in content:
    content = content.replace(old_code, new_code)
    with open(file_path, 'w') as f:
        f.write(content)
    print("Patched!")
else:
    print("Could not find old code.")
