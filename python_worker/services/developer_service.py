import json
import logging
from pathlib import Path
from datetime import datetime

from python_worker.config import get_shared_config, get_shared_fetcher, get_shared_scraper_gateway
from python_worker.developer_manager import DeveloperManager
from python_worker.api.utils import now_utc, to_iso
from python_worker.services.matching_service import MatchingService

logger = logging.getLogger(__name__)

class DeveloperService:
    def __init__(self, data_dir: Path, dev_dir: Path, scraper_gateway=None):
        self.data_dir = data_dir
        self.dev_dir = dev_dir
        self.dm = DeveloperManager(data_dir, dev_dir)
        self.gateway = scraper_gateway or get_shared_scraper_gateway()

    def get_developer_enriched(self, usi_dev_id: str) -> dict:
        """Aggregates all developer data including investments, logs, maintenance and merged members."""
        dev = self.dm.get_developer_by_id(usi_dev_id)
        if not dev:
            return None

        target_id = dev.get("usi_dev_id")
        from python_worker.services.investment_service import InvestmentService
        inv_service = InvestmentService(data_dir=self.data_dir)
        all_invs = inv_service.list_investments_filtered()
        
        base_invs = []
        invs_by_dev_id = {}
        
        # MANDAT ID-ONLY: Inwestycje przypisujemy WYŁĄCZNIE po usi_dev_id.
        target_pm = dev.get("portal_mapping", {})
        
        for i in all_invs:
            did = i.get("usi_dev_id")
            is_match = False
            
            if did:
                s_did = str(did)
                invs_by_dev_id.setdefault(s_did, []).append(i)
                if s_did == str(target_id):
                    is_match = True
            
            if not is_match and MatchingService.is_match(i, target_pm):
                is_match = True
                
            if is_match:
                base_invs.append(i)
                
        # Ładowanie historii zdarzeń
        events = []
        res_info = self.dm.get_developer_resources(usi_dev_id)
        if res_info and "files" in res_info and res_info["files"].get("logs"):
            log_files = res_info["files"]["logs"]
            if log_files:
                log_path = Path(log_files[0])
                if log_path.exists():
                    try:
                        with open(log_path, "r", encoding="utf-8") as lf:
                            for line in lf:
                                if line.strip():
                                    events.append(json.loads(line.strip()))
                    except Exception:
                        pass
        dev["events"] = sorted(events, key=lambda x: x.get("at", ""), reverse=True)

        # Maintenance info
        crawler = dev.setdefault("crawler", {})
        maintenance_score = self.get_maintenance_overdue_score(dev)
        crawler["last_visit"] = dev.get("last_maintenance")
        crawler["last_new_count"] = dev.get("new_since_review", 0)
        crawler["next_visit"] = "Wymaga uwagi" if maintenance_score > 500 else "Zintegrowany"
        dev["maintenance_overdue_score"] = maintenance_score

        # Merged members
        base_pm = (dev.get("original_portal_mapping") or dev.get("portal_mapping") or {}).copy()
        valid_members = []
        
        for member in dev.get("merged_from", []):
            child_id = member.get("usi_dev_id")
            child_dev = self.dm.get_developer_by_id(child_id) if child_id else None
            if not child_dev or str(child_dev.get("usi_dev_id")) == str(dev.get("usi_dev_id")):
                continue
                
            member["slug"] = child_dev.get("developer_slug")
            child_pm = (child_dev.get("original_portal_mapping") or child_dev.get("portal_mapping") or {}).copy()
            member["_pm"] = child_pm
            
            child_invs = list(invs_by_dev_id.get(str(child_id), []))
            for i in all_invs:
                if MatchingService.is_match(i, child_pm):
                    iid = i.get("usi_inv_id")
                    if iid and not any(ci.get("usi_inv_id") == iid for ci in child_invs):
                        child_invs.append(i)
            
            member["_invs"] = child_invs
            valid_members.append(member)

        # Base record
        dev["base_record"] = {
            "name": dev.get("name"),
            "developer_slug": dev.get("developer_slug"),
            "usi_dev_id": dev.get("usi_dev_id"),
            "portal_mapping": base_pm,
            "investments_count": len(base_invs),
            "inv_list": [
                {"name": inv.get("name", inv.get("usi_inv_id", "")), "id": inv.get("usi_inv_id", "")}
                for inv in base_invs[:10]
            ]
        }

        final_members = []
        investments = list(base_invs)
        existing_inv_ids = {i.get("usi_inv_id") for i in base_invs if i.get("usi_inv_id")}
        aggregated_pm = base_pm.copy()
        
        for m in valid_members:
            m["investments_count"] = len(m["_invs"])
            m["inv_list"] = [
                {"name": inv.get("name", inv.get("usi_inv_id", "")), "id": inv.get("usi_inv_id", "")}
                for inv in m["_invs"][:10]
            ]
            m["portal_mapping"] = m["_pm"]
            m["original_portal_mapping"] = m["_pm"] 
            
            for p, pdata in m["_pm"].items():
                if not aggregated_pm.get(p) and pdata:
                    aggregated_pm[p] = pdata
            
            for inv in m["_invs"]:
                iid = inv.get("usi_inv_id")
                if iid and iid not in existing_inv_ids:
                    investments.append(inv)
                    existing_inv_ids.add(iid)
            
            m.pop("_pm", None); m.pop("_invs", None)
            final_members.append(m)

        dev["merged_from"] = final_members
        
        # Suggestions (Reverse Lookup)
        suggestions_dict = {str(s.get("usi_dev_id") or s.get("target_id")): s for s in dev.get("suggestions", []) if (s.get("usi_dev_id") or s.get("target_id"))}
        merged_ids = {str(m.get("usi_dev_id")) for m in final_members if m.get("usi_dev_id")}

        all_devs_cached = self.dm.list_developers() or []
        for other_dev in all_devs_cached:
            other_id = other_dev.get("usi_dev_id")
            if not other_id or str(other_id) == str(target_id):
                continue
                
            for other_sug in other_dev.get("suggestions", []):
                if str(other_sug.get("usi_dev_id") or other_sug.get("target_id")) == str(target_id) and other_sug.get("score", 0) >= 0.75:
                    if str(other_id) not in suggestions_dict:
                        suggestions_dict[str(other_id)] = {
                            "usi_dev_id": other_id,
                            "target_id": other_id,
                            "developer_slug": other_dev.get("developer_slug"),
                            "reason": f"[Relacja zwrotna] {other_sug.get('reason')}",
                            "score": other_sug.get("score", 0.0)
                        }

        valid_suggestions = []
        for s_id, s in suggestions_dict.items():
            if s_id in merged_ids or s_id == str(target_id):
                continue

            s_dev = self.dm.get_developer_by_id(s_id)
            if s_dev:
                valid_suggestions.append({
                    "usi_dev_id": s_id,
                    "target_id": s_id,
                    "developer_slug": s_dev.get("developer_slug", "unknown"),
                    "name": s_dev.get("name", s_id),
                    "reason": s.get("reason", "Podobieństwo systemowe"),
                    "score": s.get("score", 1.0),
                    "portal_mapping": s_dev.get("portal_mapping", {}),
                    "website": s_dev.get("website"),
                    "investments_count": len(invs_by_dev_id.get(s_id, []))
                })

        dev["suggestions"] = valid_suggestions
        dev["investments"] = investments
        dev["investments_count"] = len(investments)
        dev["portal_mapping"] = aggregated_pm
        
        return dev

    def download_dev_profile_raw(self, portal: str, identifier: str, dev_slug: str) -> Path | None:
        """
        Pobiera surowy profil dewelopera oraz jego logo delegując zadanie do usi-scrapers przez bramę.
        Zgodnie z ID-only identyfikacja opiera się wyłącznie o portal_id.
        """
        try:
            portal_prefix = self.gateway.resolve_prefix(portal)
            
            # Wywołanie przez bramę
            res = self.gateway.download_raw_dev(portal_prefix, str(identifier))
            if not res or res.get("status") != "success":
                msg = res.get("message", "Unknown error") if res else "No response"
                logger.error(f"usi-scrapers failed to download dev profile for {portal_prefix}/{identifier}: {msg}")
                return None

            # Zwrócenie ścieżki do pliku zweryfikowanej zgodnie z CANONICAL.md
            resolved_slug = res.get("dev_slug") or dev_slug
            target_path = self.dev_dir / resolved_slug / f"raw_{portal_prefix}_{identifier}.json"
            
            if target_path.exists():
                return target_path
            return None
            
        except Exception as e:
            logger.error(f"Failed to download developer profile for {portal}/{dev_slug}: {e}")
            return None

    def update_developer_profile(self, usi_dev_id: str) -> bool:
        """
        Odświeża surowe zrzuty profili ze wszystkich zmapowanych portali i przebudowuje Level 2.
        """
        dev_data = self.dm.get_developer_by_id(usi_dev_id)
        if not dev_data:
            logger.warning(f"Developer metadata not found for {usi_dev_id}, cannot update.")
            return False

        dev_slug = dev_data.get("developer_slug")
        mapping = dev_data.get("portal_mapping", {})
        updated = False

        # Odświeżanie zmapowanych portali
        for portal in ("rp", "oto", "to"):
            if p_map := mapping.get(portal):
                if pid := p_map.get("id") or p_map.get("agency_id"):
                    logger.info(f"Updating {portal} profile for {dev_slug} (ID: {pid})")
                    if self.download_dev_profile_raw(portal, str(pid), dev_slug):
                        updated = True

        # Kompilacja warstwy Level 2 (usi_dev_*.json) na bazie nowych plików raw
        if updated:
            from python_worker.init_developers import _build_dev_from_raws
            dev_subdir = self.dev_dir / dev_slug
            if dev_subdir.exists():
                _build_dev_from_raws(dev_subdir, dev_slug, dev_data.get("name"), self.dm)
            
        return updated

    def get_maintenance_overdue_score(self, dev_data: dict) -> float:
        """
        Wylicza priorytet konserwacji opierając się ściśle o wzorce nazw z CANONICAL.md.
        """
        score = 0.0
        now = now_utc()
        
        if not dev_data.get("logo"):
            score += 1000.0
            
        pm = dev_data.get("portal_mapping", {})
        dev_slug = dev_data.get("developer_slug")
        dev_subdir = self.dev_dir / dev_slug
        
        for portal in ("rp", "oto", "to"):
            if portal_info := pm.get(portal):
                # Ekstrakcja portal_id zamiast używania deweloperskiego sluga w nazwie pliku
                portal_id = portal_info.get("id") or portal_info.get("agency_id")
                if portal_id:
                    raw_file = dev_subdir / f"raw_{portal}_{portal_id}.json"
                    if not raw_file.exists():
                        score += 500.0
        
        last_maint_str = dev_data.get("last_maintenance")
        if not last_maint_str:
            score += 100.0
        else:
            try:
                last_maint = datetime.fromisoformat(last_maint_str.replace("Z", "+00:00"))
                overdue_days = (now - last_maint).days
                if overdue_days > 90:
                    score += overdue_days
            except ValueError:
                score += 100.0
                
        return score

    def record_maintenance(self, dev_slug: str, success: bool):
        """Zapisuje ślad rewizyjny konserwacji dewelopera na dysku."""
        dev_file = None
        subdir = self.dev_dir / dev_slug
        if subdir.is_dir():
            hits = sorted(subdir.glob(f"usi_dev_*_{dev_slug}.json"))
            if hits:
                dev_file = hits[0]
        
        if not dev_file:
            return

        try:
            data = json.loads(dev_file.read_text(encoding="utf-8"))
            data["last_maintenance"] = to_iso(now_utc())
            data["maintenance_success"] = success
            self.dm.create_developer_file(data)
            
            from python_worker.logger_utils import log_to_dev_log
            status = "sukces" if success else "błąd"
            log_to_dev_log(dev_slug, f"Konserwacja danych zakończona ({status}).")
        except Exception as e:
            logger.error(f"record_maintenance({dev_slug}) failed: {e}")
