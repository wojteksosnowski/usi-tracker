import json
import shutil
import logging
from pathlib import Path
from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver
import python_worker.investment_index as inv_index

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("cleanup_script")

def cleanup_investments():
    system_ids = [
        "INV-29838", "INV-30594", "INV-30599", "INV-31163", "INV-31164", 
        "INV-31600", "INV-32287", "INV-32529", "INV-32531", "INV-33097", 
        "INV-33135", "INV-33157", "INV-35379", "INV-35824", "INV-36198"
    ]
    
    identity_resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)

    for sid in system_ids:
        resources = identity_resolver.get_investment_resources(sid)
        if not resources:
            logger.warning(f"{sid}: Nie znaleziono zasobów do usunięcia.")
            continue
        
        # 1. Usuń katalog inwestycji (zawiera plik .json)
        base_dir = resources["base_dir"]
        if base_dir.exists():
            logger.info(f"Usuwanie katalogu: {base_dir}")
            shutil.rmtree(base_dir)
        
        # 2. Usuń katalog obrazów (jeśli istnieje)
        images_dir = resources.get("images_dir")
        if images_dir and images_dir.exists():
            logger.info(f"Usuwanie katalogu obrazów: {images_dir}")
            shutil.rmtree(images_dir)
            
        # 3. Usuń z indeksu
        try:
            # Używamy standardowej metody usuwania z indeksu
            # Wymaga importu modułu indeksu
            from python_worker import investment_index
            investment_index.remove(USI_DATA_DIR, PUBLIC_USI_DIR, inv_id=sid)
            logger.info(f"Usunięto {sid} z indeksu.")
        except Exception as e:
            logger.error(f"Błąd przy usuwaniu {sid} z indeksu: {e}")

if __name__ == "__main__":
    cleanup_investments()
