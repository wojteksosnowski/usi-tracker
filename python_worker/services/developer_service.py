import json
import logging
from pathlib import Path
from datetime import datetime, timezone

from python_worker.config import get_scraper_config
from python_worker.developer_manager import DeveloperManager
from python_worker.adapters import PORTAL_MAPPING
from usi_scrapers import resolve_path

logger = logging.getLogger(__name__)

def _now_utc() -> datetime:
    return datetime.now(tz=timezone.utc)

def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

class DeveloperService:
    def __init__(self, data_dir: Path, dev_dir: Path):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self.dm = DeveloperManager(data_dir, dev_dir)
        
        # Scraper library setup
        self.lib_config = get_scraper_config()
        self.lib_fetcher = None
        if self.lib_config:
            from usi_scrapers.fetcher import Fetcher
            self.lib_fetcher = Fetcher(self.lib_config)

    def download_dev_profile_raw(self, portal: str, identifier: str, dev_slug: str) -> Path | None:
        """Downloads raw developer profile and its logo via usi-scrapers."""
        if not self.lib_config or not self.lib_fetcher:
            logger.error("Scraper library not properly configured.")
            return None

        from usi_scrapers import api as scraper_api
        try:
            # 1. Download raw profile JSON
            target_dir = self.dev_dir / dev_slug
            raw_slug = scraper_api.download_raw_dev(self.lib_config, self.lib_fetcher, portal, identifier, target_dir)
            if not raw_slug:
                return None
            
            raw_path = target_dir / f"raw_{portal}_{identifier}.json"
            if not raw_path.exists():
                # Fallback to look for the file if identifier is a URL etc
                files = list(target_dir.glob(f"raw_{portal}_*.json"))
                if not files:
                    return None
                raw_path = files[-1]

            # 2. Extract logo URL from raw and download it
            raw_data = json.loads(raw_path.read_text(encoding="utf-8"))
            logo_path = PORTAL_MAPPING.get(portal, {}).get("developer", {}).get("logo")
            logo_url = resolve_path(raw_data, logo_path)

                from usi_scrapers.utils.images import download_developer_logo
                logger.info(f"Downloading logo for {dev_slug} from {logo_url}")
                portal_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")
                portal_id = str(identifier).split("/")[-1].split("?")[0].strip("-ID")
                download_developer_logo(logo_url, target_dir, portal_prefix, portal_id=portal_id)

            return raw_path
        except Exception as e:
            logger.error(f"Failed to download developer profile for {portal}/{dev_slug}: {e}")
            return None

    def update_developer_profile(self, dev_slug: str) -> bool:
        """
        Refreshes raw developer profile JSONs from all configured portals and rebuilds metadata.
        """
        dev_data = self.dm.get_developer(dev_slug)
        if not dev_data:
            logger.warning(f"Developer metadata not found for {dev_slug}, cannot update.")
            return False

        mapping = dev_data.get("portal_mapping", {})
        updated = False

        # RynekPierwotny
        rp_map = mapping.get("rp") or {}
        rp_id = rp_map.get("id") or rp_map.get("slug")
        if rp_id:
            logger.info(f"Updating RP profile for {dev_slug} (ID: {rp_id})")
            if self.download_dev_profile_raw("rp", rp_id, dev_slug):
                updated = True

        # Otodom
        oto_map = mapping.get("oto") or {}
        oto_url = oto_map.get("url")
        if oto_url:
            logger.info(f"Updating Otodom profile for {dev_slug} (URL: {oto_url})")
            if self.download_dev_profile_raw("oto", oto_url, dev_slug):
                updated = True

        # TabelaOfert
        to_map = mapping.get("to") or {}
        to_slug = to_map.get("slug")
        if to_slug:
            to_id = to_map.get("id") or to_slug
            logger.info(f"Updating TO profile for {dev_slug} (ID/Slug: {to_id})")
            if self.download_dev_profile_raw("to", to_id, dev_slug):
                updated = True

        # After downloading raws, rebuild Level 2 usi_dev_*.json
        from python_worker.init_developers import _build_dev_from_raws
        dev_subdir = self.dev_dir / dev_slug
        if dev_subdir.exists():
            _build_dev_from_raws(dev_subdir, dev_slug, dev_data.get("name"), self.dm)
            
        return updated

    def get_maintenance_overdue_score(self, dev_data: dict) -> float:
        """
        Returns a priority score for maintenance.
        Higher score = higher priority.
        """
        score = 0.0
        now = _now_utc()
        
        # 1. Missing logo? High priority.
        if not dev_data.get("logo"):
            score += 1000.0
            
        # 2. Missing raw files for defined portals?
        pm = dev_data.get("portal_mapping", {})
        dev_slug = dev_data.get("developer_slug")
        dev_subdir = self.dev_dir / dev_slug
        
        for portal in ("rp", "oto", "to"):
            if pm.get(portal):
                raw_file = dev_subdir / f"raw_{portal}_{dev_slug}.json"
                # For TO, it might be raw_to_{id}.json
                if portal == "to" and pm["to"].get("id"):
                    raw_file = dev_subdir / f"raw_to_{pm['to']['id']}.json"
                
                if not raw_file.exists():
                    score += 500.0
        
        # 3. Time-based overdue
        crawler = dev_data.get("crawler", {})
        last_maint_str = crawler.get("last_maintenance")
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
        """Updates the 'crawler' section in developer file after maintenance."""
        dev_file = None
        # Find file
        subdir = self.dev_dir / dev_slug
        if subdir.is_dir():
            hits = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if hits:
                dev_file = hits[0]
        
        if not dev_file:
            return

        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            crawler = data.setdefault("crawler", {})
            crawler["last_maintenance"] = _iso(_now_utc())
            crawler["maintenance_success"] = success
            data["crawler"] = crawler
            self.dm.create_developer_file(data)
            
            from python_worker.logger_utils import log_to_dev_log
            status = "sukces" if success else "błąd"
            log_to_dev_log(dev_slug, f"Wędrowiec — konserwacja zakończona ({status}).")
        except Exception as e:
            logger.error(f"record_maintenance({dev_slug}) failed: {e}")
