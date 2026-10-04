import pytest
import json
from unittest.mock import MagicMock, patch
from pathlib import Path
from python_worker.services.investment_sync import InvestmentSyncService

@pytest.fixture
def mock_identity():
    return MagicMock()

@pytest.fixture
def sync_service(mock_identity, tmp_path):
    mock_config = MagicMock()
    mock_config.public_dir = str(tmp_path / "Public")
    (tmp_path / "USIdata").mkdir(parents=True, exist_ok=True)
    with patch("python_worker.config.get_scraper_config", return_value=mock_config):
        return InvestmentSyncService(
            identity_resolver=mock_identity,
            data_dir=tmp_path / "USIdata",
            public_usi_dir=tmp_path / "Public" / "USI"
        )


def test_update_investment_uses_id_based_upsert(sync_service, mock_identity, tmp_path):
    system_id = "rp_123"
    
    # Mock resources
    anchor_file = tmp_path / "usi_rp_123.json"
    anchor_file.write_text(json.dumps({"usi_inv_id": system_id, "sources": {"rp": {"id": "123"}}}))
    
    mock_identity.get_investment_resources.return_value = {
        "base_dir": tmp_path / "base",
        "files": {"anchor": anchor_file},
        "metadata": {"slug": "dev/inv"}
    }
    
    # Mock internal methods to skip actual work
    sync_service._fetch_and_transform_portal_data = MagicMock(return_value=({"sources": {"rp": {"id": "123"}}}, "rp", None))
    sync_service._sync_investment_images = MagicMock()
    sync_service.repo = MagicMock()
    sync_service.repo.get_investment_json.return_value = {"usi_inv_id": system_id}
    
    # Pre-create index file to avoid FileNotFoundError in upsert
    index_file = tmp_path / "USIdata" / "_index.json"
    index_file.write_text(json.dumps({"entries": [], "count": 0}))
    
    with patch("python_worker.investment_index.upsert") as mock_upsert, \
         patch("python_worker.adapters.merger.Merger.merge", return_value={"usi_inv_id": system_id}):
        
        sync_service.update_investment(system_id)
        
    # Verify upsert was called with inv_id only
    mock_upsert.assert_called_once()
    kwargs = mock_upsert.call_args.kwargs
    assert kwargs["inv_id"] == system_id


def test_process_batch_saves_each_item_as_it_arrives(sync_service):
    order = []
    sync_service._prepare_batch_identifiers = MagicMock(return_value=(["http://a", "http://b"], []))

    def fake_finalize(portal, data, index=0):
        order.append(f"save:{data['n']}")
        return f"{portal}_{data['n']}"

    sync_service._finalize_batch_item = fake_finalize

    def fake_gateway(portal, targets, on_progress=None, on_item=None, on_start=None):
        results = []
        for i, t in enumerate(targets):
            order.append(f"fetch:{i}")
            d = {"n": i}
            on_item(i, t, d)
            results.append(d)
        return results

    sync_service.gateway = MagicMock()
    sync_service.gateway.process_batch = fake_gateway
    events = []
    with patch("python_worker.services.investment_sync.inv_index.rebuild"):
        saved = sync_service.process_batch("rp", [{}, {}], on_progress_callback=events.append)

    assert saved == 2
    assert order == ["fetch:0", "save:0", "fetch:1", "save:1"]  # zapis przed pobraniem kolejnego
    assert [e["status"] for e in events] == ["saved", "saved"]


def test_process_batch_fallback_saves_items_not_delivered_via_on_item(sync_service):
    sync_service._prepare_batch_identifiers = MagicMock(return_value=(["1", "2"], []))
    sync_service._finalize_batch_item = lambda portal, data, index=0: f"{portal}_{data['n']}" if data else None
    sync_service.gateway = MagicMock()
    sync_service.gateway.process_batch = lambda *a, **k: [{"n": 1}, None]
    with patch("python_worker.services.investment_sync.inv_index.rebuild"):
        assert sync_service.process_batch("rp", [{}, {}]) == 1


def test_process_batch_item_failure_does_not_stop_batch(sync_service):
    sync_service._prepare_batch_identifiers = MagicMock(return_value=(["1", "2"], []))

    def finalize(portal, data, index=0):
        if data["n"] == 1:
            raise RuntimeError("boom")
        return f"{portal}_{data['n']}"

    sync_service._finalize_batch_item = finalize
    sync_service.gateway = MagicMock()
    sync_service.gateway.process_batch = lambda *a, **k: [{"n": 1}, {"n": 2}]
    events = []
    with patch("python_worker.services.investment_sync.inv_index.rebuild"):
        assert sync_service.process_batch("rp", [{}, {}], on_progress_callback=events.append) == 1
    assert [e["status"] for e in events] == ["save_failed", "saved"]


def test_index_saved_investment_adds_entry_immediately(sync_service, tmp_path):
    f = tmp_path / "usi_rp_9.json"
    f.write_text(json.dumps({"usi_inv_id": "rp_9"}))
    idx = MagicMock()
    sync_service.dm = MagicMock()
    with patch("python_worker.services.investment_sync.inv_index._build_index_entry", return_value={"usi_inv_id": "rp_9"}), \
         patch("python_worker.services.investment_sync.inv_index.get_investment_index", return_value=idx):
        sync_service._index_saved_investment("rp_9", f)
    idx.add_or_update.assert_called_once_with("rp_9", {"usi_inv_id": "rp_9"})
    sync_service.dm.invalidate_identifiers_cache.assert_called_once()
