import logging

logger = logging.getLogger(__name__)

class DeveloperResolver:
    def __init__(self, developer_manager, sync_service=None, identity_resolver=None):
        self.dm = developer_manager
        self.sync_service = sync_service
        self.identity = identity_resolver

    def resolve_developer_for_registration(self, portal, developer_name, url, vendor_id, force_dev_slug):
        from usi_scrapers import api as scraper_api
        from python_worker.url_parser import parse_url

        developer_record = None
        dev_slug = force_dev_slug
        inv_slug_from_url = None

        # PRIORITY 1: Identify by Vendor ID (if provided)
        if not dev_slug and vendor_id:
            developer_record = self.dm.find_developer_by_id(portal, str(vendor_id))
            if developer_record:
                dev_slug = developer_record["developer_slug"]
                developer_name = developer_record["name"]
                logger.info(f"Found developer by ID {vendor_id} ({portal}): {developer_name} ({dev_slug})")

        # PRIORITY 2: Canonical Slug Extraction via library parser
        if not dev_slug and not developer_record and url:
            parsed = parse_url(url)
            if parsed.get("investment_slug") and parsed["investment_slug"] != "unknown":
                inv_slug_from_url = parsed["investment_slug"]
            if parsed.get("developer_slug") and parsed["developer_slug"] != "unknown":
                # Only overwrite if we don't have a better name already
                # or if we are dealing with 'Nieznany Deweloper'
                is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
                if is_unknown:
                    developer_name = parsed["developer_slug"].replace("-", " ").title()

        # Identification pre-scrapes (Otodom/TabelaOfert) via API
        is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
        if not dev_slug and not developer_record and is_unknown and portal in ("oto", "to") and url and self.sync_service:
            logger.info(f"Developer unknown for {url}, performing pre-scrape identification ({portal})...")
            try:
                identified_name = scraper_api.identify_developer(self.sync_service.fetcher, portal, url)
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
        if dev_slug != "unknown" and not self.dm.get_developer(dev_slug):
            logger.info(f"Auto-creating developer profile for: {developer_name} ({dev_slug})")
            
            # Initialize portal mapping if we have enough info
            initial_pm = {"rp": None, "oto": None, "to": None}
            if portal == "rp" and vendor_id:
                initial_pm["rp"] = {"id": str(vendor_id)}
            elif portal == "to" and vendor_id:
                initial_pm["to"] = {"agency_id": str(vendor_id)}
            elif portal == "oto" and vendor_id:
                initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}

            self.dm.create_developer_file({
                "developer_slug": dev_slug, 
                "name": developer_name,
                "portal_mapping": initial_pm
            })

        return dev_slug, developer_name, inv_slug_from_url

    def backfill_developer_mapping(self, system_id, new_unified):
        """Backfills developer ID into portal_mapping if missing."""
        if not self.identity:
            return
            
        resources = self.identity.get_investment_resources(system_id)
        if not resources: return
        
        slug = resources["metadata"].get("slug") or ""
        slug_parts = slug.split("/") if "/" in slug else ["unknown", "unknown"]
        dev_slug = slug_parts[0]
        
        dev_record = self.dm.get_developer(dev_slug)
        if not dev_record:
            return

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
            self.dm.create_developer_file(dev_record)
            logger.info(f"Backfilled developer ID into portal_mapping for {dev_slug}")
