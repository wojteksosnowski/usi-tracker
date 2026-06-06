import json
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_identity import InvestmentIdentityResolver

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("sync_script")

def check_and_sync():
    with open("audit_full_report.json", "r", encoding="utf-8") as f:
        affected = json.load(f)

    identity_resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)
    sync_service = InvestmentSyncService(identity_resolver, USI_DATA_DIR, PUBLIC_USI_DIR)

    for item in affected:
        system_id = item["system_id"]
        source = item["source"]
        
        logger.info(f"Processing {system_id} ({source})...")
        
        # 1. Weryfikacja dla OTO/TO
        if source in ["oto", "to"]:
            # Sprawdzenie aktywności (używamy wbudowanego w sync_service)
            if not sync_service._check_investment_exists(source, system_id.split('_')[-1]):
                logger.warning(f"Inwestycja {system_id} nieaktywna na portalu. Pomijanie.")
                continue

        # 2. Synchronizacja (pobieranie obrazów + aktualizacja JSON)
        try:
            # Używamy update_investment, które wewnątrz wywołuje image_sync
            success = sync_service.update_investment(system_id, use_local_raw=False, skip_images=False)
            if success:
                logger.info(f"Pomyślnie zsynchronizowano {system_id}.")
            else:
                logger.error(f"Nie udało się zsynchronizować {system_id}.")
        except Exception as e:
            logger.error(f"Błąd podczas synchronizacji {system_id}: {e}")

if __name__ == "__main__":
    check_and_sync()
