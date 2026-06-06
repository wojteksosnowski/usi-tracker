import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.developer_repository import DeveloperRepository

@pytest.fixture
def repo(tmp_path):
    data_dir = tmp_path / "USIdata"
    dev_dir = tmp_path / "USIdev"
    data_dir.mkdir()
    dev_dir.mkdir()
    return DeveloperRepository(data_dir, dev_dir)

def test_get_developer_by_id_direct(repo):
    """Verify that get_developer works when passed a DEV- ID directly."""
    usi_dev_id = "DEV-123"
    dev_slug = "test-dev"
    
    # Create the file in new format
    subdir = repo.dev_dir / dev_slug
    subdir.mkdir()
    dev_file = subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
    dev_data = {
        "usi_dev_id": usi_dev_id,
        "developer_slug": dev_slug,
        "name": "Test Developer"
    }
    dev_file.write_text(json.dumps(dev_data))
    
    # Mock index
    with patch("python_worker.developer_index.load", return_value=[]):
        result = repo.get_developer(usi_dev_id)
        assert result is not None
        assert result["usi_dev_id"] == usi_dev_id
        assert result["developer_slug"] == dev_slug

def test_get_developer_rejects_slug(repo):
    """Verify that get_developer rejects slugs as identifiers."""
    dev_slug = "test-dev"
    result = repo.get_developer(dev_slug)
    assert result is None

def test_get_developer_by_id_via_index(repo):
    """Verify that get_developer finds ID in index."""
    usi_dev_id = "DEV-456"
    dev_slug = "new-slug"
    
    mock_index = [
        {"developer_slug": dev_slug, "usi_dev_id": usi_dev_id, "name": "Test Developer"}
    ]
    
    with patch("python_worker.developer_index.load", return_value=mock_index):
        # Even if index has it, we still ask by ID
        result = repo.get_developer(usi_dev_id)
        
        # Note: it will call _enrich_with_master on the index entry
        assert result is not None
        assert result["usi_dev_id"] == usi_dev_id
