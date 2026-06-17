import json
import logging
from pathlib import Path
from tqdm import tqdm
from python_worker.config import PUBLIC_USI_DIR
from python_worker.services.investment_sync import _enrich_rp_unified
from usi_scrapers.api import transform_to_unified

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

def main():
    base_dir = Path(PUBLIC_USI_DIR) / "USIdata"
    count = 0
    
    # Znajdz wszystkie raw_rp_*.json
    raw_files = list(base_dir.rglob("raw_rp_*.json"))
    
    for raw_path in tqdm(raw_files):
        # Pomijamy pliki archiwalne (zawierające znacznik czasu w nazwie jak raw_rp_123_2024.json)
        if "_" in raw_path.stem[7:]: # po 'raw_rp_'
            continue
            
        usi_path = raw_path.parent / raw_path.name.replace("raw_", "usi_")
        if not usi_path.exists():
            continue
            
        raw_data = json.loads(raw_path.read_text())
        unified = transform_to_unified('rp', raw_data, 'investment')
        
        # Test czy enrichment cos wyciagnie
        _enrich_rp_unified(unified)
        specs_enriched = unified.get("specifications", {})
        
        if "delivery_date" in specs_enriched:
            usi_data = json.loads(usi_path.read_text())
            usi_specs = usi_data.setdefault("specifications", {})
            
            # Jesli data jest inna niz obecnie lub brak, aktualizuj
            if usi_specs.get("delivery_date") != specs_enriched["delivery_date"]:
                usi_specs["delivery_date"] = specs_enriched["delivery_date"]
                usi_specs["delivery_quarter"] = specs_enriched["delivery_quarter"]
                usi_specs["delivery_year"] = specs_enriched["delivery_year"]
                
                usi_path.write_text(json.dumps(usi_data, indent=2, ensure_ascii=False))
                count += 1
                
    print(f"Zaktualizowano {count} inwestycji RP.")

if __name__ == "__main__":
    main()
