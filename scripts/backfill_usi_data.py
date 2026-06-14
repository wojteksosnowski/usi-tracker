import os
import json
from pathlib import Path
import logging
import sys

# Dodajemy projekt do path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.config import get_shared_config
from python_worker.services.here_maps_service import HereMapsService
from python_worker.investment_index import get_investment_index
from usi_scrapers.mapping import transform_to_unified

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    config = get_shared_config()
    public_dir = Path(config.public_dir)
    data_dir = public_dir / "USIdata"
    from python_worker.config import HERE_API_KEY
    here_service = HereMapsService(api_key=HERE_API_KEY)

    logger.info(f"Rozpoczynamy szukanie w {data_dir}...")
    
    modified_count = 0

    for usi_file in data_dir.rglob("usi_*.json"):
        if not usi_file.is_file():
            continue
            
        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Nie mozna wczytac {usi_file}: {e}")
            continue

        loc_dict = data.get("location", {})
        coords = loc_dict.get("coords", [None, None])

        if not coords or coords[0] is None or coords[1] is None:
            logger.info(f"Brak coords w {usi_file.name}")
            
            lat, lng = None, None
            
            # Najpierw probujemy wczytac z raw_*.json
            inv_dir = usi_file.parent
            for raw_file in inv_dir.glob("raw_*.json"):
                portal_prefix = raw_file.name.split("_")[1]
                if portal_prefix.endswith(".json"):
                    portal_prefix = portal_prefix[:-5]
                
                try:
                    with open(raw_file, "r", encoding="utf-8") as f:
                        raw_data = json.load(f)
                        
                    m = transform_to_unified(portal_prefix, raw_data)
                    if m and m.get("latitude") and m.get("longitude"):
                        lat = m.get("latitude")
                        lng = m.get("longitude")
                        logger.info(f"  Odzyskano z raw_*.json ({portal_prefix}): {lat}, {lng}")
                        break
                except Exception as e:
                    logger.error(f"  Blad wczytywania {raw_file.name}: {e}")
            
            # Jesli nadal nie ma, to fallback na HereMaps
            if lat is None or lng is None:
                address = loc_dict.get("address", "") or ""
                city = loc_dict.get("city", "") or ""
                full_address = f"{address}, {city}".strip(", ")
                if full_address:
                    logger.info(f"  Probujemy geokodowania dla: {full_address}")
                    lat, lng = here_service.geocode_address(full_address)
                    if lat and lng:
                        logger.info(f"  Zgeokodowano pomyslnie: {lat}, {lng}")
                    else:
                        logger.info("  Geokodowanie nie powiodlo sie.")
            
            if lat is not None and lng is not None:
                loc_dict["coords"] = [lat, lng]
                data["location"] = loc_dict
                
                try:
                    with open(usi_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    modified_count += 1
                except Exception as e:
                    logger.error(f"Nie mozna zapisac {usi_file.name}: {e}")

    logger.info(f"Zaktualizowano plikow: {modified_count}")
    logger.info("Przebudowa indeksu...")
    idx = get_investment_index()
    idx.rebuild()
    logger.info("Koniec.")

if __name__ == "__main__":
    main()
