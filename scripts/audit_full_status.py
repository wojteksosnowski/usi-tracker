#!/usr/bin/env python3
import json
import logging
import os
import sys
from pathlib import Path

# Upewnienie się, że python_worker jest w sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("audit_script")

def audit_investments():
    identity_resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)
    
    # Skanowanie całego drzewa danych w poszukiwaniu plików usi_*.json
    all_files = list(USI_DATA_DIR.glob("**/usi_*.json"))
    usi_files = [f for f in all_files if "usi_dev_" not in f.name]

    logger.info(f"Analiza {len(usi_files)} plików USI JSON...")
    
    results = []

    for file_path in usi_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        system_id = data.get("usi_inv_id")
        
        # Sprawdź czy ma wyciek (HTTP w image_paths)
        image_paths = data.get("image_paths", [])
        has_leak = any(str(p).startswith(("http://", "https://")) for p in image_paths)
        
        # Jeśli nie ma wycieku i ma ścieżki, to zakładamy że jest poprawne
        if not has_leak and image_paths:
            continue
            
        # Jeśli trafiliśmy tutaj, to inwestycja ma wyciek LUB jest pusta
        resources = identity_resolver.get_investment_resources(system_id)
        
        source = 'unknown'
        if '_rp_' in file_path.name: source = 'rp'
        elif '_oto_' in file_path.name: source = 'oto'
        elif '_to_' in file_path.name: source = 'to'

        # Sprawdź czy na dysku są obrazy
        has_local_images = False
        if resources and resources.get("images_dir") and resources["images_dir"].exists():
            if list(resources["images_dir"].iterdir()):
                has_local_images = True
        
        results.append({
            "system_id": system_id,
            "source": source,
            "has_leak": has_leak,
            "has_local_images": has_local_images,
            "file_path": str(file_path)
        })

    # Zapisz raport
    with open("audit_full_report.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Audyt zakończony. Raport zapisano w audit_full_report.json. Znaleziono {len(results)} spraw do weryfikacji.")

if __name__ == "__main__":
    audit_investments()
