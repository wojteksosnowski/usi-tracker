import json
import logging
from pathlib import Path
from datetime import datetime

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.adapters import AdapterFactory, Merger
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)


def _primary_portal_id(sources: dict) -> tuple[str, str | None]:
    """Return (portal, id) for the highest-priority portal that has an ID."""
    for portal in ("rp", "oto", "to"):
        pid = (sources.get(portal) or {}).get("id")
        if pid:
            return portal, str(pid)
    return "rp", None


def _find_inv_file(inv_dir: Path, inv_slug: str, usi_inv_id: str = None) -> Path | None:
    """Find the canonical investment JSON in inv_dir (by ID first, then new format, then legacy)."""
    if usi_inv_id:
        for f in inv_dir.glob(f"usi_*_{usi_inv_id}.json"):
            return f
        # Fallback: check file content for ID if filename doesn't have it
        for f in inv_dir.glob("usi_*.json"):
            try:
                if json.loads(f.read_text()).get("usi_inv_id") == usi_inv_id:
                    return f
            except Exception:
                continue

    for p in ("rp", "oto", "to"):
        candidates = sorted(inv_dir.glob(f"usi_{p}_*.json"))
        if candidates:
            return candidates[0]
    for legacy in (
        inv_dir / f"usi_{inv_slug}.json",
        inv_dir / f"usi_rp_{inv_slug}.json",
        inv_dir / f"usi_oto_{inv_slug}.json",
        inv_dir / f"usi_to_{inv_slug}.json",
    ):
        if legacy.exists():
            return legacy
    return None


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

    def get_investment(self, dev_slug, inv_slug, portal: str = None):
        from python_worker.api.utils import _load_investment
        return _load_investment(dev_slug, inv_slug, data_dir=self.data_dir, public_usi_dir=self.public_usi_dir, portal=portal)

    def register_investment(self, portal, developer_name, inv_slug, name, item_id=None, url=None, allow_existing=False, vendor_id=None, force_dev_slug=None):
        from python_worker.developer_manager import DeveloperManager
        from usi_scrapers import api as scraper_api
        from python_worker.url_parser import parse_url

        dm = DeveloperManager(self.data_dir)
        developer_record = None
        dev_slug = force_dev_slug

        # PRIORITY 1: Identify by Vendor ID (if provided)
        if not dev_slug and vendor_id:
            developer_record = dm.find_developer_by_id(portal, str(vendor_id))
            if developer_record:
                dev_slug = developer_record["developer_slug"]
                developer_name = developer_record["name"]
                logger.info(f"Found developer by ID {vendor_id} ({portal}): {developer_name} ({dev_slug})")

        # PRIORITY 2: Canonical Slug Extraction via library parser
        if not dev_slug and not developer_record and url:
            parsed = parse_url(url)
            if parsed.get("investment_slug") and parsed["investment_slug"] != "unknown":
                inv_slug = parsed["investment_slug"]
            if parsed.get("developer_slug") and parsed["developer_slug"] != "unknown":
                # Only overwrite if we don't have a better name already
                # or if we are dealing with 'Nieznany Deweloper'
                is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
                if is_unknown:
                    developer_name = parsed["developer_slug"].replace("-", " ").title()

        # Identification pre-scrapes (Otodom/TabelaOfert) via API
        is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
        if not dev_slug and not developer_record and is_unknown and portal in ("oto", "to") and url:
            logger.info(f"Developer unknown for {url}, performing pre-scrape identification ({portal})...")
            try:
                identified_name = scraper_api.identify_developer(self.fetcher, portal, url)
                if identified_name:
                    developer_name = identified_name
                    is_unknown = False
            except Exception as e:
                logger.error(f"Pre-scrape identification failed ({portal}): {e}")

        if not dev_slug:
            if not developer_record:
                dev_slug = "unknown"
                if not is_unknown:
                    logger.warning(f"No USI record found by ID for developer '{developer_name}' - placing in 'unknown' folder")
            else:
                dev_slug = developer_record["developer_slug"]
        
        # Auto-create developer profile ONLY if we have a real slug (not 'unknown')
        if dev_slug != "unknown" and not dm.get_developer(dev_slug):
            logger.info(f"Auto-creating developer profile for: {developer_name} ({dev_slug})")
            
            # Initialize portal mapping if we have enough info
            initial_pm = {"rp": None, "oto": None, "to": None}
            if portal == "rp" and vendor_id:
                initial_pm["rp"] = {"id": str(vendor_id)}
            elif portal == "to" and vendor_id:
                initial_pm["to"] = {"agency_id": str(vendor_id)}
            elif portal == "oto" and vendor_id:
                initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}

            dm.create_developer_file({
                "developer_slug": dev_slug, 
                "name": developer_name,
                "portal_mapping": initial_pm
            })

        inv_dir = self.data_dir / dev_slug / inv_slug

        # 1. Check if investment already exists (any file format)
        if _find_inv_file(inv_dir, inv_slug):
            if allow_existing:
                return dev_slug, inv_slug
            raise ValueError(f"Investment already exists: {dev_slug}/{inv_slug}")

        # 2. Check for ID-based duplication across all investments
        # This prevents 500 errors when portal changes slug/dev but ID remains same
        existing_ids = dm.get_existing_identifiers()
        id_exists = False
        if portal == "rp" and item_id and str(item_id) in existing_ids.get("rp_ids", set()):
            id_exists = True
        elif portal == "oto" and item_id and str(item_id) in existing_ids.get("oto_ids", set()):
            id_exists = True
        elif portal == "to" and item_id and str(item_id) in existing_ids.get("to_ids", set()):
            id_exists = True

        if id_exists:
            logger.info(f"Investment with ID {item_id} ({portal}) already exists in system. Skipping registration.")
            return None, None

        inv_dir.mkdir(parents=True, exist_ok=True)

        # Canonical filename: usi_{portal}_{portal_id}.json (new format)
        if portal == "rp" and item_id:
            filename = f"usi_rp_{item_id}.json"
            sources = {"rp": {"id": str(item_id), "url": url}}
            if vendor_id:
                sources["rp"]["vendor_id"] = str(vendor_id)
        elif portal == "oto" and item_id:
            filename = f"usi_oto_{item_id}.json"
            sources = {"oto": {"id": str(item_id), "url": url}}
        elif portal == "to" and item_id:
            filename = f"usi_to_{item_id}.json"
            sources = {"to": {"id": str(item_id), "url": url}}
        else:
            filename = f"usi_{inv_slug}.json"
            sources = {}
            if portal == "rp":
                sources["rp"] = {"url": url}
            elif portal == "oto":
                sources["oto"] = {"url": url}
            elif portal == "to":
                sources["to"] = {"url": url}

        usi_path = inv_dir / filename

        # Use DeveloperManager for consistent ID generation
        usi_inv_id = dm.generate_usi_id("INV")
        
        skeleton = {
            "investment_slug": inv_slug,
            "developer_slug": dev_slug,
            "name": name,
            "reviewed": False,
            "sources": sources,
            "status": "Brak",
            "usi_inv_id": usi_inv_id,
            "audit": {"created_at": datetime.now().isoformat()}
        }

        with open(usi_path, "w", encoding="utf-8") as f:
            json.dump(skeleton, f, indent=2, ensure_ascii=False)

        try:
            import python_worker.investment_index as inv_index
            inv_index.upsert(self.data_dir, self.public_usi_dir, dev_slug, inv_slug)
        except Exception as _ie:
            logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")

        log_to_processing_log(dev_slug, inv_slug, f"Registered from discovery ({portal})")
        return dev_slug, inv_slug

    def _canonical_slug_from_raw(self, portal: str, raw_details: dict, fallback: str) -> str:
        """Resolves the canonical USI developer slug by reading it from portal raw data.

        Priority:
          1. find_developer_by_id(portal_id from raw)  — ID-first, authoritative
          2. portal slug parsed from raw data           — slug as the portal defines it
          3. fallback                                   — whatever was passed in
        """
        from python_worker.developer_manager import DeveloperManager
        dm = DeveloperManager(self.data_dir)

        portal_id = None
        portal_slug = None

        if portal == "rp":
            vendor = raw_details.get("vendor") or {}
            portal_id = str(vendor.get("id", "")) or None
            portal_slug = vendor.get("slug")
        elif portal == "oto":
            agency = (raw_details.get("ad") or {}).get("agency") or {}
            raw_id = agency.get("id")
            portal_id = str(raw_id) if raw_id else None
            url = agency.get("url", "")
            if url and "-ID" in url:
                portal_slug = url.rstrip("/").split("/")[-1].rsplit("-ID", 1)[0]
        elif portal == "to":
            portal_slug = raw_details.get("developer_slug")

        if portal_id:
            dev_record = dm.find_developer_by_id(portal, portal_id)
            if dev_record:
                return dev_record["developer_slug"]

        return portal_slug or fallback

    def update_investment(self, dev_slug, inv_slug, use_local_raw=False, skip_images=False, skip_index=False, skip_log=False):
        """
        Orchestrates the update of an investment:
        1. Scrapes raw data (or loads local)
        2. Transforms to unified USI schema
        3. Merges with existing data and ratings
        4. Synchronizes images

        Returns True on success, False if no data was fetched/merged.
        Raises RuntimeError with a human-readable message if all portals failed.
        """
        from usi_scrapers import api as scraper_api

        inv_dir = self.data_dir / dev_slug / inv_slug
        actual_file = _find_inv_file(inv_dir, inv_slug)

        if not actual_file and not use_local_raw:
            logger.warning(f"Investment file not found skipping: {inv_dir}/usi_*.json")
            return False

        usi_data = {}
        if actual_file and actual_file.exists():
            with open(actual_file, "r", encoding="utf-8") as f:
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
        failed_sources = []
        # Initial guess for images is the current folder name
        img_dev_slug = dev_slug
        
        # Mandate: Trust recorded paths. Check where images WERE stored before.
        existing_img_list = usi_data.get("ratings", {}).get("imgList")
        if not existing_img_list and usi_data.get("image_paths"):
            existing_img_list = usi_data["image_paths"][0]
            
        if existing_img_list:
            import re
            m = re.search(r'/Public/USI/([^/]+)/', str(existing_img_list))
            if m:
                img_dev_slug = m.group(1)
                logger.info(f"Image folder for {inv_slug} pinned to recorded path: {img_dev_slug}")

        # Generic update loop using scraper_api
        for portal in ["rp", "oto", "to"]:
            if portal not in sources: continue

            portal_name = "RynekPierwotny" if portal == "rp" else ("Otodom" if portal == "oto" else "TabelaOfert")
            raw_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")
            raw_files = list(inv_dir.glob(f"raw_{raw_prefix}_*.json"))

            if use_local_raw and raw_files:
                canonical = inv_dir / f"raw_{raw_prefix}_{inv_slug}.json"
                raw_path = canonical if canonical.exists() else sorted(raw_files)[-1]
                with open(raw_path, "r") as f:
                    raw_details = json.load(f)
                
                # Transform using the FOLDER slug (dev_slug) to maintain consistency
                rp_oto_to_unified = AdapterFactory.get_adapter(raw_prefix).transform(raw_details, inv_slug, dev_slug)
                if portal == "rp": rp_unified = rp_oto_to_unified
                elif portal == "oto": oto_unified = rp_oto_to_unified
                elif portal == "to": to_unified = rp_oto_to_unified
                fetched_sources.append(f"{portal_name} (local)")
            elif use_local_raw:
                logger.debug(f"[local-raw] {portal_name}: no raw file in {inv_dir}, skipping")
                continue
            else:
                # RP uses numeric ID; Otodom and TO require a full URL
                if portal == "rp":
                    identifier = sources[portal].get("id") or sources[portal].get("url")
                else:
                    identifier = sources[portal].get("url") or sources[portal].get("id")
                if not identifier:
                    log_to_processing_log(dev_slug, inv_slug, f"Skipped {portal_name}: no identifier in sources")
                    continue
                try:
                    res = scraper_api.fetch_investment(self.lib_config, self.fetcher, portal, identifier)
                except Exception as e:
                    error_msg = f"Exception during fetch: {e}"
                    logger.error(f"[{portal_name}] {inv_slug}: {error_msg}")
                    log_to_processing_log(dev_slug, inv_slug, f"Error fetching from {portal_name}: {error_msg}")
                    failed_sources.append(f"{portal_name} ({error_msg})")
                    continue

                if res and "raw_details" in res:
                    raw_data = res["raw_details"]
                    canonical_dev_slug = self._canonical_slug_from_raw(raw_prefix, raw_data, dev_slug)
                    
                    if self.tech_manager:
                        # Save raw data using canonical slug (for library mapping)
                        self.tech_manager.save_raw_data(raw_data, canonical_dev_slug, inv_slug, raw_prefix)
                    else:
                        logger.error(f"Cannot save raw data for {inv_slug}: TechnicalDataManager is not available.")
                        raise RuntimeError("TechnicalDataManager is required for saving raw portal data.")

                    # Transform unified data using the FOLDER slug (dev_slug)
                    rp_oto_to_unified = AdapterFactory.get_adapter(raw_prefix).transform(raw_data, inv_slug, dev_slug)
                    if portal == "rp": rp_unified = rp_oto_to_unified
                    elif portal == "oto": oto_unified = rp_oto_to_unified
                    elif portal == "to": to_unified = rp_oto_to_unified
                    fetched_sources.append(portal_name)
                else:
                    error_msg = res.get("error", "Unknown error") if isinstance(res, dict) else "No valid response"
                    logger.error(f"[{portal_name}] {inv_slug}: {error_msg}")
                    log_to_processing_log(dev_slug, inv_slug, f"Fetch failed — {portal_name}: {error_msg}")
                    failed_sources.append(f"{portal_name} ({error_msg})")


        if rp_unified or oto_unified or to_unified:
            # Semantic layer: Ratings and Merging
            # Try canonical name first, then portal-prefixed variants from bulk imports
            ratings_candidates = [
                inv_dir / f"meta_{inv_slug}_ratings.json",
                inv_dir / f"meta_rp_{inv_slug}.json",
                inv_dir / f"meta_oto_{inv_slug}.json",
                inv_dir / f"meta_to_{inv_slug}.json",
            ]
            ratings = {}
            for ratings_path in ratings_candidates:
                if ratings_path.exists():
                    try:
                        with open(ratings_path, "r", encoding="utf-8") as f:
                            ratings = json.load(f)
                        break
                    except Exception as e:
                        logger.error(f"Error reading ratings file: {e}")

            event = f"Sync: {', '.join(fetched_sources)}" if fetched_sources else "Manual Update"
            new_unified = Merger.merge(rp_unified, oto_unified, to_unified, ratings, existing_data=usi_data, event=event)

            # Technical layer: Image synchronization via library
            # img_dev_slug comes from portal raw data, not from slugify — canonical per the portal.
            all_urls = new_unified.get("image_urls", [])
            if skip_images:
                all_urls = []  # skip download; existing on-disk images are picked up below
            if all_urls and self.tech_manager:
                logger.info(f"Synchronizing images for {inv_slug} ({len(all_urls)} URLs)")
                saved_filenames = self.tech_manager.sync_images(all_urls, img_dev_slug, inv_slug)
                valid_filenames = [f for f in saved_filenames if f]
                new_unified["image_paths"] = [f"/Public/USI/{img_dev_slug}/{inv_slug}/{fname}" for fname in valid_filenames]
                new_unified["images_count"] = len(valid_filenames)
                logger.info(f"Image sync complete for {inv_slug}: {len(valid_filenames)}/{len(all_urls)} saved")
            elif all_urls and not self.tech_manager:
                logger.warning(f"Image sync skipped for {inv_slug}: tech_manager not available (check SCRAPERAPI_KEY / config)")
                log_to_processing_log(dev_slug, inv_slug, "Image sync skipped: scraper config unavailable")
            else:
                # No URLs from scraper — keep whatever is already on disk
                img_dir = self.tech_manager.get_image_path(img_dev_slug, inv_slug) if self.tech_manager else \
                          (self.public_usi_dir / img_dev_slug / inv_slug)
                if img_dir.is_dir():
                    on_disk = sorted(p.name for p in img_dir.iterdir()
                                     if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"})
                    if on_disk:
                        new_unified["image_paths"] = [f"/Public/USI/{img_dev_slug}/{inv_slug}/{fname}" for fname in on_disk]
                        new_unified["images_count"] = len(on_disk)

            # Backfill developer ID into portal_mapping if missing
            from python_worker.developer_manager import DeveloperManager
            dm = DeveloperManager(self.data_dir)
            dev_record = dm.get_developer(dev_slug)
            if dev_record:
                needs_update = False
                pm = dev_record.setdefault("portal_mapping", {"rp": None, "oto": None, "to": None})
                new_src = new_unified.get("sources", {})
                
                # Check RP
                rp_src = new_src.get("rp", {})
                if rp_src.get("vendor_id"):
                    if not pm.get("rp"):
                        pm["rp"] = {"id": rp_src["vendor_id"]}
                        needs_update = True
                    elif pm["rp"].get("id") != rp_src["vendor_id"]:
                        # Might be conflict, but we trust the fresh raw data if it was null
                        if not pm["rp"].get("id"):
                            pm["rp"]["id"] = rp_src["vendor_id"]
                            needs_update = True
                            
                # Check Otodom
                oto_src = new_src.get("oto", {})
                if oto_src.get("agency_id"):
                    if not pm.get("oto"):
                        pm["oto"] = {"agency_id": oto_src["agency_id"], "agency_ids": [oto_src["agency_id"]]}
                        needs_update = True
                    else:
                        aids = pm["oto"].setdefault("agency_ids", [])
                        if oto_src["agency_id"] not in aids:
                            aids.append(oto_src["agency_id"])
                            pm["oto"]["agency_id"] = oto_src["agency_id"] # promote to main
                            needs_update = True
                            
                # Check TO
                to_src = new_src.get("to")
                if to_src is not None:
                    if not pm.get("to"):
                        pm["to"] = {"agency_id": to_src.get("developer_id", "")}
                        needs_update = True
                    elif not pm["to"].get("agency_id") and to_src.get("developer_id"):
                        pm["to"]["agency_id"] = to_src["developer_id"]
                        needs_update = True
                        
                if needs_update:
                    dm.create_developer_file(dev_record)
                    logger.info(f"Backfilled developer ID into portal_mapping for {dev_slug}")

            # Save to canonical new-format path; fall back to existing file path
            primary_portal, primary_id = _primary_portal_id(new_unified.get("sources", {}))
            if primary_id:
                out_path = inv_dir / f"usi_{primary_portal}_{primary_id}.json"
            else:
                out_path = actual_file or (inv_dir / f"usi_{inv_slug}.json")

            with open(out_path, "w", encoding="utf-8") as f_out:
                json.dump(new_unified, f_out, indent=2, ensure_ascii=False)

            if not skip_index:
                try:
                    import python_worker.investment_index as inv_index
                    inv_index.upsert(self.data_dir, self.public_usi_dir, dev_slug, inv_slug)
                except Exception as _ie:
                    logger.debug(f"Index upsert skipped for {inv_slug}: {_ie}")

            if not skip_log:
                summary = f"Updated: {', '.join(fetched_sources)}"
                if failed_sources:
                    summary += f". Failed: {', '.join(failed_sources)}"
                log_to_processing_log(dev_slug, inv_slug, summary)
            return True

        # All portals failed
        if failed_sources:
            raise RuntimeError(f"Fetch failed for all portals: {'; '.join(failed_sources)}")
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

        usi_file = _find_inv_file(inv_dir, inv_slug)
        if usi_file:
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

        try:
            import python_worker.investment_index as inv_index
            inv_index.upsert(self.data_dir, self.public_usi_dir, dev_slug, inv_slug)
        except Exception as _ie:
            logger.debug(f"Index upsert skipped after ratings save for {inv_slug}: {_ie}")

        return True

    def process_batch(self, portal, investments, on_progress_callback=None):
        """
        Processes a batch of investments using the library's process_batch function.
        Downloads data first, then registers and unifies only successful ones.
        """
        from usi_scrapers import api as scraper_api
        from python_worker.slug_utils import slugify
        from python_worker.url_parser import parse_url
        from python_worker.developer_manager import DeveloperManager

        dm = DeveloperManager(self.data_dir)

        # 1. Prepare identifiers and metadata without registering skeletons yet
        to_process = []
        identifiers = []

        for item in investments:
            # We don't strictly need slugs or names here anymore, as usi-scrapers v0.5.0+ 
            # resolves and saves everything to the correct folders in-flight.
            ident = url = item.get("url")
            inv_slug = item.get("inv_slug") or item.get("slug")
            if not inv_slug and url:
                import re as _re
                _parsed = parse_url(url)
                _raw_slug = _parsed.get("investment_slug", "")
                if _raw_slug:
                    inv_slug = _raw_slug
                    inv_slug = inv_slug or None
            dev_name = item.get("developer_name") or item.get("developer")
            
            if ident:
                # Try to resolve dev_slug if possible for faster post-processing, but don't block
                dev_slug = None
                vendor_id = item.get("vendor_id") or item.get("agency_id") or item.get("developer_id")
                if portal == "rp" and isinstance(item.get("vendor"), dict):
                    vendor_id = item["vendor"].get("id")
                
                dev_record = dm.find_developer_by_id(portal, str(vendor_id)) if vendor_id else None
                if dev_record:
                    dev_slug = dev_record["developer_slug"]
                    dev_name = dev_record["name"]
                elif dev_name and dev_name.lower() not in ("nieznany deweloper", "unknown", "nieznany-deweloper"):
                    # Only use existing folder if we have a real name match
                    matched_dev = dm.get_developer_by_name(dev_name)
                    if matched_dev:
                        dev_slug = matched_dev["developer_slug"]

                if portal == "rp":
                    ident = item.get("id") or url

                identifiers.append(ident)
                to_process.append({
                    "ident": ident,
                    "dev_slug": dev_slug,
                    "inv_slug": inv_slug,
                    "name": item.get("name"),
                    "item_id": item.get("id"),
                    "url": url,
                    "portal": portal,
                    "dev_name": dev_name
                })

        if not identifiers:
            return False

        # 2. Call library process_batch
        # This will save raw_*.json files to disk for successful items
        batch_results = scraper_api.process_batch(
            self.lib_config, self.fetcher, portal, identifiers, on_progress=on_progress_callback
        )

        # 3. Finalize: Register and Update ONLY if raw data exists
        success_count = 0
        raw_prefix = "rp" if portal == "rp" else ("oto" if portal == "oto" else "to")

        for info, data in zip(to_process, batch_results):
            try:
                # Fallbacks in case scraping failed completely
                dev_slug = info["dev_slug"]
                inv_slug = info["inv_slug"]
                
                # Use precise data returned from library if available
                vendor_id = None
                if data and isinstance(data, dict):
                    if data.get("developer_slug"):
                        dev_slug = data["developer_slug"]
                        logger.info(f"Using developer_slug '{dev_slug}' from library result for {info['ident']}")
                    if data.get("investment_slug"):
                        inv_slug = data["investment_slug"]
                    if data.get("id"):
                        info["item_id"] = data["id"]
                    if data.get("agency_id"):
                        vendor_id = data["agency_id"]
                    elif data.get("vendor_id"):
                        vendor_id = data["vendor_id"]

                if not dev_slug or not inv_slug:
                    logger.warning(f"Could not finalize batch item {info['ident']} - missing slugs (dev={dev_slug}, inv={inv_slug}).")
                    continue

                inv_dir = self.data_dir / dev_slug / inv_slug
                raw_files = list(inv_dir.glob(f"raw_{raw_prefix}_*.json"))

                if not raw_files:
                    logger.warning(f"Batch download failed for {inv_slug} (no raw data found in {dev_slug}/{inv_slug}) - skipping registration.")
                    continue

                # Register (creates usi_*.json skeleton and ID)
                res = self.register_investment(
                    portal=info["portal"],
                    developer_name=info["dev_name"] or dev_slug.replace("-", " ").title(),
                    inv_slug=inv_slug,
                    name=info["name"] or (data.get("title") if isinstance(data, dict) else None),
                    item_id=info["item_id"],
                    url=info["url"],
                    allow_existing=True,
                    vendor_id=vendor_id,
                    force_dev_slug=dev_slug
                )

                
                if res and res[0]: # res is (dev_slug, inv_slug)
                    # Unify and Sync images
                    if self.update_investment(res[0], res[1], use_local_raw=True):
                        success_count += 1
                else:
                    logger.info(f"Investment {inv_slug} already exists or duplicate ID - skipping batch update.")

                    
            except Exception as e:
                logger.error(f"Post-batch processing failed for {info['inv_slug']}: {e}")

        logger.info(f"Batch processing complete: {success_count}/{len(to_process)} investments fully ingested.")
        return success_count

    def mark_as_reviewed(self, dev_slug, inv_slug, usi_inv_id=None):
        """Sets the reviewed flag to true for the specified investment."""
        inv_dir = self.data_dir / dev_slug / inv_slug
        usi_file = _find_inv_file(inv_dir, inv_slug, usi_inv_id=usi_inv_id)

        if not usi_file:
            return False

        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            data["reviewed"] = True
            data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

            with open(usi_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_to_processing_log(dev_slug, inv_slug, f"Investment {usi_inv_id or inv_slug} marked as reviewed by analyst.")
            return True
        except Exception as e:
            logger.error(f"Failed to mark as reviewed: {e}")
            return False

    def add_report(self, dev_slug, inv_slug, note, usi_inv_id=None):
        """Adds a problem report note to the investment record."""
        inv_dir = self.data_dir / dev_slug / inv_slug
        usi_file = _find_inv_file(inv_dir, inv_slug, usi_inv_id=usi_inv_id)

        if not usi_file:
            return False

        try:
            with open(usi_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            reports = data.setdefault("issue_reports", [])
            reports.insert(0, {
                "note": note,
                "at": datetime.now().isoformat()
            })

            audit = data.setdefault("audit", {})
            audit["updated_at"] = datetime.now().isoformat()
            audit["audit_needed"] = True

            with open(usi_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            log_to_processing_log(dev_slug, inv_slug, f"Issue reported for {usi_inv_id or inv_slug}: {note[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Failed to add report for {inv_slug}: {e}")
            return False

    def mark_deleted_photos(self, dev_slug, inv_slug, paths, usi_inv_id=None):
        inv_dir = self.data_dir / dev_slug / inv_slug
        if not inv_dir.exists():
            return False

        # Deletion list is currently folder-wide, but we could make it per-ID if needed.
        # For now, we'll keep it as-is but log the ID that triggered it.
        out = {"paths": paths, "updated_at": datetime.now().isoformat(timespec="seconds")}
        (inv_dir / "deletion_list.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
        log_to_processing_log(dev_slug, inv_slug, f"Updated deletion list (via {usi_inv_id or 'slug'}). Count: {len(paths)}")
        return True
