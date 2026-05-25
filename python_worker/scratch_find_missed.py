import json
from pathlib import Path
from collections import defaultdict
import math

def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

with open("/Volumes/Samsam/Public/USIdata/_index.json", "r") as f:
    index_data = json.load(f)
    invs = index_data.get("entries", [])

# Group by lowercase name
name_groups = defaultdict(list)
for inv in invs:
    name = (inv.get("name") or "").strip().lower()
    if len(name) > 3:
        name_groups[name].append(inv)

missed = []

for name, items in name_groups.items():
    if len(items) < 2:
        continue
    for i in range(len(items)):
        for j in range(i+1, len(items)):
            inv1 = items[i]
            inv2 = items[j]
            if inv1.get("master_id") and inv1.get("master_id") == inv2.get("master_id"):
                continue # merged
            
            c1 = inv1.get("coords")
            c2 = inv2.get("coords")
            if not c1 or not c2 or not c1[0] or not c2[0]:
                continue
                
            dist = haversine(c1[0], c1[1], c2[0], c2[1])
            if dist < 0.5: # 500 meters
                # Check if they are suggested to each other
                sugg1 = {s.get("usi_inv_id") for s in inv1.get("suggestions", [])}
                sugg2 = {s.get("usi_inv_id") for s in inv2.get("suggestions", [])}
                id1 = inv1.get("usi_inv_id")
                id2 = inv2.get("usi_inv_id")
                
                if id2 not in sugg1 and id1 not in sugg2:
                    missed.append((inv1, inv2, dist))

for m in missed[:10]:
    i1, i2, dist = m
    print(f"MISSED: {i1['name']} ({i1['usi_inv_id']}, {i1['developer']}) <-> {i2['name']} ({i2['usi_inv_id']}, {i2['developer']}) | dist: {dist:.2f}km")

print(f"Total missed identical names < 500m apart: {len(missed)}")
