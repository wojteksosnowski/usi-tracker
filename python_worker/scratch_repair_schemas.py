import json
from pathlib import Path
from python_worker.developer_manager import DeveloperManager
from python_worker.config import USI_DATA_DIR, USI_DEV_DIR
from python_worker.developer_index import load as load_dev_index
import logging
from python_worker.developer_index import remove as remove_index

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_repair():
    dm = DeveloperManager(USI_DATA_DIR, USI_DEV_DIR)
    devs = load_dev_index(USI_DEV_DIR) or dm.list_developers(only_merged=False)
    
    orphans_removed = 0
    schemas_repaired = 0
    merge_candidates = []
    
    for dev in devs:
        slug = dev.get("developer_slug")
        if not slug:
            continue
            
        dev_data_dir = USI_DATA_DIR / slug
        has_investments = False
        investment_portal_ids = {"rp": set(), "oto": set(), "to": set()}
        
        if dev_data_dir.exists() and dev_data_dir.is_dir():
            for child in dev_data_dir.iterdir():
                if child.is_dir() and not child.name.startswith("_") and not child.name.startswith("."):
                    has_investments = True
                    # Look for usi_*.json
                    for usi_file in child.glob("usi_*.json"):
                        try:
                            inv_data = json.loads(usi_file.read_text(encoding="utf-8"))
                            sources = inv_data.get("sources", {})
                            if "rp" in sources and sources["rp"].get("id"):
                                investment_portal_ids["rp"].add(str(sources["rp"]["id"]))
                            if "oto" in sources and sources["oto"].get("agency_id"):
                                investment_portal_ids["oto"].add(str(sources["oto"]["agency_id"]))
                            if "to" in sources and sources["to"].get("id"):
                                investment_portal_ids["to"].add(str(sources["to"]["id"]))
                        except Exception:
                            pass
                            
        is_merged = bool(dev.get("master_id"))
        
        # 1. ORPHAN CHECK
        if not has_investments and not is_merged:
            # Delete the developer
            logger.info(f"Removing orphan developer: {slug}")
            dev_file_path = dm._dev_file_path(slug, dev.get("usi_dev_id"))
            if dev_file_path and dev_file_path.exists():
                dev_file_path.unlink()
            # Also try flat paths
            for candidate in [
                dm._dev_file_path_old_canonical(slug),
                dm._dev_file_path_legacy(slug),
                dm.data_dir / slug / f"usi_dev_{slug}.json"
            ]:
                if candidate and candidate.exists():
                    candidate.unlink()
            
            remove_index(USI_DEV_DIR, dev.get("usi_dev_id"))
            orphans_removed += 1
            continue

        # 2. SCHEMA REPAIR
        needs_save = False
        pm = dev.get("portal_mapping")
        
        # Ensure default structure
        if not pm or not isinstance(pm, dict):
            pm = {"rp": None, "oto": None, "to": None}
            dev["portal_mapping"] = pm
            needs_save = True
        
        for p in ["rp", "oto", "to"]:
            if p not in pm:
                pm[p] = None
                needs_save = True

        # Try to heal missing mappings using investment data
        for portal in ["rp", "oto", "to"]:
            current_mapping = pm.get(portal)
            # If current mapping is missing or empty
            if not current_mapping:
                found_ids = investment_portal_ids[portal]
                if found_ids:
                    # Pick the first one (usually there's only one developer ID per portal)
                    new_id = list(found_ids)[0]
                    
                    # DUPLICATE PREVENTION: check if someone else already has this ID
                    existing_dev = dm.find_by_portal_id(portal, new_id)
                    if existing_dev and existing_dev.get("usi_dev_id") != dev.get("usi_dev_id"):
                        logger.warning(f"Merge candidate detected: {slug} has investments with {portal}={new_id}, but {existing_dev.get('developer_slug')} already maps to it.")
                        merge_candidates.append((slug, existing_dev.get('developer_slug'), portal, new_id))
                    else:
                        # Auto-assign
                        if portal == "oto":
                            pm[portal] = {"agency_id": new_id}
                        else:
                            pm[portal] = {"id": new_id}
                        needs_save = True
                        logger.info(f"Healed {slug} {portal} mapping with ID {new_id}")

        if needs_save:
            dm.create_developer_file(dev)
            schemas_repaired += 1

    logger.info(f"Cleanup complete. Orphans removed: {orphans_removed}. Schemas repaired: {schemas_repaired}.")
    if merge_candidates:
        logger.info(f"Found {len(merge_candidates)} potential merge candidates requiring manual resolution.")
        for mc in merge_candidates:
            logger.info(f" - {mc[0]} has investments, {mc[1]} has mapping ({mc[2]}:{mc[3]})")

if __name__ == "__main__":
    run_repair()
