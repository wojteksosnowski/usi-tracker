import logging
from typing import Tuple, Optional, Dict, Any
from python_worker.url_parser import parse_url

logger = logging.getLogger(__name__)

class DeveloperResolver:
    def __init__(self, developer_manager: Any, identity_resolver: Optional[Any] = None) -> None:
        self.dm = developer_manager
        self.identity = identity_resolver

    def resolve_developer_for_registration(
        self, 
        portal: str, 
        developer_name: Optional[str], 
        url: Optional[str], 
        vendor_id: Optional[str], 
        force_dev_slug: Optional[str]
    ) -> Tuple[str, str, Optional[str]]:
        """
        Deterministycznie rozwiązuje tożsamość dewelopera bez odwołań do crawlerów/scraperów.
        Zwraca: (dev_slug, developer_name, inv_slug_from_url)
        """
        developer_record: Optional[Dict[str, Any]] = None
        dev_slug: Optional[str] = force_dev_slug
        inv_slug_from_url: Optional[str] = None

        # PRIORITY 1: Identyfikacja po Vendor ID
        if not dev_slug and vendor_id:
            developer_record = self.dm.find_developer_by_id(portal, str(vendor_id))
            if developer_record:
                dev_slug = developer_record["developer_slug"]
                developer_name = developer_record["name"]
                logger.info(f"Found developer by ID {vendor_id} ({portal}): {developer_name} ({dev_slug})")

        # PRIORITY 2: Ekstrakcja Canonical Slug z URL za pomocą wbudowanego parsera
        if not dev_slug and not developer_record and url:
            parsed = parse_url(url)
            if parsed.get("investment_slug") and parsed["investment_slug"] != "unknown":
                inv_slug_from_url = parsed["investment_slug"]
            if parsed.get("developer_slug") and parsed["developer_slug"] != "unknown":
                is_unknown = not developer_name or developer_name.lower() in ("nieznany deweloper", "unknown", "nieznany-deweloper")
                if is_unknown:
                    developer_name = parsed["developer_slug"].replace("-", " ").title()

        if not dev_slug:
            if not developer_record:
                dev_slug = "unknown"
                if developer_name and developer_name.lower() not in ("nieznany deweloper", "unknown", "nieznany-deweloper"):
                    logger.warning(f"No USI record found by ID for developer '{developer_name}' - placing in 'unknown' folder")
            else:
                dev_slug = developer_record["developer_slug"]
        
        # Automatyczne tworzenie profilu dewelopera tylko dla zidentyfikowanego sluga
        if dev_slug != "unknown" and not self.dm.get_developer(dev_slug):
            logger.info(f"Auto-creating developer profile for: {developer_name} ({dev_slug})")
            
            initial_pm: Dict[str, Any] = {"rp": None, "oto": None, "to": None}
            if portal == "rp" and vendor_id:
                initial_pm["rp"] = {"id": str(vendor_id)}
            elif portal == "to" and vendor_id:
                initial_pm["to"] = {"agency_id": str(vendor_id)}
            elif portal == "oto" and vendor_id:
                initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}

            self.dm.create_developer_file({
                "developer_slug": dev_slug, 
                "name": developer_name or dev_slug.replace("-", " ").title(),
                "portal_mapping": initial_pm
            })

        return dev_slug, developer_name or "Nieznany Deweloper", inv_slug_from_url

    def backfill_developer_mapping(self, system_id: str, new_unified: Dict[str, Any]) -> None:
        """Uzupełnia portal_mapping w plikach deweloperów na podstawie ujednoliconych danych inwestycji."""
        if not self.identity:
            return
            
        resources = self.identity.get_investment_resources(system_id)
        if not resources: 
            return
        
        m = resources["metadata"]
        dev_slug = m.get("developer_slug")
        if not dev_slug: 
            return
        
        dev_record = self.dm.get_developer(dev_slug)
        if not dev_record:
            return

        needs_update = False
        pm = dev_record.setdefault("portal_mapping", {"rp": None, "oto": None, "to": None})
        new_src = new_unified.get("sources", {})
        
        # Walidacja źródła RynekPierwotny
        rp_src = new_src.get("rp", {})
        if rp_src.get("vendor_id"):
            if not pm.get("rp"):
                pm["rp"] = {"id": rp_src["vendor_id"]}
                needs_update = True
            elif pm["rp"].get("id") != rp_src["vendor_id"]:
                if not pm["rp"].get("id"):
                    pm["rp"]["id"] = rp_src["vendor_id"]
                    needs_update = True
                    
        # Walidacja źródła Otodom
        oto_src = new_src.get("oto", {})
        if oto_src.get("agency_id"):
            if not pm.get("oto"):
                pm["oto"] = {"agency_id": oto_src["agency_id"], "agency_ids": [oto_src["agency_id"]]}
                needs_update = True
            else:
                aids = pm["oto"].setdefault("agency_ids", [])
                if oto_src["agency_id"] not in aids:
                    aids.append(oto_src["agency_id"])
                    pm["oto"]["agency_id"] = oto_src["agency_id"]
                    needs_update = True
                    
        # Walidacja źródła TabelatOfert
        to_src = new_src.get("to", {})
        if to_src and to_src.get("developer_id"):
            if not pm.get("to"):
                pm["to"] = {"agency_id": to_src["developer_id"]}
                needs_update = True
            elif not pm["to"].get("agency_id"):
                pm["to"]["agency_id"] = to_src["developer_id"]
                needs_update = True
                
        if needs_update:
            self.dm.create_developer_file(dev_record)
            logger.info(f"Backfilled developer ID into portal_mapping for {dev_slug}")
