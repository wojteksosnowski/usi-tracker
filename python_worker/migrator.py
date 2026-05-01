import csv
import json
import logging
import argparse
from pathlib import Path
from datetime import datetime

from .config import USI_DATA_DIR, DROPBOX_PATH
from .init_developers import import_developers_from_csv
from .adapters import RPAdapter, OtodomAdapter, Merger

logger = logging.getLogger("Migrator")
logging.basicConfig(level=logging.INFO)

def parse_stars(stars_str):
    """Maps ★ symbols to numbers."""
    if not stars_str: return None
    mapping = {
        "★": 1, "★★": 2, "★★★": 3, "★★★★": 4,
        "⓿¾": 0.75, "★¼": 1.25, "★½": 1.5, "★¾": 1.75,
        "★★¼": 2.25, "★★½": 2.5, "★★¾": 2.75,
        "★★★¼": 3.25, "★★★½": 3.5, "★★★¾": 3.75
    }
    return mapping.get(stars_str.strip())

def safe_float(val):
    if not val: return None
    try:
        return float(str(val).replace(',', '.'))
    except ValueError:
        return None

def migrate(csv_path: Path, data_dir: Path, limit=None):
    # 1. Init developers first
    logger.info("Step 1: Initializing developers from Konkurenci.csv...")
    konkurenci_path = csv_path.parent / "Konkurenci.csv"
    import_developers_from_csv(konkurenci_path, data_dir)

    # 1b. Build Developer Lookup Table
    dev_lookup = {}
    with open(konkurenci_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            d_name = row.get('Deweloper', '').strip()
            d_slug = row.get('usiFolder', '').strip()
            if d_name and d_slug:
                dev_lookup[d_name] = d_slug

    from python_worker.csv_importer import slugify

    # 2. Process USImaster.csv
    logger.info(f"Step 2: Migrating investments from {csv_path}...")
    count = 0
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if limit and count >= limit: break
            
            inv_slug = row.get('USIfolder', '').strip()
            if not inv_slug: continue

            dev_name = row.get('Deweloper', '').strip()
            dev_slug = dev_lookup.get(dev_name)
            if not dev_slug:
                dev_slug = slugify(dev_name) if dev_name else "unknown"
            
            inv_dir = data_dir / dev_slug / inv_slug
            inv_dir.mkdir(parents=True, exist_ok=True)

            # Phase 2: Raw Extraction
            rp_json_raw = row.get('rpJSON', '').strip()
            oto_json_raw = row.get('otoJSON', '').strip()
            
            rp_raw = None
            oto_raw = None
            
            if rp_json_raw:
                try:
                    rp_raw = json.loads(rp_json_raw)
                    with open(inv_dir / f"raw_rp_{inv_slug}_imported.json", "w", encoding="utf-8") as f_out:
                        json.dump(rp_raw, f_out, indent=2, ensure_ascii=False)
                except:
                    pass

            if oto_json_raw:
                try:
                    oto_raw = json.loads(oto_json_raw)
                    with open(inv_dir / f"raw_oto_{inv_slug}_imported.json", "w", encoding="utf-8") as f_out:
                        json.dump(oto_raw, f_out, indent=2, ensure_ascii=False)
                except:
                    pass

            # Ratings & Meta
            ratings = {
                "status": row.get("Ocena", "Brak"),
                "Gwiazdki": parse_stars(row.get("Gwiazdki")),
                "Balkony": safe_float(row.get("Balkony")),
                "Fasady": safe_float(row.get("Fasady")),
                "Wnętrza": safe_float(row.get("Wnętrza")),
                "Teren": safe_float(row.get("Teren")),
                "Mieszkania": safe_float(row.get("Mieszkania")),
                "Udogodnienia": safe_float(row.get("Udogodnienia")),
                "komentarz": row.get("komentarz", "").strip()
            }
            with open(inv_dir / f"meta_{inv_slug}_ratings.json", "w", encoding="utf-8") as f_out:
                json.dump(ratings, f_out, indent=2, ensure_ascii=False)

            # Phase 3: Unification
            rp_unified = RPAdapter.transform(rp_raw, inv_slug, dev_slug) if rp_raw else None
            oto_unified = OtodomAdapter.transform(oto_raw, inv_slug, dev_slug) if oto_raw else None
            
            unified = Merger.merge(rp_unified, oto_unified, ratings)
            
            if unified:
                with open(inv_dir / f"usi_{inv_slug}.json", "w", encoding="utf-8") as f_out:
                    json.dump(unified, f_out, indent=2, ensure_ascii=False)

            count += 1
            if count % 100 == 0:
                logger.info(f"Processed {count} investments...")

    logger.info(f"Migration completed. Total investments processed: {count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate data from USImaster.csv to new USI architecture")
    parser.add_argument("--limit", type=int, help="Limit number of investments to process")
    args = parser.parse_args()
    
    csv_path = Path("reference-data/coda/USImaster.csv")
    migrate(csv_path, USI_DATA_DIR, limit=args.limit)
