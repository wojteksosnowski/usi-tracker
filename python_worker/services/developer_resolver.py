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
    ) -> Tuple[str, str, Optional[str], Optional[str]]:
        """
        Gwarantuje identyfikację wyłącznie po oryginalnym ID portalu.
        Slugi z URL służą wyłącznie do lokalizacji plików, nigdy do identyfikacji.
        Zwraca: (dev_slug, dev_name, inv_slug, usi_dev_id)
        """
        developer_record: Optional[Dict[str, Any]] = None
        dev_slug: Optional[str] = force_dev_slug
        inv_slug_from_url: Optional[str] = None
        usi_dev_id: Optional[str] = None

        # PARSOWANIE URL - wyłącznie do celów wyciągnięcia sluga inwestycji (struktura plików)
        if url:
            parsed = parse_url(url)
            if parsed.get("investment_slug") and parsed["investment_slug"] != "unknown":
                inv_slug_from_url = parsed["investment_slug"]

        # BEZWZGLĘDNY RYGOR: Identyfikacja wyłącznie po oryginalnym ID portalu
        if vendor_id:
            developer_record = self.dm.find_developer_by_id(portal, str(vendor_id))
            if developer_record:
                dev_slug = developer_record["developer_slug"]
                developer_name = developer_record["name"]
                usi_dev_id = developer_record["usi_dev_id"]
                logger.info(f"Zidentyfikowano dewelopera po ID {vendor_id} ({portal}): {developer_name} ({usi_dev_id})")
        else:
            # Brak oryginalnego ID portalu = brak możliwości bezpiecznej rejestracji/identyfikacji
            logger.error(f"Krytyczny brak oryginalnego ID portalu dla dewelopera '{developer_name}'. Rejestracja przerwana.")
            return "unknown", developer_name or "Nieznany Deweloper", inv_slug_from_url, None

        if not dev_slug:
            # Nie generujemy sluga z nazwy, nie zgadujemy. Jeśli rekord nie istnieje w indeksie po ID portalu,
            # ląduje w 'unknown' do czasu manualnego powiązania lub pełnego importu bazy deweloperów.
            dev_slug = "unknown"
            logger.warning(f"Brak rekordu USI dla ID {vendor_id} ({portal}) - przeniesienie do katalogu 'unknown'")
        
        # Automatyczne tworzenie profilu dewelopera TYLKO, gdy znamy poprawnego sluga dewelopera i mamy ID
        if dev_slug != "unknown" and not developer_record:
            logger.info(f"Auto-tworzenie profilu dewelopera dla ID: {vendor_id} ({portal})")
            
            initial_pm: Dict[str, Any] = {"rp": None, "oto": None, "to": None}
            if portal == "rp":
                initial_pm["rp"] = {"id": str(vendor_id)}
            elif portal == "oto":
                initial_pm["oto"] = {"agency_id": str(vendor_id), "agency_ids": [str(vendor_id)]}
            elif portal == "to":
                initial_pm["to"] = {"agency_id": str(vendor_id)}

            dev_file = self.dm.create_developer_file({
                "developer_slug": dev_slug, 
                "name": developer_name or dev_slug.replace("-", " ").title(),
                "portal_mapping": initial_pm
            })
            
            # Re-load to get assigned usi_dev_id
            if dev_file:
                try:
                    d = json.loads(dev_file.read_text())
                    usi_dev_id = d.get("usi_dev_id")
                except Exception: pass

        return dev_slug, developer_name or "Nieznany Deweloper", inv_slug_from_url, usi_dev_id

    def backfill_developer_mapping(self, system_id: str, new_unified: Dict[str, Any]) -> None:
        """Uzupełnia portal_mapping w plikach deweloperów na podstawie ujednoliconych danych inwestycji.
        MANDAT ID-ONLY: Identyfikacja dewelopera odbywa się WYŁĄCZNIE po technicznych ID portali.
        """
        if not self.identity:
            return
            
        sources = new_unified.get("sources", {})
        if not sources:
            return

        # 1. Znajdź dewelopera na podstawie któregokolwiek ID portalu z inwestycji
        target_dev = None
        from usi_scrapers import get_mapping

        for portal, pdata in sources.items():
            try:
                # Używamy ścieżki do ID dewelopera z konfiguracji biblioteki
                # (np. 'vendor_id' dla RP w sources inwestycji)
                pid = pdata.get("vendor_id") or pdata.get("agency_id") or pdata.get("developer_id")
                if pid:
                    target_dev = self.dm.find_developer_by_id(portal, str(pid))
                    if target_dev:
                        break
            except Exception: continue

        if not target_dev:
            return

        # Always inject usi_dev_id into investment data if found and missing
        if target_dev.get("usi_dev_id") and not new_unified.get("usi_dev_id"):
            new_unified["usi_dev_id"] = target_dev["usi_dev_id"]
            logger.info(f"Injected usi_dev_id {target_dev['usi_dev_id']} into investment {system_id}")

        # 2. Skoro mamy dewelopera, uzupełniamy jego mapowanie o pozostałe ID z tej inwestycji
        needs_update = False
        pm = target_dev.setdefault("portal_mapping", {"rp": None, "oto": None, "to": None})
        
        for portal, pdata in sources.items():
            pid = pdata.get("vendor_id") or pdata.get("agency_id") or pdata.get("developer_id")
            if not pid: continue
            
            clean_id = str(pid)
            if portal == "rp":
                if not pm.get("rp"):
                    pm["rp"] = {"id": clean_id}
                    needs_update = True
            elif portal == "oto":
                if not pm.get("oto"):
                    pm["oto"] = {"agency_id": clean_id, "agency_ids": [clean_id]}
                    needs_update = True
                else:
                    aids = pm["oto"].setdefault("agency_ids", [])
                    if clean_id not in aids:
                        aids.append(clean_id)
                        pm["oto"]["agency_id"] = clean_id
                        needs_update = True
            elif portal == "to":
                if not pm.get("to"):
                    pm["to"] = {"agency_id": clean_id}
                    needs_update = True

        if needs_update:
            self.dm.create_developer_file(target_dev)
            logger.info(f"Zaktualizowano portal_mapping dla {target_dev.get('usi_dev_id')} na podstawie inwestycji {system_id}")
