import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MatchingService:
    """Service for portal-to-investment matching logic."""

    @staticmethod
    def is_match(inv: Dict[str, Any], pm: Dict[str, Any]) -> bool:
        """
        Checks if an investment record matches any portal identifier in the given portal mapping.
        
        Mandat ID-only: This logic compares technical portal IDs from the investment sources 
        against the developer's registered portal identifiers.
        """
        if not inv or not pm:
            return False
            
        sources = inv.get("sources", {})
        if not sources:
            return False

        # 1. RynekPierwotny check
        if pm.get("rp") and pm["rp"].get("id"):
            rp_id = str(pm["rp"]["id"])
            if "rp" in sources and str(sources["rp"].get("vendor_id") or sources["rp"].get("id")) == rp_id:
                return True

        # 2. Otodom check (supports multiple agency IDs)
        if pm.get("oto"):
            oto_mapping = pm["oto"]
            # Extract all known agency IDs for this developer
            agency_ids = set()
            if oto_mapping.get("agency_id"):
                agency_ids.add(str(oto_mapping["agency_id"]))
            if oto_mapping.get("agency_ids"):
                for aid in oto_mapping["agency_ids"]:
                    if aid: agency_ids.add(str(aid))
            
            if agency_ids and "oto" in sources:
                inv_agency_id = str(sources["oto"].get("agency_id") or sources["oto"].get("id"))
                if inv_agency_id in agency_ids:
                    return True

        # 3. TabelaOfert check
        if pm.get("to") and pm["to"].get("agency_id"):
            to_id = str(pm["to"]["agency_id"])
            if "to" in sources and str(sources["to"].get("agency_id") or sources["to"].get("id")) == to_id:
                return True

        return False
