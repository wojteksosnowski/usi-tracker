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
    
    # Mock index and master enrichment
    with patch("python_worker.developer_index.load", return_value=[]), \
         patch.object(repo, "_enrich_with_master", side_effect=lambda x, ids=None: x):
        
        result = repo.get_developer(usi_dev_id)
        assert result is not None
        assert result["usi_dev_id"] == usi_dev_id
        assert result["developer_slug"] == dev_slug

def test_get_developer_by_slug_via_index(repo):
    """Verify that get_developer resolves slug to ID via index and then loads correctly."""
    usi_dev_id = "DEV-456"
    dev_slug = "new-slug"
    old_slug = "old-slug"
    
    # Record exists on disk with new-slug
    subdir = repo.dev_dir / dev_slug
    subdir.mkdir()
    dev_file = subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
    dev_data = {
        "usi_dev_id": usi_dev_id,
        "developer_slug": dev_slug,
        "name": "Test Developer"
    }
    dev_file.write_text(json.dumps(dev_data))
    
    # Index says "old-slug" -> "DEV-456"
    mock_index = [
        {"developer_slug": old_slug, "usi_dev_id": usi_dev_id, "name": "Test Developer"}
    ]
    
    with patch("python_worker.developer_index.load", return_value=mock_index), \
         patch.object(repo, "_enrich_with_master", side_effect=lambda x, ids=None: x):
        
        # We ask for "old-slug"
        result = repo.get_developer(old_slug)
        
        assert result is not None
        assert result["usi_dev_id"] == usi_dev_id
        # Note: the loaded data has the ACTUAL current slug
        assert result["developer_slug"] == dev_slug

def test_get_developer_by_name_via_index(repo):
    """Verify that get_developer resolves name to ID via index."""
    usi_dev_id = "DEV-789"
    dev_slug = "test-dev-name"
    dev_name = "Major Developer"
    
    subdir = repo.dev_dir / dev_slug
    subdir.mkdir()
    dev_file = subdir / f"usi_dev_{usi_dev_id}_{dev_slug}.json"
    dev_data = {
        "usi_dev_id": usi_dev_id,
        "developer_slug": dev_slug,
        "name": dev_name
    }
    dev_file.write_text(json.dumps(dev_data))
    
    mock_index = [
        {"developer_slug": dev_slug, "usi_dev_id": usi_dev_id, "name": dev_name}
    ]
    
    with patch("python_worker.developer_index.load", return_value=mock_index), \
         patch.object(repo, "_enrich_with_master", side_effect=lambda x, ids=None: x):
        
        # We ask by exact name
        result = repo.get_developer(dev_name)
        assert result is not None
        assert result["usi_dev_id"] == usi_dev_id
        
        # We ask by lowercase name
        result_lower = repo.get_developer(dev_name.lower())
        assert result_lower is not None
        assert result_lower["usi_dev_id"] == usi_dev_id
