import json
import logging
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Tuple

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.services.amenity_scorer import suggest_udogodnienia
from python_worker.services.image_resolver import resolve_images
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.developer_index import load as load_dev_index

logger = logging.getLogger(__name__)

class InvestmentLoaderService:
    """Service for loading and transforming investment data for the UI and other services."""
    def __init__(
        self, 
        identity_resolver: Optional[InvestmentIdentityResolver] = None,
        developer_manager: Optional[Any] = None,  # Wstrzyknij menedżera deweloperów
        investment_repository: Optional[Any] = None,  # Wstrzyknij repozytorium
        data_dir: Optional[Path] = None,
        public_usi_dir: Optional[Path] = None
    ) -> None:
        self.data_dir = Path(data_dir or USI_DATA_DIR)
        self.public_usi_dir = Path(public_usi_dir or PUBLIC_USI_DIR)
        self.identity = identity_resolver or InvestmentIdentityResolver(self.data_dir, self.public_usi_dir)
        self._dev_manager = developer_manager
        self._repo = investment_repository
        self._dev_index = None

    def _extract_location_data(self, usi_data: Dict) -> Tuple[str, str, str, List[float]]:
        """Extracts and normalizes location information (address, city, district, coords)."""
        loc = usi_data.get("location", {})
        coords = loc.get("coords")
        lat = coords[0] if coords and len(coords) > 0 else None
        lng = coords[1] if coords and len(coords) > 1 else None
        
        address = loc.get("address") or ""
        city = loc.get("city")
        if not city and address:
            first_part = address.split(",")[0].strip()
            if first_part and not first_part.lower().startswith(("ul.", "al.", "os.", "pl.")):
                city = first_part
        district = loc.get("district")
        if not district:
            parts = [p.strip() for p in address.split(",")]
            district = parts[-1] if len(parts) >= 2 else ""
            
        return address, city, district, [lat, lng]

    def _resolve_source_data(self, usi_data: Dict) -> Tuple[str, str, List[Dict]]:
        """Determines the primary source and gathers all available source links."""
        sources = usi_data.get("sources", {})
        
        # Ustala główny portal prezentacji na podstawie hierarchii ważności
        source = "RP"
        if any(k.startswith("rp") for k in sources): source = "RP"
        elif any(k.startswith("oto") for k in sources): source = "OTO"
        elif any(k.startswith("to") for k in sources): source = "TO"
        
        source_links = []
        website = usi_data.get("website", "")
        
        for k, src_info in sources.items():
            urls = []
            
            if isinstance(src_info, str):
                urls = [src_info]
            elif isinstance(src_info, list):
                urls = src_info
            elif isinstance(src_info, dict):
                u = src_info.get("url")
                if isinstance(u, list):
                    urls.extend(u)
                elif isinstance(u, str):
                    urls.append(u)
            
            # Fallback dla starszych rekordów, które miały url w website zamiast w sources
            if not urls and website:
                if k.startswith("rp") and "rynekpierwotny" in website:
                    urls.append(website)
                elif k.startswith("oto") and "otodom" in website:
                    urls.append(website)
                elif k.startswith("to") and "tabelaofert" in website:
                    urls.append(website)
                    
            for u in urls:
                if not u: continue
                if k.startswith("rp"):
                    source_links.append({"source": "RP", "url": u})
                elif k.startswith("oto"):
                    source_links.append({"source": "OTO", "url": u})
                elif k.startswith("to"):
                    source_links.append({"source": "TO", "url": u})
        
        source_url = source_links[0]["url"] if source_links else ""
        return source, source_url, source_links

    def _load_master_data(self, usi_data: Dict, inv_dir: Path) -> Tuple[Optional[str], List, Optional[str]]:
        """Loads data from master investment files if the investment is merged."""
        master_id = usi_data.get("master_id")
        merged_from = []
        master_usi_inv_id = None
        if master_id:
            # Zapytanie kierowane do wstrzykniętego repozytorium
            if not self._repo:
                from python_worker.investment_repository import InvestmentRepository
                self._repo = InvestmentRepository(self.identity, self.data_dir)
            merged_from, master_usi_inv_id = self._repo.get_master_data(master_id, inv_dir)
        return master_id, merged_from, master_usi_inv_id

    def _resolve_usi_dev_id(self, usi_data: Dict) -> Optional[str]:
        """Resolves the developer's USI ID by matching portal identifiers against the developer index."""
        if usi_data.get("usi_dev_id"):
            return usi_data.get("usi_dev_id")
            
        if not self._dev_manager:
            from python_worker.developer_manager import DeveloperManager
            self._dev_manager = DeveloperManager(self.data_dir, self.data_dir.parent / "USIdev")
            
        sources = usi_data.get("sources", {})
        for portal, pdata in sources.items():
            pid = pdata.get("vendor_id") or pdata.get("agency_id") or pdata.get("developer_id")
            if not pid: 
                continue
            
            dev_record = self._dev_manager.find_developer_by_id(portal, str(pid))
            if dev_record:
                return dev_record.get("usi_dev_id")
        return None

    def load_investment(
        self,
        system_id: Optional[str] = None,
        usi_file: Optional[Path] = None,
        fast_index: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Unified loader for investment data.
        - IM-XXXX: ładuje bezpośrednio z USImaster/ (self-contained, zero agregacji)
        - INV-XXXXX z master_id: przekierowuje do mastera
        - INV-XXXXX bez master_id: standardowy ładunek z USIdata/
        """
        start_t = time.time()

        if not usi_file and not system_id:
            logger.error("load_investment: Neither system_id nor usi_file provided.")
            return None

        # IM-XXXX: bezpośrednio z USImaster/
        if system_id and system_id.startswith("IM-") and not usi_file:
            resources = self.identity.get_investment_resources(system_id)
            if not resources:
                logger.error(f"load_investment: Master {system_id} not found.")
                return None
            usi_file = resources["files"].get("anchor")
            if not usi_file or not usi_file.exists():
                logger.error(f"load_investment: Master file missing for {system_id}.")
                return None

        resources = None
        inv_dir = None
        dev_slug = None
        inv_slug = None

        if not usi_file and system_id:
            resources = self.identity.get_investment_resources(system_id)
            if resources:
                usi_file = resources["files"].get("anchor")
                metadata = resources["metadata"]
                dev_slug = metadata.get("developer_slug") or "unknown"
                inv_slug = metadata.get("investment_slug") or "unknown"
                inv_dir = resources["base_dir"]
            else:
                logger.error(f"load_investment: Could not resolve resources for ID {system_id}.")
                return None

        if not usi_file or not usi_file.exists():
            logger.error(f"load_investment: Anchor file not found for ID {system_id or 'unknown'}.")
            return None

        if not inv_dir:
            inv_dir = usi_file.parent
            if inv_dir.name == "USImaster":
                inv_slug = system_id or usi_file.stem.replace("inv_master_", "").replace("usi_", "")
                dev_slug = "USImaster"
            else:
                inv_slug = inv_dir.name
                dev_slug = inv_dir.parent.name

        try:
            usi = json.loads(usi_file.read_text(encoding="utf-8"))

            # INV-XXXXX z master_id — przekieruj ładowanie do mastera
            master_id_in_file = usi.get("master_id")
            if master_id_in_file and system_id and not system_id.startswith("IM-"):
                logger.debug(f"Redirecting {system_id} → master {master_id_in_file}")
                return self.load_investment(system_id=master_id_in_file, fast_index=fast_index)

            if resources and not usi.get("usi_inv_id"):
                usi["usi_inv_id"] = resources["id"]

            # Dla masterów: usi_inv_id = master_id
            if not usi.get("usi_inv_id") and usi.get("master_id"):
                usi["usi_inv_id"] = usi["master_id"]

            if not usi.get("portal") or not usi.get("portal_id"):
                if resources and "metadata" in resources:
                    usi.setdefault("portal", resources["metadata"].get("portal"))
                    usi.setdefault("portal_id", resources["metadata"].get("portal_id"))
                else:
                    sources = usi.get("sources", {})
                    for p in ("rp", "oto", "to"):
                        if p in sources and sources[p].get("id"):
                            usi.setdefault("portal", p)
                            usi.setdefault("portal_id", str(sources[p]["id"]))
                            break

            if not usi.get("usi_dev_id"):
                usi["usi_dev_id"] = self._resolve_usi_dev_id(usi)
        except Exception as e:
            logger.error(f"load_investment: JSON error in {usi_file}: {e}")
            return None

        images = []
        try:
            deleted_paths = set()
            if inv_dir:
                deletion_file = inv_dir / "deletion_list.json"
                if deletion_file.exists():
                    with open(deletion_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, dict):
                            deleted_paths = set(data.get("paths", []))
                        elif isinstance(data, list):
                            deleted_paths = set(data)
            
            images = resolve_images(usi, inv_dir=inv_dir, public_usi_dir=self.public_usi_dir, fast_index=fast_index, deleted_paths=deleted_paths)
        except Exception as e:
            logger.error(f"Failed to resolve images for {system_id}: {e}")
            
        duration = (time.time() - start_t) * 1000
        if not fast_index:
            logger.info(f"load_investment: Loaded {system_id or usi_file.name} in {duration:.1f}ms")

        am_data = usi.get("amenities", {})
        display_amenities = []
        
        # Pancerne sprawdzenie typu i struktury danych wejściowych
        if isinstance(am_data, dict):
            display_amenities = am_data.get("labels", [])
        elif isinstance(am_data, list):
            display_amenities = am_data
        elif am_data is None:
            display_amenities = []
            
        if not display_amenities and usi.get("amenities_matched"):
            display_amenities = [m["label"] for m in usi.get("amenities_matched")]

        address, city, district, coords = self._extract_location_data(usi)

        # Members i master_id — bezpośrednio z pliku (dla IM-XXXX już zagregowane)
        master_id = usi.get("master_id")
        raw_members = usi.get("members", [])
        # Wzbogać members o name/portal z indeksu RAM
        merged_from = []
        if master_id and raw_members:
            from python_worker.investment_index import get_entry_by_id
            for m in raw_members:
                uid = m.get("usi_inv_id") if isinstance(m, dict) else m
                if not uid:
                    continue
                entry = get_entry_by_id(uid)
                merged_from.append({
                    "usi_inv_id": uid,
                    "name": (entry or {}).get("name") or uid,
                    "portal": (entry or {}).get("source") or (entry or {}).get("portal"),
                    "investment_slug": (entry or {}).get("investment_slug"),
                })
        master_usi_inv_id = master_id  # master_id IS the canonical ID

        # Dla masterów i samodzielnych inwestycji: zdjęcia bezpośrednio z pliku
        # (nie ma potrzeby agregacji — master ma już image_paths ze wszystkich members)

        source, source_url, source_links = self._resolve_source_data(usi)
        ratings_data = usi.get("ratings", {})

        base_dir_rel = ""
        if resources and resources.get("base_dir"):
            try:
                base_dir_rel = str(resources["base_dir"].relative_to(self.data_dir.parent.parent))
            except ValueError:
                base_dir_rel = str(resources["base_dir"])
        else:
            if inv_dir and inv_dir.name == "USImaster":
                base_dir_rel = "Public/USImaster"
            else:
                base_dir_rel = f"Public/USIdata/{dev_slug}/{inv_slug}"
            
        inv_id_canonical = system_id or usi.get("usi_inv_id") or usi.get("master_id")
        if not inv_id_canonical:
            raise ValueError(f"Krytyczny brak identyfikatora strukturalnego w pliku {usi_file}")
            
        # Wyszukanie linku do oficjalnej strony WWW w strukturze JSON
        official_website = usi.get("website") or usi.get("specifications", {}).get("website") or ""
        if not official_website and isinstance(usi.get("sources"), dict):
            # Fallback na poszukiwanie w danych źródłowych dewelopera/portalu, jeśli skraper tam go wrzucił
            for src_data in usi["sources"].values():
                if isinstance(src_data, dict) and src_data.get("developer_website"):
                    official_website = src_data["developer_website"]
                    break

        usi_status = usi.get("status", "Brak")
        if usi_status not in ["Brak", "AI", "Wstępna", "Poszerzona", "Pełna", "Aktualizacja", "Ukończona", "Niedostateczne dane"]:
            usi_status = "Brak"
                
        base_data = {
            "slug": f"{dev_slug}/{inv_slug}",
            "developer_slug": dev_slug,
            "investment_slug": inv_slug,
            "name": usi.get("name", inv_slug.title()),
            "developer": usi.get("developer", dev_slug.title()),
            "address": address,
            "city": city,
            "district": district,
            "source": source,
            "source_url": source_url,
            "source_links": source_links,
            "price_avg": usi.get("financials", {}).get("price_avg") or 0,
            "price_min": usi.get("financials", {}).get("price_min"),
            "price_max": usi.get("financials", {}).get("price_max"),
            "price_m2_min": usi.get("financials", {}).get("price_m2_min"),
            "price_m2_max": usi.get("financials", {}).get("price_m2_max"),
            "rent_price_min": usi.get("financials", {}).get("rent_price_min"),
            "rent_price_max": usi.get("financials", {}).get("rent_price_max"),
            "units": usi.get("specifications", {}).get("units_count") or 0,
            "delivery": usi.get("specifications", {}).get("delivery_date") or "—",
            "segment": usi.get("specifications", {}).get("segment"),
            "ceiling_height_min": usi.get("specifications", {}).get("ceiling_height_min"),
            "ceiling_height_max": usi.get("specifications", {}).get("ceiling_height_max"),
            "specifications": usi.get("specifications", {}),
            "status": usi_status,
            "amenities": display_amenities,
            "amenities_score": usi.get("amenities_score", 0),
            "amenities_matched": usi.get("amenities_matched", []),
            "suggested_udogodnienia": usi.get("suggested_udogodnienia", []),
            "coords": coords,
            "photos": images,
            "image_urls": usi.get("image_urls", []),
            "images_count": usi.get("images_count", len(images)),
            "portal": usi.get("portal"),
            "portal_id": usi.get("portal_id"),
            "id": inv_id_canonical,
            "usi_inv_id": usi.get("usi_inv_id"),
            "usi_dev_id": usi.get("usi_dev_id"),
            "reviewed": usi.get("reviewed", False),
            "ratings": ratings_data,
            "comment": ratings_data.get("komentarz", ""),
            "photos_to_delete": usi.get("photos_to_delete", 0),
            "folder_path": base_dir_rel,
            "last_updated_ts": usi_file.stat().st_mtime if usi_file else None,
            "website": official_website,
            "sources": usi.get("sources", {}),
            "master_id": master_id,
            "master_usi_inv_id": master_usi_inv_id,
            "suggestions": usi.get("suggestions", []),
            "merged_from": merged_from,
        }
        
        if not fast_index and coords and coords[0]:
            from python_worker import investment_index
            inv_id_val = system_id or usi.get("master_id") or usi.get("usi_inv_id")
            base_data["nearby_investments"] = investment_index.get_nearby_investments(inv_id_val, coords)
        else:
            base_data["nearby_investments"] = []

        if resources:
            files_dict = {}
            for key, val in resources.get("files", {}).items():
                if val is None: 
                    continue
                if isinstance(val, list): 
                    files_dict[key] = [str(p) for p in val]
                else: 
                    files_dict[key] = str(val)
            
            base_data["resources"] = {
                "images_dir": str(resources["images_dir"]) if resources.get("images_dir") else None,
                "files": files_dict
            }

        return base_data

_shared_loader: Optional[InvestmentLoaderService] = None

def get_shared_loader(data_dir=None, public_usi_dir=None) -> InvestmentLoaderService:
    """Returns or creates a shared InvestmentLoaderService instance."""
    global _shared_loader
    if _shared_loader is None or data_dir or public_usi_dir:
        _shared_loader = InvestmentLoaderService(data_dir=data_dir, public_usi_dir=public_usi_dir)
    return _shared_loader

def load_investment(
    system_id: Optional[str] = None, 
    usi_file: Optional[Path] = None, 
    data_dir: Optional[Path] = None, 
    public_usi_dir: Optional[Path] = None, 
    fast_index: bool = True, 
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Legacy compatibility wrapper for InvestmentLoaderService.load_investment."""
    loader = get_shared_loader(data_dir=data_dir, public_usi_dir=public_usi_dir)
    return loader.load_investment(system_id=system_id, usi_file=usi_file, fast_index=fast_index)
