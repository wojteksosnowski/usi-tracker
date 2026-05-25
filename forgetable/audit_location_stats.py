import json
import logging
import sys
from pathlib import Path

# Add project root to path to allow imports from python_worker
sys.path.append(str(Path(__file__).resolve().parent.parent))

from python_worker.config import USI_DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def audit_location():
    index_path = USI_DATA_DIR / "_index.json"
    if not index_path.exists():
        logger.error(f"Plik indeksu nie istnieje: {index_path}")
        return

    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
        entries = data.get("entries", [])
    except Exception as e:
        logger.error(f"Błąd odczytu indeksu: {e}")
        return

    total = len(entries)
    if total == 0:
        print("Brak inwestycji w indeksie.")
        return

    valid = 0
    missing = 0
    zeros = 0
    
    for entry in entries:
        coords = entry.get("coords")
        if not coords:
            missing += 1
            continue
            
        # Coordinates can be [lat, lng]
        if len(coords) < 2:
            missing += 1
            continue
            
        lat, lng = coords[0], coords[1]
        if lat is None or lng is None:
            missing += 1
        elif lat == 0 and lng == 0:
            zeros += 1
        else:
            valid += 1

    print("\n--- RAPORT AUDYTU LOKALIZACJI ---")
    print(f"Suma inwestycji:        {total}")
    print(f"Poprawne współrzędne:   {valid} ({valid/total*100:.2f}%)")
    print(f"Brakujące (Null):       {missing} ({missing/total*100:.2f}%)")
    print(f"Błędne (0,0):           {zeros} ({zeros/total*100:.2f}%)")
    print("---------------------------------\n")

if __name__ == "__main__":
    audit_location()
