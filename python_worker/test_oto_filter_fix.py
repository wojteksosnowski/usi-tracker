import json
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from python_worker.portal_matcher import filter_new_investments

class TestOtodomFilterFix(unittest.TestCase):
    
    @patch('python_worker.developer_manager.DeveloperManager.get_existing_identifiers')
    @patch('python_worker.config.USI_DATA_DIR', Path('/tmp/usi-test'))
    def test_filter_new_investments_ignores_none_id(self, mock_ids):
        # Setup: Mock existing identifiers in the DB
        # Assume there's one "broken" entry that caused "None" to be in the set before fix
        mock_ids.return_value = {
            "rp_ids": set(),
            "oto_ids": {"12345", "None"}, # Pre-fix state could have "None"
            "oto_slugs": {"existing-slug"},
            "to_ids": set()
        }
        
        # Test items discovered from portal
        discovered = [
            {"id": 12345, "slug": "item-1"},      # Existing ID -> should be is_new: False
            {"id": None, "slug": "existing-slug"}, # Existing Slug -> should be is_new: False
            {"id": None, "slug": "new-slug"},      # New Slug, ID is None -> should be is_new: True (this was failing)
            {"id": 67890, "slug": "new-slug-2"}    # Fully new -> should be is_new: True
        ]
        
        results = filter_new_investments(discovered, "otodom")
        
        self.assertFalse(results[0]["is_new"], "Item with existing ID should not be new")
        self.assertFalse(results[1]["is_new"], "Item with existing slug should not be new")
        self.assertTrue(results[2]["is_new"], "Item with new slug and None ID should be new (FIX VERIFIED)")
        self.assertTrue(results[3]["is_new"], "Fully new item should be new")

if __name__ == "__main__":
    unittest.main()
