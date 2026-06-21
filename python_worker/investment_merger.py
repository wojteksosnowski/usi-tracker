"""
investment_merger.py — Zarządzanie grupami inwestycji (Master Groups)

Architektura grupy:
  - Każdy rekord `usi_*.json` może zawierać klucz `"master_id"` wskazujący na ID grupy.
  - Plik `inv_master_{MASTER_ID}.json` leży w katalogu PRIMARYNEJ inwestycji.
  - "Primaryna" to ta, która ma `role: "primary"` w pliku master.
  - Oceny zapisywane przez użytkownika są propagowane do WSZYSTKICH składowych grupy.
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


class InvestmentMerger:
    """
    Zarządza grupami inwestycji (wiele rekordów z różnych portali = jeden obiekt).

    Plik master JSON (inv_master_{ID}.json) w katalogu primarynej inwestycji:
    {
        "master_id": "MASTER-INV-XXXXX",
        "created_at": "ISO",
        "updated_at": "ISO",
        "primary_id": "INV-XXXXX",          # ID primarynej inwestycji
        "members": [                          # wszyscy członkowie (włącznie z primarynym)
            {
                "usi_inv_id": "INV-XXXXX",
                "role": "primary",
                "dev_slug": "...",
                "inv_slug": "...",
                "added_at": "ISO"
            },
            {
                "usi_inv_id": "INV-YYYYY",
                "role": "secondary",
                "dev_slug": "...",
                "inv_slug": "...",
                "added_at": "ISO"
            }
        ]
    }
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

    def _master_file_path(self, primary_res: dict, master_id: str) -> Path:
        return primary_res["base_dir"] / f"{MASTER_FILE_PREFIX}{master_id}.json"

    def _load_master_file(self, master_id: str, primary_id: str) -> tuple[Optional[dict], Optional[Path]]:
        """Wczytuje plik master. Zwraca (data, path) lub (None, None)."""
        res = self._get_resources(primary_id)
        if not res:
            return None, None
        path = self._master_file_path(res, master_id)
        data = _read_json(path)
        return data, path

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
        Jeśli inwestycja nie jest w grupie, zwraca listę z samym sobą.
        """
        res = self._get_resources(inv_id)
        if not res:
            return []
        data = _read_json(res["files"].get("anchor"))
        if not data:
            return []
        master_id = data.get("master_id")
        if not master_id:
            return [{"usi_inv_id": inv_id, "role": "standalone"}]

        primary_id = data.get("master_primary_id", inv_id)
        master_data, _ = self._load_master_file(master_id, primary_id)
        if not master_data:
            return [{"usi_inv_id": inv_id, "role": "standalone"}]
        return master_data.get("members", [])

    # ------------------------------------------------------------------
    # Merge
    # ------------------------------------------------------------------

    def merge_by_id(self, primary_inv_id: str, secondary_inv_id: str) -> bool:
        """
        Łączy secondary_inv_id w grupę primaryną primary_inv_id.

        Reguły:
        - Jeśli primary ma już master_id, secondary jest dodawany do tej samej grupy.
        - Jeśli secondary ma już master_id w INNEJ grupie, jest wpierw z niej wyłączany.
        - Oceny primarynego są propagowane do wszystkich składowych grupy.
        - Zapis atomowy dla każdego pliku.
        - Tylko `upsert` O(1) — zero `rebuild()`.
        """
        if primary_inv_id == secondary_inv_id:
            logger.error("Cannot merge investment into itself.")
            return False

        p_res = self._get_resources(primary_inv_id)
        s_res = self._get_resources(secondary_inv_id)
        if not p_res or not s_res:
            return False

        p_file = p_res["files"].get("anchor")
        s_file = s_res["files"].get("anchor")
        if not p_file or not s_file:
            logger.error("Anchor files not found.")
            return False

        p_data = _read_json(p_file)
        s_data = _read_json(s_file)
        if p_data is None or s_data is None:
            logger.error("Failed to read anchor files.")
            return False

        p_meta = p_res["metadata"]
        s_meta = s_res["metadata"]

        # --- Obsługa istniejącego master_id secondary ---
        old_s_master = s_data.get("master_id")
        if old_s_master:
            old_primary = s_data.get("master_primary_id", secondary_inv_id)
            if old_s_master != p_data.get("master_id"):
                logger.info(f"Secondary {secondary_inv_id} was in group {old_s_master}. Removing first.")
                self._remove_member_from_master(old_s_master, old_primary, secondary_inv_id)
                # Reload after removal
                s_data = _read_json(s_file) or s_data

        # --- Wyznacz lub utwórz master_id ---
        master_id = p_data.get("master_id") or f"MASTER-{primary_inv_id}"
        master_path = self._master_file_path(p_res, master_id)

        master_data = _read_json(master_path) if master_path.exists() else None
        if not master_data:
            # Nowa grupa — utwórz plik master
            master_data = {
                "master_id": master_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "primary_id": primary_inv_id,
                "members": [
                    {
                        "usi_inv_id": primary_inv_id,
                        "role": "primary",
                        "dev_slug": p_meta.get("developer_slug", ""),
                        "inv_slug": p_meta.get("investment_slug", ""),
                        "added_at": datetime.now().isoformat()
                    }
                ]
            }

        # --- Sprawdź czy secondary już jest w grupie ---
        if any(m["usi_inv_id"] == secondary_inv_id for m in master_data["members"]):
            logger.info(f"{secondary_inv_id} already in group {master_id}.")
            return True

        # --- Dodaj secondary do listy members ---
        master_data["members"].append({
            "usi_inv_id": secondary_inv_id,
            "role": "secondary",
            "dev_slug": s_meta.get("developer_slug", ""),
            "inv_slug": s_meta.get("investment_slug", ""),
            "added_at": datetime.now().isoformat()
        })
        master_data["updated_at"] = datetime.now().isoformat()

        # --- Aktualizuj oba rekordy anchor ---
        p_data["master_id"] = master_id
        p_data["master_primary_id"] = primary_inv_id
        p_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()

        s_data["master_id"] = master_id
        s_data["master_primary_id"] = primary_inv_id
        s_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
        s_data["audit"].setdefault("history", []).append({
            "timestamp": datetime.now().isoformat(),
            "event": "Merged into group",
            "changes": [{"field": "master_id", "old": old_s_master, "new": master_id}]
        })

        # --- Atomowe zapisy ---
        _atomic_write(master_path, master_data)
        _atomic_write(p_file, p_data)
        _atomic_write(s_file, s_data)

        # --- Propagacja ocen primarynego do secondary ---
        primary_ratings = p_data.get("ratings", {})
        if primary_ratings:
            self._propagate_ratings_to_member(s_file, s_data, primary_ratings)

        # --- Automatyczne scalenie deweloperów (konsekwencja łączenia inwestycji) ---
        self._try_merge_developers(p_data.get("usi_dev_id"), s_data.get("usi_dev_id"), primary_inv_id, secondary_inv_id)

        # Kolejność kluczowa: 1) secondary — usuwa się z indeksu, 2) primary — odświeża z pełnymi merged_from
        self._upsert_index(secondary_inv_id)
        self._upsert_index(primary_inv_id)
        self._invalidate_service_cache(secondary_inv_id)
        self._invalidate_service_cache(primary_inv_id)

        log_to_processing_log(
            s_meta.get("developer_slug", "unknown"),
            s_meta.get("investment_slug", "unknown"),
            f"Merged into group {master_id} (primary: {primary_inv_id})"
        )
        logger.info(f"Merge OK: {secondary_inv_id} -> group {master_id} (primary: {primary_inv_id})")
        return True

    # ------------------------------------------------------------------
    # Unmerge
    # ------------------------------------------------------------------

    def unmerge_by_id(self, primary_inv_id: str, secondary_inv_id: str) -> bool:
        """
        Usuwa secondary_inv_id z grupy primarynej.
        Jeśli po usunięciu zostaje tylko 1 member, rozwiązuje całą grupę.
        """
        p_res = self._get_resources(primary_inv_id)
        s_res = self._get_resources(secondary_inv_id)
        if not p_res or not s_res:
            return False

        s_file = s_res["files"].get("anchor")
        s_data = _read_json(s_file)
        if s_data is None:
            return False

        master_id = s_data.get("master_id")
        if not master_id:
            logger.warning(f"{secondary_inv_id} is not in any group.")
            return False

        removed = self._remove_member_from_master(master_id, primary_inv_id, secondary_inv_id)

        if removed:
            s_meta = s_res["metadata"]
            # Kolejność: primary odświeżony (bez byłego membera), secondary wstawiony z powrotem
            self._upsert_index(primary_inv_id)   # zaktualizuj primary w indeksie
            self._upsert_index(secondary_inv_id) # wstaw secondary z powrotem (master_id=null -> nie jest już secondary)
            self._invalidate_service_cache(primary_inv_id)
            self._invalidate_service_cache(secondary_inv_id)
            log_to_processing_log(
                s_meta.get("developer_slug", "unknown"),
                s_meta.get("investment_slug", "unknown"),
                f"Unmerged from group {master_id}"
            )
        return removed

    def _remove_member_from_master(self, master_id: str, primary_id: str, member_id: str) -> bool:
        """Usuwa member z pliku master i czyści master_id z pliku anchor member."""
        p_res = self._get_resources(primary_id)
        if not p_res:
            return False

        master_path = self._master_file_path(p_res, master_id)
        master_data = _read_json(master_path)
        if not master_data:
            logger.error(f"Master file not found: {master_path}")
            return False

        before_count = len(master_data["members"])
        master_data["members"] = [m for m in master_data["members"] if m["usi_inv_id"] != member_id]
        after_count = len(master_data["members"])
        was_removed = after_count < before_count
        master_data["updated_at"] = datetime.now().isoformat()

        # Wyczyść master_id z pliku anchor tego membera
        m_res = self._get_resources(member_id)
        if m_res:
            m_file = m_res["files"].get("anchor")
            m_data = _read_json(m_file)
            if m_data:
                m_data["master_id"] = None
                m_data["master_primary_id"] = None
                m_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
                m_data["audit"].setdefault("history", []).append({
                    "timestamp": datetime.now().isoformat(),
                    "event": "Unmerged from group",
                    "changes": [{"field": "master_id", "old": master_id, "new": None}]
                })
                _atomic_write(m_file, m_data)

        # Jeśli zostało <= 1 member, rozwiąż grupę całkowicie
        remaining = master_data["members"]
        if len(remaining) <= 1:
            logger.info(f"Group {master_id} dissolved (only {len(remaining)} member left).")
            # Wyczyść master_id z ostatniego membera
            for last in remaining:
                last_res = self._get_resources(last["usi_inv_id"])
                if last_res:
                    last_file = last_res["files"].get("anchor")
                    last_data = _read_json(last_file)
                    if last_data:
                        last_data["master_id"] = None
                        last_data["master_primary_id"] = None
                        last_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
                        _atomic_write(last_file, last_data)
                    self._upsert_index(last["usi_inv_id"])
            # Usuń plik master
            if master_path.exists():
                master_path.unlink()
        else:
            _atomic_write(master_path, master_data)

        return was_removed

    # ------------------------------------------------------------------
    # Propagacja ocen
    # ------------------------------------------------------------------

    def propagate_ratings(self, primary_inv_id: str, ratings: dict, status: Optional[str] = None) -> list[str]:
        """
        Propaguje oceny do wszystkich secondary members grupy.
        Zwraca listę ID inwestycji, do których propagacja się powiodła.

        Wywołaj to po każdym zapisie ocen dla rekordu primarynego.
        """
        members = self.get_group_members(primary_inv_id)
        updated = []

        for member in members:
            mid = member.get("usi_inv_id")
            if not mid or mid == primary_inv_id or member.get("role") == "primary":
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
        """Zapisuje oceny primarynego do jednego rekordu secondary (atomowo)."""
        if not ratings and status is None:
            return

        existing = m_data.get("ratings", {})
        changed = False

        for k, v in ratings.items():
            if k not in ("status", "komentarz") and existing.get(k) != v:
                existing[k] = v
                changed = True

        # Status propagujemy tylko jeśli jest ustawiony
        if status is not None and existing.get("status") != status:
            existing["status"] = status
            changed = True
            m_data["status"] = status

        if changed:
            m_data["ratings"] = existing
            m_data.setdefault("audit", {})["updated_at"] = datetime.now().isoformat()
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
                logger.info(f"[DEV_MERGE] Scalono deweloperów {secondary_dev_id} -> {primary_dev_id}")
                dev_manager.invalidate_identifiers_cache()
        except Exception as e:
            logger.warning(f"Auto dev merge failed (non-critical): {e}")
