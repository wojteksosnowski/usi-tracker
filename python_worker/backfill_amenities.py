import sys
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed

from python_worker.services.investment_service import InvestmentService
from python_worker.investment_index import InvestmentIndex
from python_worker.config import USI_DATA_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

def _process_single(system_id: str) -> bool:
    try:
        svc = InvestmentService()
        # Wykorzystujemy wbudowaną funkcję, która zaczytuje TYLKO lokalne pliki raw_*.json
        # i przepuszcza je przez zaktualizowany mechanizm usi_scrapers,
        # a na koniec bezpiecznie i atomowo zapisuje usi_*.json przez tempfile (wymóg architektoniczny).
        return svc.update_investment(
            system_id, 
            use_local_raw=True, 
            skip_images=True, 
            skip_index=True, 
            skip_log=True
        )
    except Exception as e:
        logger.error(f"Failed {system_id}: {e}")
        return False

def main():
    logger.info("Ładowanie indeksu inwestycji...")
    idx = InvestmentIndex(USI_DATA_DIR)
    all_investments = [e.get("usi_inv_id") for e in idx.get_all() if e.get("usi_inv_id")]
    
    total = len(all_investments)
    logger.info(f"Rozpoczynam zrównoleglony backfill dla {total} rekordów...")
    
    built = 0
    failed = 0
    
    # Używamy ThreadPoolExecutor, aby respektować wbudowane w kodzie blokady wątków (threading.Lock). 
    # ProcessPoolExecutor powodował błędy uszkodzenia pliku _index.json, ponieważ zamki nie działały między procesami.
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_process_single, sys_id): sys_id for sys_id in all_investments}
        
        for i, future in enumerate(as_completed(futures), 1):
            if future.result():
                built += 1
            else:
                failed += 1
                
            if i % 250 == 0 or i == total:
                logger.info(f"Postęp: {i}/{total} ({built} zaktualizowanych, {failed} błędów)")
                
    logger.info(f"Backfill zakończony: {built} sukcesów, {failed} błędów. Uruchom 'python3 -m python_worker.main rebuild-index' aby zaktualizować indeks if needed.")

if __name__ == "__main__":
    main()
