#!/usr/bin/env python3
import json
import logging
import os
import sys
from pathlib import Path

# Upewnienie się, że python_worker jest w sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR, get_shared_config
from python_worker.services.investment_identity import InvestmentIdentityResolver
import python_worker.investment_index as inv_index

# Konfiguracja rygorystycznego logowania na konsolę
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("repair_script")


# Configuration
DRY_RUN = False

def repair_investments():
    identity_resolver = InvestmentIdentityResolver(USI_DATA_DIR, PUBLIC_USI_DIR)
    
    # Próba importu funkcji oczyszczającej nazwy z biblioteki zewnętrznej
    try:
        from usi_scrapers.utils.images import clean_filename
    except ImportError:
        logger.critical("Brak dostępu do usi_scrapers.utils.images. clean_filename. Skrypt przerwany.")
        return

    # Skanowanie całego drzewa danych w poszukiwaniu plików usi_*.json
    all_files = list(USI_DATA_DIR.glob("**/usi_*.json"))
    usi_files = [f for f in all_files if "usi_dev_" not in f.name]

    logger.info(f"Rozpoczęto analizę repozytorium. Znaleziono {len(usi_files)} plików USI JSON.")
    
    repaired_count = 0
    skipped_count = 0

    for file_path in usi_files:
        if not file_path.exists():
             logger.warning(f"Plik {file_path} nie istnieje. Pomijanie.")
             continue
        
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.error(f"Nie można odczytać pliku {file_path}: {e}")
            continue

        system_id = data.get("usi_inv_id")
        if not system_id:
            # Próba rekonstrukcji system_id, jeśli pole jest puste
            system_id = file_path.stem.replace("usi_", "")

        resources = identity_resolver.get_investment_resources(system_id)
        if not resources:
            logger.warning(f"[{system_id}] Brak zasobów (resources) w systemie. Pomijanie.")
            continue

        image_paths = data.get("image_paths", [])
        all_urls = data.get("image_urls", [])

        # Sprawdzenie, czy w image_paths znajduje się jakikolwiek ślad wycieku URL HTTP
        has_leak = any(str(p).startswith(("http://", "https://")) for p in image_paths)
        
        # Jeśli pole image_paths jest puste, a mamy URL-e, również traktujemy to jako przypadek do naprawy
        if not has_leak and image_paths:
            skipped_count += 1
            continue

        logger.info(f"[{system_id}] Wykryto skażone dane lub brak ścieżek. Rozpoczynanie naprawy...")
        
        target_image_dir = resources.get("images_dir")
        if not target_image_dir or not target_image_dir.exists():
            logger.warning(f"[{system_id}] Katalog obrazów {target_image_dir} nie istnieje na dysku. Ścieżki zostaną wyczyszczone.")
            data["image_paths"] = []
            data["images_count"] = 0
            # Zapisujemy wyczyszczony stan, by usunąć błędne URL-e z bazy
            _save_and_index(file_path, system_id, data)
            repaired_count += 1
            continue

        # Klonowanie logiki z ImageSyncService.sync_investment_images
        try:
            url_to_basename = {url: os.path.splitext(clean_filename(url))[0] for url in all_urls}
            basename_to_urls = {}
            for url, bname in url_to_basename.items():
                basename_to_urls.setdefault(bname, []).append(url)
                
            expected_set = set(basename_to_urls.keys())
            found_paths = {}

            # Przeszukaj fizyczny katalog na dysku
            for file_name in os.listdir(target_image_dir):
                bname = os.path.splitext(file_name)[0]
                if bname in expected_set:
                    rel_path = os.path.relpath(target_image_dir / file_name, PUBLIC_USI_DIR)
                    path_str = f"/Public/USI/{rel_path}"
                    for url in basename_to_urls[bname]:
                        found_paths[url] = path_str
                    # Nie usuwamy z expected_set, aby obsłużyć duplikaty nazw z różnych URL-i

            unique_paths = []
            for url in all_urls:
                if url in found_paths:
                    p = found_paths[url]
                    if p not in unique_paths:
                        unique_paths.append(p)

            # Aktualizacja struktury danych
            data["image_paths"] = unique_paths
            data["images_count"] = len(unique_paths)

            # Przeliczenie widocznych zdjęć przez resolve_images (oczyszczenie pola photos)
            from python_worker.services.image_resolver import resolve_images
            data["photos"] = resolve_images(data, resources["base_dir"], PUBLIC_USI_DIR, resources, fast_index=False)
            
            # Zapis pliku i aktualizacja indeksów
            _save_and_index(file_path, system_id, data)
            logger.info(f"[{system_id}] Sukces. Przywrócono {len(unique_paths)} lokalnych ścieżek z {len(all_urls)} URL-i.")
            repaired_count += 1

        except Exception as ex:
            logger.error(f"[{system_id}] Błąd podczas rekonstrukcji ścieżek: {ex}", exc_info=True)

    logger.info(f"KONIEC PRACY. Naprawiono plików: {repaired_count}, Zweryfikowano jako poprawne/pominięto: {skipped_count}")


def _save_and_index(file_path: Path, system_id: str, data: dict):
    """Zapisuje poprawiony plik JSON i wymusza aktualizację indeksu."""
    if DRY_RUN:
        logger.info(f"[DRY RUN] Zapisano dane dla {system_id}")
        return

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    try:
        inv_index.upsert(USI_DATA_DIR, PUBLIC_USI_DIR, inv_id=system_id)
    except Exception as ie:
        logger.debug(f"Pominięto upsert indeksu dla {system_id}: {ie}")


if __name__ == "__main__":
    repair_investments()
