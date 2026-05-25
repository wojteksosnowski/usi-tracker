import json
from pathlib import Path

USI_DEV_DIR = Path("/Volumes/Samsam/Public/USIdev")

def clean_duplicates():
    for dev_file in USI_DEV_DIR.rglob("usi_dev_*.json"):
        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            if "suggestions" in data and isinstance(data["suggestions"], list):
                # Unique based on usi_dev_id
                seen = set()
                unique_suggestions = []
                for s in data["suggestions"]:
                    sid = s.get("usi_dev_id")
                    if sid not in seen:
                        seen.add(sid)
                        unique_suggestions.append(s)
                
                if len(unique_suggestions) != len(data["suggestions"]):
                    print(f"Cleaning {dev_file.name}: {len(data['suggestions'])} -> {len(unique_suggestions)}")
                    data["suggestions"] = unique_suggestions
                    dev_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Error processing {dev_file}: {e}")

if __name__ == "__main__":
    clean_duplicates()
