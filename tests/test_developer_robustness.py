import pytest
from unittest.mock import Mock, call
from python_worker.developer_merge_manager import DeveloperMergeManager
from python_worker.services.developer_resolver import DeveloperResolver

@pytest.fixture
def mock_repo_and_indexer():
    from pathlib import Path
    repo = Mock()
    indexer = Mock()
    # Domyślne makiety zachowań repozytorium
    repo._get_or_create_dev_master.return_value = {"merged_from": [], "dev_master_id": "DM-100"}
    repo.data_dir = Path("/tmp/mock_data_dir")
    return repo, indexer


class TestDeveloperMergeManagerRobustness:

    def test_should_properly_aggregate_investments_count_and_trigger_indexer(self, mock_repo_and_indexer):
        """
        Krytyczny test dla Problemu 2. Verifikuje, że licznik inwestycji jest poprawnie sumowany
        oraz czy wymuszono pełny rebuild wpisu w indeksie dla OBU deweloperów.
        """
        repo, indexer = mock_repo_and_indexer
        manager = DeveloperMergeManager(repo, indexer)

        target_dev = {
            "usi_dev_id": "DEV-TARGET",
            "developer_slug": "target-slug",
            "investments_count": 5,
            "suggestions": []
        }
        source_dev = {
            "usi_dev_id": "DEV-SOURCE",
            "developer_slug": "source-slug",
            "investments_count": 3,
            "suggestions": []
        }

        repo.get_developer_by_id.side_effect = lambda dev_id: {
            "DEV-TARGET": target_dev,
            "DEV-SOURCE": source_dev
        }.get(dev_id)

        # Wykonanie operacji
        result = manager.merge_by_id("DEV-TARGET", "DEV-SOURCE")

        # Aserty uniemożliwiające false-positive:
        assert result is True, "Metoda powinna zwrócić True przy poprawnym merge"
        
        # 1. Sprawdzenie rygoru agregacji danych
        assert target_dev["investments_count"] == 8, f"Oczekiwano 8 inwestycji, otrzymano: {target_dev['investments_count']}"
        
        # 2. Sprawdzenie zapisu stanu w warstwie persystencji
        repo.create_developer_file.assert_has_calls([
            call(target_dev),
            call(source_dev)
        ], any_order=True)

        # 3. Weryfikacja powiadomienia indeksu (Zapobiega Stale Aggregations z Problemu 2)
        indexer.rebuild_developer_index_entry.assert_has_calls([
            call("DEV-TARGET"),
            call("DEV-SOURCE")
        ], any_order=True)

    def test_should_block_merge_if_either_developer_is_marked_as_virtual(self, mock_repo_and_indexer):
        """
        Krytyczny test dla Problemu 4 (Backend).
        Merge musi zostać natychmiast przerwany, jeśli choć jeden rekord to hub wirtualny.
        """
        repo, indexer = mock_repo_and_indexer
        manager = DeveloperMergeManager(repo, indexer)

        # Przypadek 1: Target jest wirtualny
        target_dev = {"usi_dev_id": "DEV-VIRTUAL", "is_virtual": True, "developer_slug": "platforma-m"}
        source_dev = {"usi_dev_id": "DEV-NORMAL", "is_virtual": False, "developer_slug": "zwykly-dev"}

        result = manager._do_merge(target_dev, source_dev)
        
        assert result is False, "Merge powinien zostać zablokowany, gdy target jest wirtualny"
        repo.create_developer_file.assert_not_called()

        # Przypadek 2: Source jest wirtualny
        target_dev["is_virtual"] = False
        source_dev["is_virtual"] = True

        result = manager._do_merge(target_dev, source_dev)
        
        assert result is False, "Merge powinien zostać zablokowany, gdy source jest wirtualny"
        repo.create_developer_file.assert_not_called()


class TestDeveloperResolverConflictRobustness:

    def test_backfill_should_trigger_system_merge_instead_of_stealing_mapping(self, mock_repo_and_indexer):
        """
        Krytyczny test dla Problemu 3 ("Ciche złodziejstwo ID").
        Jeśli nowo ujednolicona inwestycja powiązana jest z dwoma różnymi technicznie deweloperami,
        system NIE MOŻE przepisać mapowania po cichu do jednego. Musi wywołać oficjalny proces Merge.
        """
        repo, indexer = mock_repo_and_indexer
        
        # Tworzymy Mock dla DeveloperManager który udaje repo/resolver fasadę
        mock_dm = Mock()
        mock_dm.repo = repo
        mock_dm.indexer = indexer

        resolver = DeveloperResolver(developer_manager=mock_dm, identity_resolver=Mock())

        # Inwestycja łączy źródła z dwóch portali (rp oraz oto)
        new_unified_data = {
            "sources": {
                "rp": {"vendor_id": "111"},
                "oto": {"agency_id": "222"}
            }
        }

        # Developer z portalu 'rp'
        dev_target = {"usi_dev_id": "DEV-TARGET", "developer_slug": "target-dev", "portal_mapping": {"rp": {"id": "111"}}}
        # Inny developer, który już istnieje w systemie pod portalem 'oto'
        dev_conflict_child = {"usi_dev_id": "DEV-CONFLICT", "developer_slug": "conflict-dev", "portal_mapping": {"oto": {"agency_id": "222"}}}

        # Symulacja wyszukiwania po ID portalu
        def mock_find_by_id(portal, pid):
            if portal == "rp" and pid == "111":
                return dev_target
            if portal == "oto" and pid == "222":
                return dev_conflict_child
            return None

        mock_dm.find_developer_by_id.side_effect = mock_find_by_id

        # Przygotowujemy przechwytywanie wywołań oryginalnego merge_by_id w repozytorium
        # Musimy upewnić się, że pod spodem wywoła się pełna mechanika łączenia profili
        repo.get_developer_by_id.side_effect = lambda dev_id: {
            "DEV-TARGET": dev_target,
            "DEV-CONFLICT": dev_conflict_child
        }.get(dev_id)

        # Wykonanie kodu resolvera
        resolver.backfill_developer_mapping(system_id="INV-999", new_unified=new_unified_data)

        # ASERCJE ANTY-FAŁSZOWE:
        # 1. Sprawdzamy czy wykryto konflikt i wywołano oficjalny zapis rekordu nadrzędnego (master)
        # Zamiast cichej mutacji, słownik merged_from w repo mastera powinien zarejestrować próbę mergowania.
        assert repo._save_dev_master.called, (
            "Krytyczny błąd: System nie uruchomił mechanizmu Merge Manager w obliczu konfliktu ID. "
            "Doszło do cichego nadpisania lub zignorowania relacji!"
        )

        # 2. Sprawdzenie, czy relacja oznaczona została w pliku źródłowym (podrzędnym) poprzez master_id
        assert dev_conflict_child.get("master_id") is not None, (
            "Profil konfliktowy (źródłowy) nie otrzymał master_id! "
            "Oznacza to, że dane zostały skradzione, a profil nie został poprawnie zmergowany."
        )
