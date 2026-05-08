import json
import logging
from pathlib import Path
from datetime import datetime

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class InvestmentService:
    def __init__(self, data_dir: Path = None, public_usi_dir: Path = None):
        from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR, get_scraper_config
        from usi_scrapers.manager import TechnicalDataManager
        
        self.data_dir = data_dir or Path(USI_DATA_DIR)
        self.public_usi_dir = public_usi_dir or Path(PUBLIC_USI_DIR)
        
        # Initialize library-based technical manager
        self.lib_config = get_scraper_config()
        if self.lib_config:
            from usi_scrapers.fetcher import Fetcher
            from usi_scrapers.manager import TechnicalDataManager
            self.fetcher = Fetcher(self.lib_config)
            self.tech_manager = TechnicalDataManager(self.lib_config)
        else:
            self.fetcher = None
            self.tech_manager = None

    def get_investment(self, dev_slug, inv_slug):
        from python_worker.api.utils import _load_investment
        return _load_investment(dev_slug, inv_slug, data_dir=self.data_dir, public_usi_dir=self.public_usi_dir)

    def register_investment(self, portal, developer_name, inv_slug, name, item_id=None, url=None):
        from python_worker.csv_importer import slugify
        from python_worker.developer_manager import DeveloperManager
        from usi_scrapers import api as scraper_api

        # Identification pre-scrapes (Otodom/TabelaOfert) via API
        if (not developer_name or slugify(developer_name) == "nieznany-deweloper") and portal in ("oto", "to") and url:
            logger.info(f"Developer unknown for {url}, performing pre-scrape identification ({portal})...")
            try:
                identified_name = scraper_api.identify_developer(self.fetcher, portal, url)
                if identified_name:
                    developer_name = identified_name
            except Exception as e:
                logger.error(f"Pre-scrape identification failed ({portal}): {e}")

        if not developer_name or slugify(developer_name) == "nieznany-deweloper":
            logger.error(f"Attempted to register investment with missing or invalid developer: {developer_name}")
            raise ValueError("Registration failed: Real developer identity is required. Cannot use 'Nieznany Deweloper'.")

        dev_slug = slugify(developer_name)
        dm = DeveloperManager(self.data_dir)
        
        # Auto-create developer profile if it doesn't exist (semantic layer)
        dev_path = dm.dev_dir / f"usi_dev_{dev_slug}.json"
        if not dev_path.exists():
            logger.info(f"Auto-creating developer profile for: {developer_name} ({dev_slug})")
            dm.create_developer_file({"developer_slug": dev_slug, "name": developer_name})

        # Path resolution via library
        usi_path = self.tech_manager.get_usi_json_path(dev_slug, inv_slug) if self.tech_manager else \
                   (self.data_dir / dev_slug / inv_slug / f"usi_{inv_slug}.json")

        if usi_path.exists():
            raise ValueError("Investment already exists")

        usi_path.parent.mkdir(parents=True, exist_ok=True)

        sources = {}
        if portal == "rp":
            sources["rp"] = {"id": item_id, "url": url}
        elif portal == "oto":
            sources["oto"] = {"url": url}
        elif portal == "to":
            sources["to"] = {"url": url}

        # Use DeveloperManager for consistent ID generation
        usi_inv_id = dm.generate_usi_id("INV")
        
        skeleton = {
            "investment_slug": inv_slug,
            "developer_slug": dev_slug,
            "name": name,
            "sources": sources,
            "status": "Brak",
            "usi_inv_id": usi_inv_id,
            "audit": {"created_at": datetime.now().isoformat()}
        }

        with open(usi_path, "w", encoding="utf-8") as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)

        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        return dev_slug, inv_slug

    def update_investment(self, dev_slug, inv_slug, use_local_raw=False):
        """
        Orchestrates the update of an investment:
        1. Scrapes raw data (or loads local)
        2. Transforms to unified USI schema
        3. Merges with existing data and ratings
        4. Synchronizes images
        """
        from usi_scrapers import api as scraper_api
        from python_worker.developer_manager import DeveloperManager

        # Path resolution via library
        usi_path = self.tech_manager.get_usi_json_path(dev_slug, inv_slug) if self.tech_manager else \
                   (self.data_dir / dev_slug / inv_slug / f"usi_{inv_slug}.json")
        inv_dir = usi_path.parent

        if not usi_path.exists() and not use_local_raw:
            logger.warning(f"Investment file not found skipping: {usi_path}")
            return False

        usi_data = {}
        if usi_path.exists():
            with open(usi_path, "r", encoding="utf-8") as f:
                usi_data = json.load(f)

        sources = usi_data.get("sources", {})
        if not sources and use_local_raw:
            for p in ["rp", "oto", "to"]:
                raw_path = inv_dir / f"raw_{p}_{inv_slug}.json"
                if raw_path.exists():
                    sources[p] = {"id": "rebuild"}

        rp_unified = None
        oto_unified = None
        to_unified = None
        fetched_sources = []

        # Generic update loop using scraper_api
        for portal in ["rp", "oto", "to"]:
            if portal not in sources: continue
            
            portal_name = "RynekPierwotny" if portal == "rp" else ("Otodom" if portal == "oto" else "TabelaOfert")
            raw_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")
            raw_files = list(inv_dir.glob(f"raw_{raw_prefix}_*.json"))
            
            if use_local_raw and raw_files:
                raw_path = raw_files[0]
                with open(raw_path, "r") as f:
                    raw_details = json.load(f)
                    adapter_key = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")
                    rp_oto_to_unified = AdapterFactory.get_adapter(adapter_key).transform(raw_details, inv_slug, dev_slug)
                    
                    if portal == "rp": rp_unified = rp_oto_to_unified
                    elif portal == "oto": oto_unified = rp_oto_to_unified
                    elif portal == "to": to_unified = rp_oto_to_unified
                    
                    fetched_sources.append(f"{portal_name} ({raw_path.name})")
            else:
                identifier = sources[portal].get("id") or sources[portal].get("url")
                if identifier:
                    res = scraper_api.fetch_investment(self.lib_config, self.fetcher, portal, identifier, dev_slug, inv_slug)
                    if "raw_details" in res:
                        dm = DeveloperManager(self.data_dir)
                        dm.save_raw_json(res["raw_details"], dev_slug, inv_slug, raw_prefix)
                        
                        adapter_key = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")
                        rp_oto_to_unified = AdapterFactory.get_adapter(adapter_key).transform(res["raw_details"], inv_slug, dev_slug)
                        
                        if portal == "rp": rp_unified = rp_oto_to_unified
                        elif portal == "oto": oto_unified = rp_oto_to_unified
                        elif portal == "to": to_unified = rp_oto_to_unified
                        
                        fetched_sources.append(portal_name)

        if rp_unified or oto_unified or to_unified:
            # Semantic layer: Ratings and Merging
            ratings_path = inv_dir / f"meta_{inv_slug}_ratings.json"
            ratings = {}
            if ratings_path.exists():
                try:
                    with open(ratings_path, "r", encoding="utf-8") as f:
                        ratings = json.load(f)
                except Exception as e:
                    logger.error(f"Error reading ratings file: {e}")
            
            event = f"Sync: {', '.join(fetched_sources)}" if fetched_sources else "Manual Update"
            new_unified = Merger.merge(rp_unified, oto_unified, to_unified, ratings, existing_data=usi_data, event=event)
            
            # Technical layer: Image synchronization via library
            all_urls = new_unified.get("image_urls", [])
            if all_urls and self.tech_manager:
                logger.info(f"Synchronizing images for {inv_slug} ({len(all_urls)} URLs)")
                saved_filenames = self.tech_manager.sync_images(all_urls, dev_slug, inv_slug)
                valid_filenames = [f for f in saved_filenames if f]
                new_unified["image_paths"] = [f"/Public/USI/{dev_slug}/{inv_slug}/{fname}" for fname in valid_filenames]
                new_unified["images_count"] = len(valid_filenames)
            elif not all_urls:
                # Fallback: check disk if no URLs provided (e.g. rebuild from raw without internet)
                img_dir = self.tech_manager.get_image_path(dev_slug, inv_slug) if self.tech_manager else \
                          (self.public_usi_dir / dev_slug / inv_slug)
                if img_dir.is_dir():
                    on_disk = [p.name for p in img_dir.iterdir() if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
                    if on_disk:
                        new_unified["image_paths"] = [f"/Public/USI/{dev_slug}/{inv_slug}/{fname}" for fname in sorted(on_disk)]
                        new_unified["images_count"] = len(on_disk)

            with open(usi_path, "w", encoding="utf-8") as f_out:
                json.dump(new_unified, f_out, indent=2, ensure_ascii=False)
            
            log_to_processing_log(dev_slug, inv_slug, f"Updated investment data. Sources: {', '.join(fetched_sources)}")
            return True
        
        return False

    def save_ratings(self, dev_slug, inv_slug, payload):
        from python_worker.api.utils import _calculate_ocena_log, _CATS, USI_STATUSES
        
        inv_dir = self.data_dir / dev_slug / inv_slug
        if not inv_dir.exists():
            return False
            
        ratings_file = inv_dir / f"meta_{inv_slug}_ratings.json"
        existing_ratings = {}
        if ratings_file.exists():
            try:
                existing_ratings = json.loads(ratings_file.read_text())
            except: pass

        changes = []
        for cat in _CATS:
            if cat in payload:
                val = payload[cat]
                if val is not None:
                    if not isinstance(val, (int, float)) or not (0 <= val <= 4):
                        raise ValueError(f"Invalid value for {cat}: {val}")
                    new_val = float(val)
                else:
                    new_val = None
                
                if existing_ratings.get(cat) != new_val:
                    changes.append({"field": f"ratings.{cat}", "old": existing_ratings.get(cat), "new": new_val})
                    existing_ratings[cat] = new_val

        if "komentarz" in payload:
            existing_ratings["komentarz"] = str(payload["komentarz"])
        if "status" in payload:
            new_status = payload["status"]
            if new_status not in USI_STATUSES:
                raise ValueError(f"Invalid status: {new_status}")
            existing_ratings["status"] = new_status

        usi_file = inv_dir / f"usi_{inv_slug}.json"
        if usi_file.exists():
            try:
                usi_data = json.loads(usi_file.read_text())
                old_score = _calculate_ocena_log(usi_data.get("ratings", {}))
                usi_data["ratings"] = {**usi_data.get("ratings", {}), **existing_ratings}
                usi_data["status"] = existing_ratings.get("status", usi_data.get("status", "Brak"))
                new_score = _calculate_ocena_log(usi_data["ratings"])
                
                audit = usi_data.setdefault("audit", {})
                audit["updated_at"] = datetime.now().isoformat()
                if changes:
                    audit.setdefault("history", []).append({
                        "timestamp": datetime.now().isoformat(),
                        "event": "Rating Updated",
                        "changes": changes
                    })
                    log_to_processing_log(dev_slug, inv_slug, f"Ratings updated. Changes: {len(changes)}")
                usi_file.write_text(json.dumps(usi_data, ensure_ascii=False, indent=2))
            except Exception as e:
                logger.error(f"Service ratings update error: {e}")

        ratings_file.write_text(json.dumps(existing_ratings, ensure_ascii=False, indent=2))
        return True

    def mark_deleted_photos(self, dev_slug, inv_slug, paths):
        inv_dir = self.data_dir / dev_slug / inv_slug
        if not inv_dir.exists():
            return False
        out = {"paths": paths, "updated_at": datetime.now().isoformat(timespec="seconds")}
        (inv_dir / "deletion_list.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        log_to_processing_log(dev_slug, inv_slug, f"Updated deletion list. Count: {len(paths)}")
        return True
