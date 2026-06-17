import os
import json
import logging
from pathlib import Path
from usi_scrapers.utils import images as scraper_images
from python_worker.config import get_shared_config

from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class ImageSyncService:
    def __init__(self, gateway, public_usi_dir: Path):
        self.gateway = gateway
        self.public_usi_dir = public_usi_dir

    def sync_investment_images(self, system_id, new_unified, all_urls, skip_images, usi_data, resources):
        """Synchronizes images for the investment."""
        
        scraper_paths = new_unified.get("image_paths", [])
        if scraper_paths and len(scraper_paths) >= len(all_urls):
            new_unified["images_count"] = len(scraper_paths)
            logger.info(f"Image paths already resolved from scraper for {system_id}: {len(scraper_paths)} paths")
            return

        if skip_images:
            new_unified["image_paths"] = usi_data.get("image_paths", [])
            new_unified["images_count"] = usi_data.get("images_count", 0)
            return

        target_image_dir = resources.get("images_dir")
        if not target_image_dir:
            logger.warning(f"Could not determine image directory for {system_id}")
            return

        portal = resources.get("metadata", {}).get("portal")
        item_id = resources.get("metadata", {}).get("portal_id")
        
        if portal and system_id.startswith(f"{portal}_"):
            parts = system_id.split("_", 1)
            if len(parts) == 2:
                item_id = parts[1]
                
        if not portal or not item_id:
            logger.error(f"Missing portal or portal_id in resources metadata for {system_id}")
            return

        if all_urls:
            logger.info(f"Synchronizing images for {system_id} ({len(all_urls)} URLs)")
            saved_filenames = self.gateway.save_images(all_urls, portal, str(item_id))

            rel_dir = target_image_dir.relative_to(self.public_usi_dir)
            new_paths = [f"/Public/USI/{rel_dir}/{fname}" for fname in saved_filenames if fname]
            
            existing_paths = usi_data.get("image_paths", [])
            # Zachowaj kolejność (stare zdjęcia zostają, nowe lądują na końcu bez duplikatów)
            combined_paths = list(dict.fromkeys(existing_paths + new_paths))
            
            new_unified["image_paths"] = combined_paths
            new_unified["images_count"] = len(combined_paths)
        else:
            # Brak zdjęć w aktualnym scraphie -> zachowujemy to, co mieliśmy w pliku usi_*.json
            existing_paths = usi_data.get("image_paths", [])
            if existing_paths:
                new_unified["image_paths"] = existing_paths
                new_unified["images_count"] = len(existing_paths)
            elif target_image_dir.is_dir():
                on_disk = sorted(p.name for p in target_image_dir.iterdir()
                                 if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
                if on_disk:
                    rel_dir = target_image_dir.relative_to(self.public_usi_dir)
                    new_unified["image_paths"] = [f"/Public/USI/{rel_dir}/{fname}" for fname in on_disk]
                    new_unified["images_count"] = len(on_disk)
                else:
                    new_unified["image_paths"] = []
                    new_unified["images_count"] = 0
            else:
                new_unified["image_paths"] = []
                new_unified["images_count"] = 0

        logger.info(f"Image sync complete for {system_id}: {new_unified['images_count']} paths resolved")
