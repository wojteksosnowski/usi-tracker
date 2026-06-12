import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.investment_repository import InvestmentRepository
from python_worker.services.investment_loader import get_shared_loader
from python_worker.services.investment_editor import InvestmentEditorService
from python_worker.services.investment_identity import InvestmentIdentityResolver

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backfill")

def main():
    data_dir = Path(USI_DATA_DIR)
    public_usi_dir = Path(PUBLIC_USI_DIR)
    
    # Zamiast dzikiego rglob, pobierz encje zarządzane przez właściwe komponenty
    identity_resolver = InvestmentIdentityResolver(data_dir=data_dir, public_usi_dir=public_usi_dir)
    repo = InvestmentRepository(identity_resolver=identity_resolver, data_dir=data_dir)
    investment_ids = repo.get_all_system_ids() 
    
    loader = get_shared_loader(data_dir=data_dir, public_usi_dir=public_usi_dir)
    editor = InvestmentEditorService(identity_resolver=identity_resolver, data_dir=data_dir, public_usi_dir=public_usi_dir, investment_repo=repo)
    
    logger.info(f"Found {len(investment_ids)} investments to backfill.")
    
    success, errors = 0, 0
    
    for system_id in investment_ids:
        try:
            # Prawidłowe załadowanie przez ujednolicony loader
            inv_data = loader.load_investment(system_id=system_id)
            if not inv_data:
                logger.warning(f"Could not load data for {system_id}")
                errors += 1
                continue
                
            # Zamiast ręcznego zapisu pliku, użyj serwisu edytorskiego
            changed = editor.update_computed_fields(system_id, inv_data)
            if changed:
                success += 1
        except Exception as e:
            logger.error(f"Error processing {system_id}: {e}")
            errors += 1
            
    logger.info(f"Backfill complete. Updated: {success}, Errors: {errors}")

if __name__ == "__main__":
    main()
