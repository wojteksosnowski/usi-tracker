import os
import logging
from pathlib import Path

from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

class ImageSyncService:
    def __init__(self, tech_manager, public_usi_dir: Path):
        self.tech_manager = tech_manager
        self.public_usi_dir = public_usi_dir

    def sync_investment_images(self, system_id, new_unified, all_urls, skip_images, usi_data, resources):
        """Synchronizes images for the investment."""
        if skip_images:
            # Pełne pominięcie jakichkolwiek operacji dyskowych na katalogu obrazów
            new_unified["image_paths"] = usi_data.get("image_paths", [])
            new_unified["images_count"] = usi_data.get("images_count", 0)
            return

        target_image_dir = resources.get("images_dir")

        if all_urls and self.tech_manager:
            logger.info(f"Synchronizing images for {system_id} ({len(all_urls)} URLs)")
            
            # FAST-PATH: Try to find files already downloaded based on previous state and canonical folder
            try:
                from usi_scrapers.utils.images import clean_filename
                
                # Map urls to expected basenames
                url_to_basename = {url: os.path.splitext(clean_filename(url))[0] for url in all_urls}
                basename_to_urls = {}
                for url, bname in url_to_basename.items():
                    basename_to_urls.setdefault(bname, []).append(url)
                    
                expected_set = set(basename_to_urls.keys())
                found_paths = {}  # maps url -> full path
                
                # 1. Check existing paths from the last state of the investment
                existing_paths = usi_data.get("image_paths", [])
                for path in existing_paths:
                    bname = os.path.splitext(os.path.basename(path))[0]
                    if bname in expected_set:
                        for url in basename_to_urls[bname]:
                            found_paths[url] = path
                        expected_set.remove(bname)
                        if not expected_set: break
                        
                # 2. Check the canonical images directory for this investment
                if expected_set and target_image_dir and target_image_dir.exists():
                    for file in os.listdir(target_image_dir):
                        bname = os.path.splitext(file)[0]
                        if bname in expected_set:
                            rel_path = os.path.relpath(os.path.join(target_image_dir, file), self.public_usi_dir)
                            path_str = f"/Public/USI/{rel_path}"
                            for url in basename_to_urls[bname]:
                                found_paths[url] = path_str
                            expected_set.remove(bname)
                            if not expected_set: break
                        
                urls_to_download = []
                for url in all_urls:
                    if url not in found_paths:
                        urls_to_download.append(url)
                        
            except Exception as e:
                logger.error(f"Error during image fallback search: {e}")
                urls_to_download = all_urls
                found_paths = {}

            saved_filenames = []
            if urls_to_download:
                if not target_image_dir:
                     logger.warning(f"Could not determine image directory for {system_id}")
                else:
                     saved_filenames = self.tech_manager.sync_images(urls_to_download, target_image_dir)
                        
            unique_paths = []
            for url in all_urls:
                if url in found_paths:
                    p = found_paths[url]
                    if p not in unique_paths:
                        unique_paths.append(p)
            
            if target_image_dir:
                rel_dir = target_image_dir.relative_to(self.public_usi_dir)
                for fname in saved_filenames:
                    if fname:
                        p = f"/Public/USI/{rel_dir}/{fname}"
                        if p not in unique_paths:
                            unique_paths.append(p)
            
            new_unified["image_paths"] = unique_paths
            new_unified["images_count"] = len(unique_paths)
            logger.info(f"Image sync complete for {system_id}: {len(unique_paths)}/{len(all_urls)} paths resolved")
            
        elif all_urls and not self.tech_manager:
            logger.warning(f"Image sync skipped for {system_id}: tech_manager not available (check SCRAPERAPI_KEY / config)")
            log_to_processing_log(system_id, "unknown", "Image sync skipped: scraper config unavailable")
        else:
            # No URLs from scraper — keep whatever is already on disk
            img_dir = target_image_dir
            if img_dir and img_dir.is_dir():
                on_disk = sorted(p.name for p in img_dir.iterdir()
                                 if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
                if on_disk:
                    rel_dir = img_dir.relative_to(self.public_usi_dir)
                    new_unified["image_paths"] = [f"/Public/USI/{rel_dir}/{fname}" for fname in on_disk]
                    new_unified["images_count"] = len(on_disk)
