
import json
import logging
from python_worker.services.investment_sync import InvestmentSyncService
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("verify_script")

def verify_investments():
    system_ids = [
        "INV-29838", "INV-30594", "INV-30599", "INV-31163", "INV-31164", 
        "INV-31600", "INV-32287", "INV-32529", "INV-32531", "INV-33097", 
        "INV-33135", "INV-33157", "INV-35379", "INV-35824", "INV-36198"
    ]
    
    identity_resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)
    sync_service = InvestmentSyncService(identity_resolver, USI_DATA_DIR, PUBLIC_USI_DIR)

    for sid in system_ids:
        # Check source from file (need to resolve file path first or just try both)
        # Assuming portal is OTO (most)
        portal = "oto" 
        item_id = sid.split('_')[-1] # This might not be right for INV IDs
        
        # Need to find actual portal ID for the INV ID
        # A simpler way: use InvestmentIdentityResolver
        res = identity_resolver.get_investment_resources(sid)
        if not res:
            logger.info(f"{sid}: Nie znaleziono zasobów")
            continue
            
        # Try to find portal and id in sources
        try:
            with open(res['files']['anchor'], 'r') as f:
                data = json.load(f)
                sources = data.get('sources', {})
                for p, sdata in sources.items():
                    pid = sdata.get('id')
                    if pid:
                        is_active = sync_service._check_investment_exists(p, pid)
                        logger.info(f"{sid} ({p}): {'Aktywna' if is_active else 'Nieaktywna'}")
        except:
            logger.info(f"{sid}: Błąd odczytu")

if __name__ == "__main__":
    verify_investments()
