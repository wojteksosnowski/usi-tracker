import json
import logging
from pathlib import Path
from datetime import datetime

from python_worker.config import get_shared_config, get_shared_fetcher, get_shared_scraper_gateway
from python_worker.developer_manager import DeveloperManager
from python_worker.api.utils import now_utc, to_iso

logger = logging.getLogger(__name__)

class DeveloperService:
    def __init__(self, data_dir: Path, dev_dir: Path, scraper_gateway=None):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self.dm = DeveloperManager(data_dir, dev_dir)
        self.gateway = scraper_gateway or get_shared_scraper_gateway()

    def download_dev_profile_raw(self, portal: str, identifier: str, dev_slug: str) -> Path | None:
        """
        Pobiera surowy profil dewelopera oraz jego logo delegując zadanie do usi-scrapers przez bramę.
        Zgodnie z ID-only identyfikacja opiera się wyłącznie o portal_id.
        """
        try:
            portal_prefix = self.gateway.resolve_prefix(portal)
            
            # Wywołanie przez bramę
            res = self.gateway.download_raw_dev(portal_prefix, str(identifier))
            if not res or res.get("status") != "success":
                msg = res.get("message", "Unknown error") if res else "No response"
                logger.error(f"usi-scrapers failed to download dev profile for {portal_prefix}/{identifier}: {msg}")
                return None

            # Zwrócenie ścieżki do pliku zweryfikowanej zgodnie z CANONICAL.md
            resolved_slug = res.get("dev_slug") or dev_slug
            target_path = self.dev_dir / resolved_slug / f"raw_{portal_prefix}_{identifier}.json"
            
            if target_path.exists():
                return target_path
            return None
            
        except Exception as e:
            logger.error(f"Failed to download developer profile for {portal}/{dev_slug}: {e}")
            return None

    def update_developer_profile(self, usi_dev_id: str) -> bool:
        """
        Odświeża surowe zrzuty profili ze wszystkich zmapowanych portali i przebudowuje Level 2.
        """
        dev_data = self.dm.get_developer_by_id(usi_dev_id)
        if not dev_data:
            logger.warning(f"Developer metadata not found for {usi_dev_id}, cannot update.")
            return False

        dev_slug = dev_data.get("developer_slug")
        mapping = dev_data.get("portal_mapping", {})
        updated = False

        # Odświeżanie zmapowanych portali
        for portal in ("rp", "oto", "to"):
            if p_map := mapping.get(portal):
                if pid := p_map.get("id") or p_map.get("agency_id"):
                    logger.info(f"Updating {portal} profile for {dev_slug} (ID: {pid})")
                    if self.download_dev_profile_raw(portal, str(pid), dev_slug):
                        updated = True

        # Kompilacja warstwy Level 2 (usi_dev_*.json) na bazie nowych plików raw
        if updated:
            from python_worker.init_developers import _build_dev_from_raws
            dev_subdir = self.dev_dir / dev_slug
            if dev_subdir.exists():
                _build_dev_from_raws(dev_subdir, dev_slug, dev_data.get("name"), self.dm)
            
        return updated

    def get_maintenance_overdue_score(self, dev_data: dict) -> float:
        """
        Wylicza priorytet konserwacji opierając się ściśle o wzorce nazw z CANONICAL.md.
        """
        score = 0.0
        now = now_utc()
        
        if not dev_data.get("logo"):
            score += 1000.0
            
        pm = dev_data.get("portal_mapping", {})
        dev_slug = dev_data.get("developer_slug")
        dev_subdir = self.dev_dir / dev_slug
        
        for portal in ("rp", "oto", "to"):
            if portal_info := pm.get(portal):
                # Ekstrakcja portal_id zamiast używania deweloperskiego sluga w nazwie pliku
                portal_id = portal_info.get("id") or portal_info.get("agency_id")
                if portal_id:
                    raw_file = dev_subdir / f"raw_{portal}_{portal_id}.json"
                    if not raw_file.exists():
                        score += 500.0
        
        last_maint_str = dev_data.get("last_maintenance")
        if not last_maint_str:
            score += 100.0
        else:
            try:
                last_maint = datetime.fromisoformat(last_maint_str.replace("Z", "+00:00"))
                overdue_days = (now - last_maint).days
                if overdue_days > 90:
                    score += overdue_days
            except ValueError:
                score += 100.0
                
        return score

    def record_maintenance(self, dev_slug: str, success: bool):
        """Zapisuje ślad rewizyjny konserwacji dewelopera na dysku."""
        dev_file = None
        subdir = self.dev_dir / dev_slug
        if subdir.is_dir():
            hits = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if hits:
                dev_file = hits[0]
        
        if not dev_file:
            return

        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            data["last_maintenance"] = to_iso(now_utc())
            data["maintenance_success"] = success
            self.dm.create_developer_file(data)
            
            from python_worker.logger_utils import log_to_dev_log
            status = "sukces" if success else "błąd"
            log_to_dev_log(dev_slug, f"Konserwacja danych zakończona ({status}).")
        except Exception as e:
            logger.error(f"record_maintenance({dev_slug}) failed: {e}")
