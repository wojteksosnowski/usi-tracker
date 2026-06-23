"""
investment_merger.py — Zarządzanie grupami inwestycji (Master Groups)

Architektura grupy (ID-only, płaska):
  - Każdy rekord usi_*.json może zawierać klucz "master_id" wskazujący na ID grupy.
  - Plik master ZAWSZE leży w Public/USImaster/inv_master_{IM-XXXX}.json
  - Struktura pliku master jest prosta i płaska:
      {
          "master_id": "IM-XXXX",
          "members": [
              {"usi_inv_id": "INV-AAAAA"},
              {"usi_inv_id": "INV-BBBBB"}
          ]
      }
  - BRAK primary_id, secondary_id, roli, slugów. Tylko ID.
  - Oceny propagowane są do WSZYSTKICH składowych grupy.
  - Merge i unmerge aktualizują tylko znane ID — zero rglob.
"""

import json
import logging
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from python_worker.config import USI_DATA_DIR, PUBLIC_USI_DIR
from python_worker.services.investment_identity import InvestmentIdentityResolver
from python_worker.logger_utils import log_to_processing_log

logger = logging.getLogger(__name__)

MASTER_FILE_PREFIX = "inv_master_"


def _atomic_write(path: Path, data: dict) -> None:
    """Atomowy zapis JSON — bezpieczny przy synchronizacji Dropbox."""
    content = json.dumps(data, indent=2, ensure_ascii=False)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _read_json(path: Path) -> Optional[dict]:
    if not path or not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"JSON read error {path}: {e}")
        return None


def _usi_master_dir() -> Path:
    """Zwraca bezwzględną ścieżkę do Public/USImaster/."""
    return Path(PUBLIC_USI_DIR).parent.parent / "Public" / "USImaster"


class InvestmentMerger:
    """
    Zarządza grupami inwestycji (wiele rekordów z różnych portali = jeden obiekt).
    Plik master: Public/USImaster/inv_master_{IM-XXXX}.json
    """

    def __init__(self, data_dir: Path = None, public_dir: Path = None):
        self.data_dir = data_dir or Path(USI_DATA_DIR)
        self.public_dir = public_dir or Path(PUBLIC_USI_DIR)
        self.identity = InvestmentIdentityResolver(self.data_dir, self.public_dir)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_resources(self, inv_id: str):
        res = self.identity.get_investment_resources(inv_id)
        if not res:
            logger.error(f"Cannot resolve resources for {inv_id}")
        return res

    def _find_index_entry(self, usi_inv_id: str) -> Optional[dict]:
        """Szybkie O(1) wyszukanie w gorącym indeksie RAM."""
        import python_worker.investment_index as inv_index
        return inv_index.get_entry_by_id(usi_inv_id)

    def _master_dir(self) -> Path:
        """Public/USImaster/ — jedyne miejsce przechowywania plików master."""
        d = _usi_master_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _master_path(self, master_id: str) -> Path:
        """Bezwzględna ścieżka do pliku master."""
        return self._master_dir() / f"{MASTER_FILE_PREFIX}{master_id}.json"

    def _load_master_file(self, master_id: str, primary_id: str = None) -> tuple[Optional[dict], Optional[Path]]:
        """
        Wczytuje plik master z USImaster/.
        Argument primary_id zachowany dla kompatybilności wstecznej — ignorowany.
        """
        path = self._master_path(master_id)
        data = _read_json(path)
        return data, path if data else None

    def _save_master(self, master_id: str, member_ids: list[str]) -> Path:
        """
        Buduje i zapisuje pełny rekord mastera w USImaster/.
        Agreguje dane wszystkich memberów — master jest self-contained.
        """
        seen = set()
        members = []
        for uid in member_ids:
            if uid and uid not in seen:
                seen.add(uid)
                members.append({"usi_inv_id": uid})

        # Agregacja danych z memberów
        master = {
            "usi_inv_id": master_id,
            "master_id": master_id,
            "members": members,
            "name": None,
            "developer": None,
            "location": {},
            "financials": {},
            "specifications": {},
            "sources": {},
            "image_paths": [],
            "ratings": {},
            "status": "Brak",
            "usi_dev_id": None,
            "amenities": {"labels": [], "raw_codes": []},
            "amenities_score": 0,
        }

        seen_images: set[str] = set()
        seen_amenities: set[str] = set()
        seen_amenity_labels: set[str] = set()
        seen_amenity_codes: set[str] = set()
        amenities_matched: list = []
        w_sums = {"price_min": 0.0, "price_max": 0.0, "price_m2_min": 0.0, "price_m2_max": 0.0}
        w_counts = {k: 0 for k in w_sums}
        delivery_dates: set[str] = set()

        # Preferuj dane z RP (portal hierarchia: rp > oto > to)
        portal_priority = {"rp": 0, "oto": 1, "to": 2}

        for uid in [m["usi_inv_id"] for m in members]:
            m_res = self._get_resources(uid)
            if not m_res:
                continue
            anchor = m_res["files"].get("anchor")
            if not anchor or not anchor.exists():
                continue
            try:
                d = json.loads(anchor.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Cannot read member {uid}: {e}")
                continue

            # Podstawowe pola — bierz jeśli brak lub z portalu wyżej w hierarchii
            d_portal = (d.get("portal") or "").lower()
            cur_portal = (master.get("_anchor_portal") or "zzz").lower()
            is_better_portal = portal_priority.get(d_portal, 99) < portal_priority.get(cur_portal, 99)

            if not master["name"] or is_better_portal:
                if d.get("name"):
                    master["name"] = d["name"]
                    master["_anchor_portal"] = d_portal

            if not master["developer"] or (is_better_portal and d.get("developer")):
                if d.get("developer") and d["developer"] != "Nieznany deweloper":
                    master["developer"] = d["developer"]

            if (not master["location"].get("city")) or is_better_portal:
                if d.get("location") and d["location"].get("city"):
                    master["location"] = d["location"]

            if not master["usi_dev_id"] and d.get("usi_dev_id"):
                master["usi_dev_id"] = d["usi_dev_id"]

            # Status — bierz najlepszy (nie-Brak)
            d_status = d.get("status") or d.get("ratings", {}).get("status") or "Brak"
            if master["status"] == "Brak" and d_status != "Brak":
                master["status"] = d_status

            # Segment — preferuj Polish string
            d_seg = d.get("specifications", {}).get("segment") or d.get("segment", "")
            cur_seg = master["specifications"].get("segment", "")
            if d_seg and (not cur_seg or cur_seg in ("apartments", "houses", "commercial")):
                master["specifications"]["segment"] = d_seg

            # Ceiling height
            d_spec = d.get("specifications", {})
            for hkey in ("ceiling_height_min", "ceiling_height_max", "units_count", "delivery_date"):
                if d_spec.get(hkey) and not master["specifications"].get(hkey):
                    master["specifications"][hkey] = d_spec[hkey]
            if d_spec.get("delivery_date") and d_spec["delivery_date"] != "—":
                delivery_dates.add(str(d_spec["delivery_date"]))

            # Units — max
            try:
                d_units = int(d_spec.get("units_count") or 0)
                cur_units = int(master["specifications"].get("units_count") or 0)
                master["specifications"]["units_count"] = max(cur_units, d_units)
            except (ValueError, TypeError):
                pass

            # Ratings — bierz jeśli własne puste
            d_rat = d.get("ratings", {})
            if d_rat and "Gwiazdki" in d_rat and "Gwiazdki" not in master["ratings"]:
                master["ratings"] = dict(d_rat)

            # Sources — merge
            for k, v in d.get("sources", {}).items():
                if k not in master["sources"]:
                    master["sources"][k] = v

            # Financials — średnia ważona, tylko >0
            d_fin = d.get("financials", {})
            d_units_w = int(d_spec.get("units_count") or 1)
            for key in w_sums:
                val = d_fin.get(key)
                if val is not None:
                    try:
                        fval = float(val)
                        if fval > 0:
                            w_sums[key] += fval * d_units_w
                            w_counts[key] += d_units_w
                    except (ValueError, TypeError):
                        pass

            # Amenities matched
            d_am = d.get("amenities_matched", [])
            for am in d_am:
                code = am.get("code") if isinstance(am, dict) else am
                if code and code not in seen_amenities:
                    seen_amenities.add(code)
                    amenities_matched.append(am)

            # Amenities
            d_am_obj = d.get("amenities", {})
            for label in d_am_obj.get("labels", []):
                if label not in seen_amenity_labels:
                    seen_amenity_labels.add(label)
                    master["amenities"]["labels"].append(label)
            for raw_code in d_am_obj.get("raw_codes", []):
                if raw_code not in seen_amenity_codes:
                    seen_amenity_codes.add(raw_code)
                    master["amenities"]["raw_codes"].append(raw_code)
            
            # Amenities score
            if "amenities_score" in d:
                master["amenities_score"] = max(master["amenities_score"], d["amenities_score"])

            # Images
            for img in d.get("image_paths", []):
                from pathlib import PurePath
                fname = PurePath(img).name
                if fname not in seen_images:
                    seen_images.add(fname)
                    master["image_paths"].append(img)

        # Finanse — zapisz wyniki agregacji
        for key in w_sums:
            if w_counts[key] > 0:
                master["financials"][key] = round(w_sums[key] / w_counts[key], 2)

        # Delivery date
        if delivery_dates:
            master["specifications"]["delivery_date"] = " / ".join(sorted(delivery_dates))

        master["amenities_matched"] = amenities_matched
        master.pop("_anchor_portal", None)

        path = self._master_path(master_id)
        _atomic_write(path, master)
        logger.info(f"Master saved: {path.name} → {[m['usi_inv_id'] for m in members]}")
        return path


    def _upsert_index(self, inv_id: str) -> None:
        """Aktualizuje gorący indeks RAM + dysk dla jednego rekordu. O(1), bez rglob."""
        import python_worker.investment_index as inv_index
        from python_worker.api.utils import _load_investment
        entry = _load_investment(system_id=inv_id, fast_index=True)
        if entry:
            entry.pop("image_urls", None)
            entry.pop("nearby_investments", None)
            inv_index.get_investment_index().add_or_update(inv_id, entry)

    def _invalidate_service_cache(self, inv_id: str) -> None:
        try:
            from python_worker.services.investment_service import investment_service
            investment_service.invalidate_cache(inv_id)
        except Exception as e:
            logger.debug(f"Cache invalidation skipped for {inv_id}: {e}")

    def get_group_members(self, inv_id: str) -> list[dict]:
        """
        Dla danego ID inwestycji zwraca listę wszystkich członków jej grupy.
        Jeśli inwestycja nie jest w grupie, zwraca pustą listę.
        """
        res = self._get_resources(inv_id)
        if not res:
            return []
        data = _read_json(res["files"].get("anchor"))
        if not data:
            return []
        master_id = data.get("master_id")
        if not master_id:
            return []

        master_data, _ = self._load_master_file(master_id)
        if not master_data:
            return []
        return master_data.get("members", [])

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def merge_by_id(self, target_id: str, source_id: str) -> bool:
        """
        Dołącza source_id do grupy wskazanej przez target_id (lub tworzy nową grupę).

        Reguły (płaska struktura):
        - Brak primary/secondary. Wszystkie dodane inwestycje są równe (members).
        - Jeśli target_id to IM-XXXX, dodaje source_id do tej grupy.
        - Jeśli target_id to INV-XXXX należące już do grupy, dodaje source_id do tej samej grupy.
        - Jeśli target_id to INV-XXXX bez grupy, tworzy nową grupę IM-XXXX dla obu.
        - Zapis atomowy dla każdego pliku.
        - Tylko upsert O(1) — zero rebuild().
        """
        if target_id == source_id:
            logger.error("Cannot merge investment into itself.")
            return False

        s_res = self._get_resources(source_id)
        if not s_res:
            return False

        s_file = s_res["files"].get("anchor")
        s_data = _read_json(s_file)
        if s_data is None:
            return False

        s_meta = s_res["metadata"]

        # --- Ustalanie docelowego master_id ---
        master_id = None
        target_dev_id = None
        target_ratings = {}

        if target_id.startswith("IM-"):
            master_id = target_id
            m_data, _ = self._load_master_file(master_id)
            if not m_data:
                logger.error(f"Target master {target_id} not found.")
                return False
            target_dev_id = m_data.get("usi_dev_id")
            target_ratings = m_data.get("ratings", {})
        else:
            t_res = self._get_resources(target_id)
            if not t_res:
                return False
            t_file = t_res["files"].get("anchor")
            t_data = _read_json(t_file)
            if t_data is None:
                return False
            
            master_id = t_data.get("master_id")
            if not master_id:
                # Tworzymy nową grupę
                from python_worker.developer_indexer import DeveloperIndexer
                master_id = DeveloperIndexer(None).generate_usi_id("IM")
                t_data["master_id"] = master_id
                _atomic_write(t_file, t_data)
                
            target_dev_id = t_data.get("usi_dev_id")
            target_ratings = t_data.get("ratings", {})

        # --- Obsługa istniejącego master_id u dołączanego obiektu ---
        old_s_master = s_data.get("master_id")
        if old_s_master and old_s_master != master_id:
            logger.info(f"Source {source_id} was in group {old_s_master}. Removing first.")
            self._remove_member_from_master(old_s_master, source_id)
            s_data = _read_json(s_file) or s_data

        # --- Zbierz wszystkich dotychczasowych memberów nowej grupy ---
        existing_master_data, _ = self._load_master_file(master_id)
        existing_member_ids = [m["usi_inv_id"] for m in (existing_master_data or {}).get("members", [])]

        # Dodaj source_id i ewentualnie target_id
        all_member_ids = list(set(existing_member_ids + [source_id, target_id if not target_id.startswith("IM-") else source_id]))

        # --- Aktualizuj source anchor ---
        s_data["master_id"] = master_id
        _atomic_write(s_file, s_data)

        # --- Zapisz plik master ---
        self._save_master(master_id, all_member_ids)

        # --- Propagacja ocen (jeśli istnieją) ---
        if target_ratings:
            self._propagate_ratings_to_member(s_file, s_data, target_ratings)

        # --- Automatyczne scalenie deweloperów ---
        self._try_merge_developers(
            target_dev_id, s_data.get("usi_dev_id"),
            target_id, source_id
        )

        # Odśwież indeksy — master zastępuje members w indeksie
        self._upsert_index(master_id)
        self._upsert_index(source_id)
        if not target_id.startswith("IM-"):
            self._upsert_index(target_id)
        self._invalidate_service_cache(master_id)
        self._invalidate_service_cache(source_id)

        log_to_processing_log(
            s_meta.get("developer_slug", "unknown"),
            s_meta.get("investment_slug", "unknown"),
            f"Merged into group {master_id}"
        )
        logger.info(f"Merge OK: {source_id} → group {master_id}")
        return True


    # ------------------------------------------------------------------
    # Unmerge
    def unmerge_by_id(self, target_id: str, source_id: str) -> bool:
        """
        Usuwa source_id z grupy wskazanej przez target_id.
        (Jeśli target_id sam w sobie jest grupą, usuwa z niego; jeśli jest INV-XXXX należącym do grupy, usuwa z jego grupy).
        Jeśli po usunięciu zostaje tylko 1 member, rozwiązuje całą grupę.
        """
        s_res = self._get_resources(source_id)
        if not s_res:
            return False

        s_file = s_res["files"].get("anchor")
        s_data = _read_json(s_file)
        if s_data is None:
            return False

        master_id = s_data.get("master_id")
        if not master_id:
            logger.warning(f"{source_id} is not in any group.")
            return False

        removed = self._remove_member_from_master(master_id, source_id)

        if removed:
            s_meta = s_res["metadata"]
            if not target_id.startswith("IM-"):
                self._upsert_index(target_id)
            self._upsert_index(source_id)
            self._invalidate_service_cache(target_id)
            self._invalidate_service_cache(source_id)
            log_to_processing_log(
                s_meta.get("developer_slug", "unknown"),
                s_meta.get("investment_slug", "unknown"),
                f"Unmerged from group {master_id}"
            )
            return True
        return False

    def _remove_member_from_master(self, master_id: str, member_id: str) -> bool:
        """Usuwa member z pliku master i czyści master_id z jego pliku anchor."""
        master_data, master_path = self._load_master_file(master_id)
        if not master_data:
            logger.error(f"Master file not found for {master_id}")
            return False

        before_count = len(master_data["members"])
        master_data["members"] = [m for m in master_data["members"] if m["usi_inv_id"] != member_id]
        after_count = len(master_data["members"])
        was_removed = after_count < before_count

        # Wyczyść master_id z pliku anchor tego membera
        m_res = self._get_resources(member_id)
        if m_res:
            m_file = m_res["files"].get("anchor")
            m_data = _read_json(m_file)
            if m_data:
                m_data["master_id"] = None
                _atomic_write(m_file, m_data)

        # Jeśli zostało <= 1 member, rozwiąż grupę całkowicie
        remaining = master_data["members"]
        if len(remaining) <= 1:
            logger.info(f"Group {master_id} dissolved (only {len(remaining)} member left).")
            for last in remaining:
                last_res = self._get_resources(last["usi_inv_id"])
                if last_res:
                    last_file = last_res["files"].get("anchor")
                    last_data = _read_json(last_file)
                    if last_data:
                        last_data["master_id"] = None
                        _atomic_write(last_file, last_data)
                    self._upsert_index(last["usi_inv_id"])
            if master_path and master_path.exists():
                master_path.unlink()
                logger.info(f"Master file {master_path.name} deleted.")
        else:
            _atomic_write(master_path, master_data)

        return was_removed

    # ------------------------------------------------------------------
    # Propagacja ocen
    # ------------------------------------------------------------------

    def propagate_ratings(self, primary_inv_id: str, ratings: dict, status: Optional[str] = None) -> list[str]:
        """
        Propaguje oceny do wszystkich innych członków grupy.
        Zwraca listę ID inwestycji, do których propagacja się powiodła.
        """
        members = self.get_group_members(primary_inv_id)
        updated = []

        for member in members:
            mid = member.get("usi_inv_id")
            if not mid or mid == primary_inv_id:
                continue

            m_res = self._get_resources(mid)
            if not m_res:
                continue
            m_file = m_res["files"].get("anchor")
            m_data = _read_json(m_file)
            if m_data is None:
                continue

            self._propagate_ratings_to_member(m_file, m_data, ratings, status)
            self._upsert_index(mid)
            self._invalidate_service_cache(mid)
            updated.append(mid)

        return updated

    def _propagate_ratings_to_member(
        self, m_file: Path, m_data: dict, ratings: dict, status: Optional[str] = None
    ) -> None:
        """Zapisuje oceny do jednego rekordu (atomowo)."""
        if not ratings and status is None:
            return

        existing = m_data.get("ratings", {})
        changed = False

        for k, v in ratings.items():
            if k not in ("status", "komentarz") and existing.get(k) != v:
                existing[k] = v
                changed = True

        if status is not None and existing.get("status") != status:
            existing["status"] = status
            changed = True
            m_data["status"] = status

        if changed:
            m_data["ratings"] = existing
            _atomic_write(m_file, m_data)

    # ------------------------------------------------------------------
    # Automatyczne scalanie deweloperów
    # ------------------------------------------------------------------

    def _try_merge_developers(self, primary_dev_id: str, secondary_dev_id: str,
                               primary_inv_id: str, secondary_inv_id: str) -> None:
        """Opcjonalne automatyczne scalenie deweloperów jeśli są różni."""
        if not primary_dev_id or not secondary_dev_id or primary_dev_id == secondary_dev_id:
            return
        try:
            from python_worker.developer_manager import DeveloperManager
            from python_worker.developer_merge_manager import DeveloperMergeManager
            import python_worker.developer_index as dev_index

            dev_dir = self.data_dir.parent / "USIdev"
            dev_manager = DeveloperManager(str(self.data_dir), dev_dir)
            merge_mgr = DeveloperMergeManager(dev_manager, dev_index)
            success = merge_mgr.merge_by_id(target_id=primary_dev_id, source_id=secondary_dev_id)
            if success:
                logger.info(f"[DEV_MERGE] Scalono deweloperów {secondary_dev_id} → {primary_dev_id}")
                dev_manager.invalidate_identifiers_cache()
        except Exception as e:
            logger.warning(f"Auto dev merge failed (non-critical): {e}")


def rebuild_all_masters() -> int:
    """
    Przebudowuje wszystkie istniejące pliki inv_master_*.json nasycając je
    zagregowanymi danymi ze składowych memberów.
    Używane po migracji lub zmianie formatu mastera.
    Zwraca liczbę przebudowanych masterów.
    """
    master_dir = _usi_master_dir()
    if not master_dir.exists():
        logger.warning("USImaster/ directory not found.")
        return 0

    merger = InvestmentMerger()
    count = 0
    errors = 0

    master_files = sorted(master_dir.glob("inv_master_*.json"))
    logger.info(f"Rebuilding {len(master_files)} master files...")

    for mf in master_files:
        try:
            raw = _read_json(mf)
            if not raw:
                continue
            master_id = raw.get("master_id") or raw.get("usi_inv_id")
            if not master_id or not master_id.startswith("IM-"):
                logger.warning(f"Skipping {mf.name}: no valid master_id")
                continue
            members = raw.get("members", [])
            member_ids = [m["usi_inv_id"] for m in members if isinstance(m, dict) and m.get("usi_inv_id")]
            if not member_ids:
                logger.warning(f"Skipping {mf.name}: no members")
                continue
            merger._save_master(master_id, member_ids)
            count += 1
            logger.info(f"  ✓ {master_id} ({len(member_ids)} members)")
        except Exception as e:
            errors += 1
            logger.error(f"  ✗ {mf.name}: {e}")

    logger.info(f"Rebuild complete: {count} OK, {errors} errors.")
    return count
