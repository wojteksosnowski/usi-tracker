
import os
import json
from pathlib import Path

USI_DATA_DIR = "Public/USIdata"

def detect():
    dual_records = []
    total_checked = 0

    for root, dirs, files in os.walk(USI_DATA_DIR):
        for file in files:
            if file.startswith("usi_") and file.endswith(".json"):
                total_checked += 1
                path = Path(root) / file
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        
                    sources = data.get("sources", {})
                    # Sprawdzamy czy ma oba kluczowe źródła
                    has_rp = "rp" in sources
                    has_oto = "otodom" in sources
                    
                    if has_rp and has_oto:
                        dual_records.append({
                            "path": str(path),
                            "name": data.get("name"),
                            "rp_slug": sources["rp"].get("id"),
                            "oto_slug": sources["otodom"].get("id")
                        })
                except Exception as e:
                    print(f"Error reading {path}: {e}")

    print(f"\n--- RAPORT DETEKCJI REKORDÓW DUALNYCH ---")
    print(f"Przeskanowano: {total_checked} plików")
    print(f"Znaleziono rekordów RP+OTO: {len(dual_records)}")
    
    if dual_records:
        print("\nPrzykłady (pierwsze 10):")
        for rec in dual_records[:10]:
            print(f"- {rec['name']} | RP: {rec['rp_slug']} | OTO: {rec['oto_slug']}")
            print(f"  Path: {rec['path']}")

if __name__ == "__main__":
    detect()
