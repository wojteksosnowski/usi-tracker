# python_worker/rebuild_devs_id_only.py

import json
import logging
import os
import re
import sys
from pathlib import Path
from datetime import datetime

# Ścieżka bazowa i konfiguracja sys.path dla bibliotek zewnętrznych
_BASE_DIR = Path(__file__).resolve().parent.parent
LIB_PATH = str(_BASE_DIR.parent / "usi-scrapers")
if os.path.exists(LIB_PATH) and LIB_PATH not in sys.path:
    sys.path.insert(0, LIB_PATH)

# Autorytatywna brama systemowa
try:
    from python_worker.config import get_shared_scraper_gateway
    HAS_GATEWAY = True
except ImportError:
    HAS_GATEWAY = False

# Konfiguracja logowania
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("rebuild_devs_id_only")

class DevIdOnlyRebuilder:
    def __init__(self, dev_dir: Path, counters_path: Path):
        self.dev_dir = Path(dev_dir)
        self.counters_path = Path(counters_path)
        if not self.dev_dir.exists():
            raise FileNotFoundError(f"Katalog USIdev nie istnieje: {dev_dir}")
        if not HAS_GATEWAY:
            raise RuntimeError("Krytyczny brak bramy ScraperGateway. Rebuild przerwany.")
        self.gateway = get_shared_scraper_gateway()

    def _generate_usi_dev_id(self) -> str:
        """Atomowo inkrementuje i pobiera ID z usi_counters.json."""
        if not self.counters_path.exists():
            self.counters_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.counters_path, "w", encoding="utf-8") as f:
                json.dump({"dev": 1, "inv": 1, "dm": 1}, f)

        with open(self.counters_path, "r+", encoding="utf-8") as f:
            counters = json.load(f)
            counters["dev"] = counters.get("dev", 0) + 1
            next_id = counters["dev"]
            f.seek(0)
            json.dump(counters, f, indent=2)
            f.truncate()
            return f"DEV-{next_id:04d}"

    def purge_and_rebuild(self, apply: bool = False):
        """Bezlitosne czyszczenie i rekonstrukcja 1:1 z Portal ID."""
        logger.info(f"Rozpoczynanie operacji ID-Only w: {self.dev_dir}")
        if not apply:
            logger.warning("TRYB DRY-RUN. Brak zmian na dysku.")

        all_raw_files = []
        # Mapa do śledzenia już przetworzonych ID w tej sesji: {(portal, portal_id): usi_dev_id}
        processed_identities = {}

        for root, _, files in os.walk(self.dev_dir):
            current_dir = Path(root)
            if current_dir.name == "raw" and current_dir.parent == self.dev_dir:
                continue

            for file in files:
                file_path = current_dir / file
                
                # RYGORYSTYCZNY REGEX: Tylko pliki główne, ignorujemy archiwa z timestampem
                # Format: raw_{portal}_{portal_id}.json
                if re.match(r"^raw_(rp|oto|to)_([a-zA-Z0-9]+)\.json$", file):
                    all_raw_files.append(file_path)
                    continue
                
                # Usuwamy tylko pliki wygenerowane (usi_dev_*.json, dev_master_*.json, _index.json)
                if file.startswith(("usi_dev_", "dev_master_", "_index", "_dev_")):
                    if apply:
                        file_path.unlink()
                        logger.info(f"Usunięto śmieci: {file}")
                    else:
                        logger.info(f"[DRY-RUN] Do usunięcia: {file}")

        logger.info(f"Znaleziono {len(all_raw_files)} autentycznych plików RAW (zignorowano archiwa).")

        for raw_path in all_raw_files:
            dev_slug = raw_path.parent.name
            if raw_path.parent == self.dev_dir: continue

            try:
                raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Błąd odczytu {raw_path.name}: {e}")
                continue

            # Ponowna walidacja portalu i ID
            match = re.match(r"raw_(rp|oto|to)_([a-zA-Z0-9]+)\.json", raw_path.name)
            if not match: continue
            
            portal = match.group(1)
            filename_portal_id = match.group(2)
            
            # --- UŻYCIE BRAMY SYSTEMOWEJ ---
            try:
                mapping = self.gateway.get_mapping(portal)
                dev_mapping = mapping.get("developer", {})
                portal_id = str(self.gateway.resolve_path(raw_data, dev_mapping.get("id")) or filename_portal_id)
                dev_name = self.gateway.resolve_path(raw_data, dev_mapping.get("name"))
                if not dev_name: dev_name = raw_data.get("name") or dev_slug.replace("-", " ").title()
            except Exception as api_err:
                logger.error(f"Błąd Bramy dla {raw_path.name}: {api_err}")
                portal_id = filename_portal_id
                dev_name = raw_data.get("name") or dev_slug.replace("-", " ").title()

            # DE-DUPLIKACJA: Sprawdzamy czy to ID portalu już zostało obsłużone
            identity_key = (portal, portal_id)
            if identity_key in processed_identities:
                logger.warning(f"ID {portal_id} ({portal}) już istnieje jako {processed_identities[identity_key]}. Pomijam duplikat RAW.")
                continue

            usi_dev_id = self._generate_usi_dev_id() if apply else "DEV-XXXXX"
            processed_identities[identity_key] = usi_dev_id
            
            # Budowa czystego rekordu Level 2
            portal_mapping = {"rp": None, "oto": None, "to": None}
            if portal == "rp":
                portal_mapping["rp"] = {"id": str(portal_id), "slug": dev_slug}
            elif portal == "oto":
                portal_mapping["oto"] = {"agency_id": str(portal_id), "agency_ids": [str(portal_id)]}
            elif portal == "to":
                portal_mapping["to"] = {"agency_id": str(portal_id)}

            rebuilt_record = {
                "developer_slug": dev_slug,
                "name": dev_name,
                "usi_dev_id": usi_dev_id,
                "portal_mapping": portal_mapping,
                "audit": {
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            }

            output_filename = f"usi_dev_{portal}_{portal_id}.json"
            output_path = raw_path.parent / output_filename

            if apply:
                output_path.write_text(json.dumps(rebuilt_record, indent=2, ensure_ascii=False), encoding="utf-8")
                logger.info(f"Utworzono: {dev_slug}/{output_filename} (USI ID: {usi_dev_id})")
            else:
                logger.info(f"[DRY-RUN] Powstanie: {dev_slug}/{output_filename} z USI ID: {usi_dev_id}")

        logger.info("Rekonstrukcja ID-Only zakończona.")

if __name__ == "__main__":
    import argparse
    base_dir = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser()
    parser.add_argument("--dev-dir", type=str, default=str(base_dir / "Public" / "USIdev"))
    parser.add_argument("--counters", type=str, default=str(base_dir / "python_worker" / "data" / "usi_counters.json"))
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rebuilder = DevIdOnlyRebuilder(Path(args.dev_dir), Path(args.counters))
    rebuilder.purge_and_rebuild(apply=args.apply)
