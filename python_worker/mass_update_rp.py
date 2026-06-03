import json
import logging
import sys
from pathlib import Path
from python_worker.config import USI_DATA_DIR
from python_worker.services.investment_service import InvestmentService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MassUpdate")

def run_mass_update():
    index_path = USI_DATA_DIR / "_index.json"
    if not index_path.exists():
        logger.error(f"Nie znaleziono pliku indeksu: {index_path}")
        sys.exit(1)

    with open(index_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    entries = data.get("entries", [])
    # Filtrujemy tylko inwestycje z RynekPierwotny, ponieważ to ich dotyczy problem parsera
    rp_entries = [e for e in entries if e.get("source") == "RP"]
    
    logger.info(f"Znaleziono {len(rp_entries)} inwestycji z portalu RP do aktualizacji.")
    
    service = InvestmentService()
    success_count = 0
    fail_count = 0
    
    for i, entry in enumerate(rp_entries, 1):
        system_id = entry.get("usi_inv_id")
        name = entry.get("name", "Nieznana")
        
        if not system_id:
            continue
            
        logger.info(f"[{i}/{len(rp_entries)}] Aktualizacja {system_id} ({name})...")
        
        try:
            # Flaga use_local_raw=True jest kluczowa - dzięki niej nie odpytujemy API,
            res = service.update_investment(system_id, use_local_raw=True, skip_images=True, skip_index=True, skip_log=True)
            if res:
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            logger.error(f"Błąd podczas aktualizacji {system_id}: {e}")
            fail_count += 1
            
    logger.info(f"\n--- PODSUMOWANIE ---")
    logger.info(f"Zakończono sukcesem: {success_count}")
    logger.info(f"Niepowodzenia: {fail_count}")
    
    logger.info("Rozpoczynam finalną, jednorazową przebudowę indeksu systemowego...")
    from python_worker.investment_index import rebuild
    from python_worker.config import PUBLIC_USI_DIR
    rebuild(USI_DATA_DIR, PUBLIC_USI_DIR)
    logger.info("Indeks przebudowany. Całość operacji zakończona!")

if __name__ == "__main__":
    logger.info("Rozpoczynam masową aktualizację (tylko lokalne przeliczanie parsera).")
    run_mass_update()
