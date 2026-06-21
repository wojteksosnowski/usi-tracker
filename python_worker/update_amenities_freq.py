import csv
from collections import Counter
import sys
from pathlib import Path
import json

# Setup paths
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.investment_index import InvestmentIndex
from python_worker.services.investment_loader import InvestmentLoaderService

def update_amenities_freq():
    idx = InvestmentIndex()
    loader = InvestmentLoaderService()
    
    c = Counter()
    
    all_invs = idx.get_all()
    total = len(all_invs)
    print(f"Loaded {total} master investments from index.")
    
    for i, inv in enumerate(all_invs):
        if i % 1000 == 0:
            print(f"Processed {i}/{total}...")
        
        full_inv = loader.load_investment(inv['id'])
        if not full_inv:
            continue
            
        amenities = full_inv.get("amenities", [])
        if isinstance(amenities, dict):
            labels = amenities.get("labels", [])
        elif isinstance(amenities, list):
            labels = amenities
        else:
            labels = []
        
        # Deduplicate within the same investment just in case
        unique_labels = set(lbl.strip() for lbl in labels if lbl.strip())
        
        for label in unique_labels:
            c[label] += 1

    print(f"Found {len(c)} unique amenity tags. Updating CSV...")

    csv_path = Path(__file__).parent / "data" / "HasłaMarketingowe.csv"
    
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row["n"] = 0  # reset old counts
            rows.append(row)

    # Build case-insensitive map to existing labels
    # If multiple existing rows map to the same lowercase string, the first one wins.
    # We will update the FIRST matching row to avoid duplicating counts across "balkon" and "Balkon" rows if they exist.
    label_to_row_idx = {}
    for i, row in enumerate(rows):
        lbl_low = row["HMLabel"].strip().lower()
        if lbl_low not in label_to_row_idx:
            label_to_row_idx[lbl_low] = i

    for label, count in c.items():
        lbl_low = label.lower()
        if lbl_low in label_to_row_idx:
            idx_row = label_to_row_idx[lbl_low]
            rows[idx_row]["n"] = int(rows[idx_row].get("n") or 0) + count
        else:
            new_row = {f: "" for f in fieldnames}
            new_row["HMLabel"] = label
            new_row["n"] = count
            rows.append(new_row)
            # Add to index so if we process duplicates somehow, they merge
            label_to_row_idx[lbl_low] = len(rows) - 1

    # Sort rows descending by 'n'
    rows.sort(key=lambda x: int(x["n"] if x["n"] else 0), reverse=True)

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print("Done updating HasłaMarketingowe.csv")

if __name__ == "__main__":
    update_amenities_freq()
